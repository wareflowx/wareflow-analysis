"""Column-level validation checks."""

import pandas as pd

from wareflow_analysis.validation.models import ValidationError
from wareflow_analysis.validation.schema_parser import TableSchema


def check_required_columns(
    df: pd.DataFrame, schema: TableSchema, sheet_name: str
) -> list[ValidationError]:
    """Check if all required columns are present.

    Args:
        df: DataFrame to validate
        schema: Table schema with required columns
        sheet_name: Sheet name for error reporting

    Returns:
        List of validation errors
    """
    errors = []

    required_columns = schema.get_required_columns()
    missing_columns = set(required_columns) - set(df.columns)

    for col in missing_columns:
        errors.append(
            ValidationError(
                sheet=sheet_name,
                row=None,
                column=col,
                code="COLUMN_MISSING",
                message=f"Required column '{col}' not found",
                suggestion=f"Add column '{col}' to the sheet",
                severity="error",
            )
        )

    return errors


def check_extra_columns(
    df: pd.DataFrame, schema: TableSchema, sheet_name: str
) -> list[ValidationError]:
    """Check for extra columns that will be ignored.

    Args:
        df: DataFrame to validate
        schema: Table schema with expected columns
        sheet_name: Sheet name for reporting

    Returns:
        List of validation warnings
    """
    warnings = []

    expected_columns = set(schema.columns)
    extra_columns = set(df.columns) - expected_columns

    for col in extra_columns:
        warnings.append(
            ValidationError(
                sheet=sheet_name,
                row=None,
                column=col,
                code="EXTRA_COLUMN",
                message=f"Extra column '{col}' will be ignored",
                suggestion="Remove column if not needed or it will be ignored",
                severity="warning",
            )
        )

    return warnings


def check_column_exists(
    df: pd.DataFrame, column_name: str, sheet_name: str
) -> bool:
    """Check if a column exists in DataFrame.

    Args:
        df: DataFrame to check
        column_name: Column name to look for
        sheet_name: Sheet name for error reporting

    Returns:
        True if column exists, False otherwise
    """
    return column_name in df.columns
