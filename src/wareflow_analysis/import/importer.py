"""Importer module for wareflow-analysis.

This module wraps excel-to-sql SDK to perform data import with progress reporting.
"""

from pathlib import Path
from typing import Any, Dict, Tuple
import time

try:
    from excel_to_sql import ExcelToSqlite
except ImportError:
    raise ImportError(
        "excel-to-sql>=0.3.0 is required. "
        "Install it with: pip install excel-to-sql>=0.3.0"
    )


from wareflow_analysis.import.config_refiner import (
    load_existing_config,
    validate_config,
)


def run_import(
    project_dir: Path,
    verbose: bool = True,
) -> Tuple[bool, str]:
    """Execute import using excel-to-sql SDK.

    Args:
        project_dir: Path to wareflow project directory
        verbose: Enable verbose output

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Load configuration
    config = load_existing_config(project_dir)

    if not config:
        return False, "No configuration found. Run 'wareflow import --init' first."

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

        # Initialize SDK
        sdk = ExcelToSqlite(db_path=str(db_path))

        # Import each mapping
        results = []
        total_rows = 0
        start_time = time.time()

        for table_name, mapping_config in config["mappings"].items():
            if verbose:
                print(f"  → {table_name}...", end=" ", flush=True)

            try:
                result = sdk.import_excel(
                    file_path=mapping_config["source"],
                    type_name=table_name,
                    tags=["wareflow-import"],
                )

                rows_imported = result.get("rows_imported", 0)
                total_rows += rows_imported
                results.append((table_name, True, rows_imported))

                if verbose:
                    print(f"✅ {rows_imported:,} rows")

            except Exception as e:
                error_msg = str(e)
                results.append((table_name, False, error_msg))

                if verbose:
                    print(f"❌ Error: {error_msg}")

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
                print("\n⚠️  Failed imports:")
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
        from wareflow_analysis.import.autopilot import generate_autopilot_config
        from wareflow_analysis.import.config_refiner import refine_config

        # Generate Auto-Pilot configuration
        config = generate_autopilot_config(data_dir)

        if verbose:
            print(f"✅ Analyzed {config['summary']['total_files']} file(s)")
            print(f"✅ Total rows: {config['summary']['total_rows']:,}")
            print(f"✅ Tables: {', '.join(config['summary']['tables'])}\n")

        # Refine with wareflow-specific logic
        refined_config = refine_config(config, project_dir)

        if verbose:
            print("✅ Configuration generated: excel-to-sql-config.yaml")
            print("\nNext steps:")
            print("  1. Review the configuration file")
            print("  2. Run 'wareflow import' to import data")
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
        sdk = ExcelToSqlite(db_path=str(db_path))

        # Get list of tables
        tables_query = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        tables_df = sdk.query(tables_query)

        tables = {}
        for table_name in tables_df["name"]:
            count_query = f"SELECT COUNT(*) as count FROM '{table_name}'"
            count_df = sdk.query(count_query)
            tables[table_name] = count_df.iloc[0]["count"]

        return {
            "database_exists": True,
            "database_path": str(db_path),
            "tables": tables,
        }

    except Exception as e:
        return {
            "database_exists": True,
            "error": str(e),
            "tables": {},
        }
