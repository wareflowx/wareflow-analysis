"""Importer module for wareflow-analysis.

This module provides direct import functionality using pandas and sqlite3.
"""

from pathlib import Path
from typing import Any, Dict, Tuple
import time
import sqlite3
import pandas as pd


from wareflow_analysis.data_import.config_refiner import (
    load_existing_config,
    validate_config,
)


def run_import(
    project_dir: Path,
    verbose: bool = True,
) -> Tuple[bool, str]:
    """Execute import using pandas and sqlite3.

    Args:
        project_dir: Path to wareflow project directory
        verbose: Enable verbose output

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Load configuration
    config = load_existing_config(project_dir)

    if not config:
        return False, "No configuration found. Run 'wareflow import-data --init' first."

    # Validate configuration
    is_valid, error_msg = validate_config(config)
    if not is_valid:
        return False, f"Configuration error: {error_msg}"

    db_path = project_dir / "warehouse.db"

    try:
        if verbose:
            print("\n" + "=" * 60)
            print("WAREFLOW DATA IMPORT")
            print("=" * 60)
            print(f"\nDatabase: {db_path}")
            print(f"Processing {len(config['mappings'])} import(s)...\n")

        # Connect to database
        conn = sqlite3.connect(db_path)

        # Import each mapping
        results = []
        total_rows = 0
        start_time = time.time()

        for table_name, mapping_config in config["mappings"].items():
            if verbose:
                print(f"  -> {table_name}...", end=" ", flush=True)

            try:
                # Read Excel file
                df = pd.read_excel(mapping_config["source"])

                # Apply value mappings if configured
                if "value_mappings" in mapping_config:
                    for col, mappings in mapping_config["value_mappings"].items():
                        if col in df.columns:
                            df[col] = df[col].map(mappings).fillna(df[col])

                # Import to database
                rows_imported = df.to_sql(
                    table_name, conn, if_exists="replace", index=False
                )

                total_rows += rows_imported
                results.append((table_name, True, rows_imported))

                if verbose:
                    print(f"[OK] {rows_imported:,} rows")

            except Exception as e:
                error_msg = str(e)
                results.append((table_name, False, error_msg))

                if verbose:
                    print(f"[ERROR] Error: {error_msg}")

        # Commit and close
        conn.commit()
        conn.close()

        # Generate summary
        duration = time.time() - start_time
        success_count = sum(1 for _, success, _ in results if success)
        total_count = len(results)

        if verbose:
            print("\n" + "=" * 60)
            print("IMPORT SUMMARY")
            print("=" * 60)
            print(f"\nTotal rows imported: {total_rows:,}")
            print(f"Successful imports: {success_count}/{total_count}")
            print(f"Duration: {duration:.2f} seconds")

            # Show errors if any
            failed = [r for r in results if not r[1]]
            if failed:
                print("\n[!]  Failed imports:")
                for table_name, _, error in failed:
                    print(f"  - {table_name}: {error}")

            print("\n" + "=" * 60)

        # Return success if all imports succeeded
        if success_count == total_count:
            success_msg = f"Successfully imported {total_rows:,} rows from {total_count} table(s)"
            return True, success_msg
        else:
            error_msg = f"Partial success: {success_count}/{total_count} imports succeeded"
            return False, error_msg

    except Exception as e:
        error_msg = f"Import failed: {e}"
        return False, error_msg


def init_import_config(
    data_dir: Path,
    project_dir: Path,
    verbose: bool = True,
) -> Tuple[bool, str]:
    """Initialize import configuration using Auto-Pilot.

    This function analyzes Excel files and generates configuration automatically.

    Args:
        data_dir: Path to directory containing Excel files
        project_dir: Path to wareflow project directory
        verbose: Enable verbose output

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        if verbose:
            print("\n" + "=" * 60)
            print("AUTO-PILOT CONFIGURATION GENERATION")
            print("=" * 60)
            print(f"\nAnalyzing Excel files in: {data_dir}\n")

        # Import here to avoid issues if excel-to-sql is not installed
        from wareflow_analysis.data_import.autopilot import generate_autopilot_config
        from wareflow_analysis.data_import.config_refiner import refine_config

        # Generate Auto-Pilot configuration
        config = generate_autopilot_config(data_dir)

        if verbose:
            print(f"[OK] Analyzed {config['summary']['total_files']} file(s)")
            print(f"[OK] Total rows: {config['summary']['total_rows']:,}")
            print(f"[OK] Tables: {', '.join(config['summary']['tables'])}\n")

        # Refine with wareflow-specific logic
        refined_config = refine_config(config, project_dir)

        if verbose:
            print("[OK] Configuration generated: excel-to-sql-config.yaml")
            print("\nNext steps:")
            print("  1. Review the configuration file")
            print("  2. Run 'wareflow import-data' to import data")
            print("\n" + "=" * 60)

        return True, "Configuration generated successfully"

    except FileNotFoundError as e:
        return False, f"No Excel files found: {e}"
    except Exception as e:
        return False, f"Configuration generation failed: {e}"


def get_import_status(project_dir: Path) -> Dict[str, Any]:
    """Get current import status.

    Args:
        project_dir: Path to wareflow project directory

    Returns:
        Dictionary with import status information
    """
    db_path = project_dir / "warehouse.db"

    if not db_path.exists():
        return {
            "database_exists": False,
            "tables": {},
        }

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get list of tables
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        # Get row counts
        table_counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM '{table}'")
            table_counts[table] = cursor.fetchone()[0]

        conn.close()

        return {
            "database_exists": True,
            "database_path": str(db_path),
            "tables": table_counts,
        }

    except Exception as e:
        return {
            "database_exists": True,
            "error": str(e),
            "tables": {},
        }
