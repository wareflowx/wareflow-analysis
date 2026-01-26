"""Data import module for wareflow-analysis.

This module provides data import functionality using excel-to-sql Auto-Pilot Mode.

Note: Uses lazy imports to avoid triggering excel-to-sql imports at module load time.
This prevents import errors when the module is imported but not actively used.
"""

# Lazy imports - these are only imported when actually used
# This prevents issues with excel-to-sql dependency loading

__all__ = ["generate_autopilot_config", "run_import"]


def __getattr__(name: str):
    """Lazy import attributes only when accessed.

    Args:
        name: Attribute name being accessed

    Returns:
        The requested attribute

    Raises:
        AttributeError: If attribute doesn't exist
    """
    if name == "generate_autopilot_config":
        from wareflow_analysis.data_import.autopilot import generate_autopilot_config
        return generate_autopilot_config
    elif name == "run_import":
        from wareflow_analysis.data_import.importer import run_import
        return run_import
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
