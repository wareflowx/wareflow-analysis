"""Configuration refiner for wareflow-specific business logic.

This module adds wareflow-specific refinements to Auto-Pilot generated configuration.
"""

from pathlib import Path
from typing import Any, Dict
import yaml


WAREFLOW_SPECIFIC_MAPPINGS = {
    # French movement types
    "mouvement_type": {
        "ENTRÉE": "inbound",
        "SORTIE": "outbound",
        "TRANSFERT": "transfer",
        "AJUSTEMENT": "adjustment",
        "INVENTAIRE": "inventory",
        "EN_COURS": "pending",
        # Common variations
        "ENTREE": "inbound",
        "SORTIE": "outbound",
        "ENTRÉE": "inbound",
    },
    # Order status
    "order_status": {
        "EN_COURS": "pending",
        "COMPLÉTÉ": "completed",
        "COMPLÉTÉE": "completed",
        "ANNULÉ": "cancelled",
        "ANNULÉE": "cancelled",
        "EN_ATTENTE": "on_hold",
        "EXPÉDIÉ": "shipped",
        "EXPÉDIE": "shipped",
        "LIVRÉ": "delivered",
    },
    # Product status
    "product_status": {
        "ACTIF": "active",
        "ACTIVE": "active",
        "INACTIF": "inactive",
        "INACTIVE": "inactive",
        "EN_RUPTURE": "out_of_stock",
        "DISCONTINUÉ": "discontinued",
        "DISCONTINUE": "discontinued",
    },
}


WAREFLOW_VALIDATION_RULES = {
    # Movement-specific validations
    "mouvements": [
        {
            "column": "quantite",
            "type": "range",
            "params": {"min": 0, "max": 1000000},
        },
        {
            "column": "no_produit",
            "type": "reference",
            "params": {"table": "produits", "column": "no_produit"},
        },
    ],
    # Product-specific validations
    "produits": [
        {
            "column": "prix",
            "type": "range",
            "params": {"min": 0, "max": 10000000},
        }
    ],
}


WAREFLOW_CALCULATED_COLUMNS = {
    # Combine split date fields if they exist
    "date_heure_combined": {
        "expression": "COALESCE(date_heure_2, date_heure, date)",
        "name": "date_heure_clean",
    },
    # Combined status from multiple status fields
    "status_combined": {
        "expression": "COALESCE(etat_superieur, etat_inferieur, etat, status)",
        "name": "status_unified",
    },
}


def refine_config(
    config: Dict[str, Any],
    project_dir: Path = None,
) -> Dict[str, Any]:
    """Refine Auto-Pilot generated configuration with wareflow-specific logic.

    Args:
        config: Auto-Pilot generated configuration
        project_dir: Optional project directory path

    Returns:
        Refined configuration with wareflow-specific enhancements
    """
    refined_config = config.copy()

    # Refine each mapping
    for table_name, mapping_config in config.get("mappings", {}).items():
        refined_mapping = mapping_config.copy()

        # Add wareflow-specific value mappings
        refined_mapping = add_wareflow_value_mappings(refined_mapping, table_name)

        # Add wareflow-specific validation rules
        refined_mapping = add_wareflow_validations(refined_mapping, table_name)

        # Add wareflow-specific calculated columns
        refined_mapping = add_wareflow_calculated_columns(refined_mapping, table_name)

        # Update the refined config
        refined_config["mappings"][table_name] = refined_mapping

    # Save refined configuration if project dir provided
    if project_dir:
        config_path = project_dir / "excel-to-sql-config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(refined_config, f, default_flow_style=False, sort_keys=False)
        print(f"Refined configuration saved to: {config_path}")

    return refined_config


def add_wareflow_value_mappings(
    mapping_config: Dict[str, Any],
    table_name: str,
) -> Dict[str, Any]:
    """Add wareflow-specific value mappings to configuration.

    Args:
        mapping_config: Current mapping configuration
        table_name: Name of the table

    Returns:
        Updated mapping configuration
    """
    column_mappings = mapping_config.get("column_mappings", {})
    existing_mappings = mapping_config.get("value_mappings", {})

    # Detect columns that might contain French codes
    for col_name, col_config in column_mappings.items():
        col_lower = col_name.lower()

        # Check if this is a status/movement type column
        if any(
            keyword in col_lower
            for keyword in ["type", "status", "etat", "état", "mouvement", "movement"]
        ):
            # Add wareflow-specific mappings
            wareflow_maps = WAREFLOW_SPECIFIC_MAPPINGS.get("mouvement_type", {})

            # Merge with existing mappings
            merged_mappings = {**existing_mappings, **wareflow_maps}
            if merged_mappings:
                mapping_config["value_mappings"] = merged_mappings

    return mapping_config


def add_wareflow_validations(
    mapping_config: Dict[str, Any],
    table_name: str,
) -> Dict[str, Any]:
    """Add wareflow-specific validation rules to configuration.

    Args:
        mapping_config: Current mapping configuration
        table_name: Name of the table

    Returns:
        Updated mapping configuration
    """
    # Get wareflow-specific validations for this table
    table_validations = WAREFLOW_VALIDATION_RULES.get(table_name, [])

    if table_validations:
        existing_validations = mapping_config.get("validation_rules", [])
        mapping_config["validation_rules"] = existing_validations + table_validations

    return mapping_config


def add_wareflow_calculated_columns(
    mapping_config: Dict[str, Any],
    table_name: str,
) -> Dict[str, Any]:
    """Add wareflow-specific calculated columns to configuration.

    Args:
        mapping_config: Current mapping configuration
        table_name: Name of the table

    Returns:
        Updated mapping configuration
    """
    # Get existing calculated columns
    existing_columns = mapping_config.get("calculated_columns", [])

    # Add wareflow-specific calculated columns for movements table
    if table_name == "mouvements":
        for col_def in WAREFLOW_CALCULATED_COLUMNS.values():
            existing_columns.append(
                {"name": col_def["name"], "expression": col_def["expression"]}
            )

        mapping_config["calculated_columns"] = existing_columns

    return mapping_config


def load_existing_config(project_dir: Path) -> Dict[str, Any]:
    """Load existing excel-to-sql configuration.

    Args:
        project_dir: Path to project directory

    Returns:
        Configuration dictionary or empty dict if not found
    """
    config_path = project_dir / "excel-to-sql-config.yaml"

    if not config_path.exists():
        return {}

    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def validate_config(config: Dict[str, Any]) -> tuple[bool, str]:
    """Validate configuration before import.

    Args:
        config: Configuration to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not config:
        return False, "Configuration is empty"

    if "mappings" not in config:
        return False, "Configuration missing 'mappings' section"

    if not config["mappings"]:
        return False, "No mappings defined in configuration"

    # Validate each mapping
    for table_name, mapping_config in config["mappings"].items():
        if "source" not in mapping_config:
            return False, f"Mapping '{table_name}' missing 'source' field"

        if "target_table" not in mapping_config:
            return False, f"Mapping '{table_name}' missing 'target_table' field"

        # Check source file exists
        source_path = Path(mapping_config["source"])
        if not source_path.exists():
            return False, f"Source file not found: {source_path}"

    return True, ""
