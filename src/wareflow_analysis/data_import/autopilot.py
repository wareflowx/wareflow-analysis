"""Auto-Pilot configuration generator for wareflow-analysis.

This module uses excel-to-sql's Auto-Pilot Mode to automatically detect patterns
and generate import configuration.
"""

from pathlib import Path
from typing import Any, Dict
import pandas as pd

from wareflow_analysis.data_import.header_detector import HeaderDetector

try:
    from excel_to_sql.auto_pilot import PatternDetector
    from excel_to_sql import ExcelToSqlite
except ImportError:
    raise ImportError(
        "excel-to-sql>=0.3.0 is required. "
        "Install it with: pip install excel-to-sql>=0.3.0"
    )


def find_excel_files(data_dir: Path) -> list[Path]:
    """Find all Excel files in the data directory.

    Args:
        data_dir: Path to data directory

    Returns:
        List of Excel file paths
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    excel_files = []
    for ext in ["*.xlsx", "*.xls"]:
        excel_files.extend(data_dir.glob(ext))

    return sorted(excel_files)


def analyze_excel_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a single Excel file with Auto-Pilot.

    Args:
        file_path: Path to Excel file

    Returns:
        Dictionary with analysis results including patterns
    """
    # Read Excel file with automatic header detection
    try:
        detector = HeaderDetector()
        df = detector.read_excel_with_header_detection(file_path, normalize_columns=False)
    except Exception as e:
        raise ValueError(f"Failed to read {file_path}: {e}")

    if df.empty:
        raise ValueError(f"Excel file is empty: {file_path}")

    # Generate table name from filename
    table_name = file_path.stem.lower().replace(" ", "_").replace("-", "_")

    # Detect patterns using PatternDetector
    detector = PatternDetector()
    patterns = detector.detect_patterns(df, table_name)

    return {
        "file_path": str(file_path),
        "table_name": table_name,
        "rows": len(df),
        "columns": list(df.columns),
        "patterns": patterns,
    }


def generate_autopilot_config(
    data_dir: Path,
    output_path: Path = None,
) -> Dict[str, Any]:
    """Generate configuration using Auto-Pilot Mode.

    This function analyzes all Excel files in the data directory and generates
    an import configuration automatically.

    Args:
        data_dir: Path to directory containing Excel files
        output_path: Optional path to save configuration as YAML

    Returns:
        Dictionary containing the complete Auto-Pilot configuration
    """
    # Find Excel files
    excel_files = find_excel_files(data_dir)

    if not excel_files:
        raise FileNotFoundError(f"No Excel files found in {data_dir}")

    # Analyze each file
    analyses = []
    for file_path in excel_files:
        try:
            analysis = analyze_excel_file(file_path)
            analyses.append(analysis)
        except Exception as e:
            print(f"Warning: Failed to analyze {file_path}: {e}")
            continue

    if not analyses:
        raise ValueError("No valid Excel files could be analyzed")

    # Build configuration
    config = {
        "mappings": {},
        "summary": {
            "total_files": len(analyses),
            "total_rows": sum(a["rows"] for a in analyses),
            "tables": [a["table_name"] for a in analyses],
        },
    }

    # Add each table configuration
    for analysis in analyses:
        table_name = analysis["table_name"]
        patterns = analysis["patterns"]

        # Build mapping configuration
        mapping_config = {
            "source": analysis["file_path"],
            "target_table": table_name,
            "primary_key": patterns.get("primary_key", []),
        }

        # Add column mappings
        column_mappings = {}
        for col in analysis["columns"]:
            column_mappings[str(col)] = {"target": str(col), "type": "text"}

        mapping_config["column_mappings"] = column_mappings

        # Add value mappings if detected
        if patterns.get("value_mappings"):
            mapping_config["value_mappings"] = patterns["value_mappings"]

        # Add calculated columns for split fields if detected
        if patterns.get("split_fields"):
            calculated_columns = []
            for split_field in patterns["split_fields"]:
                calculated_columns.append(
                    {
                        "name": split_field.get("combined_name", "combined"),
                        "expression": split_field.get("expression", ""),
                    }
                )
            mapping_config["calculated_columns"] = calculated_columns

        config["mappings"][table_name] = mapping_config

    # Save configuration if output path provided
    if output_path:
        import yaml

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        print(f"Configuration saved to: {output_path}")

    return config
