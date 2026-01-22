"""Null value validation checks."""

import pandas as pd

from wareflow_analysis.validation.models import ValidationError
from wareflow_analysis.validation.schema_parser import TableSchema


def check_null_values(
    df: pd.DataFrame, schema: TableSchema, sheet_name: str
) -> list[ValidationError]:
    """Check for null values in important columns.

    Args:
        df: DataFrame to validate
        schema: Table schema
        sheet_name: Sheet name for error reporting

    Returns:
        List of validation warnings
    """
    warnings = []

    # Check critical columns that shouldn't have null values
    # Currently all columns are considered important if they have data
    for col_name in schema.columns:
        if col_name not in df.columns:
            continue

        null_count = df[col_name].isna().sum()

        if null_count > 0:
            # Get sample rows with null values
            null_rows = df[df[col_name].isna()].index.tolist()[:10]
            rows_str = ", ".join([str(r + 2) for r in null_rows])  # +2 for Excel 1-indexing + header

            if null_count > 10:
                rows_str += f", ... and {null_count - 10} more"

            warnings.append(
                ValidationError(
                    sheet=sheet_name,
                    row=None,
                    column=col_name,
                    code="NULL_VALUES",
                    message=f"{null_count} null values found",
                    suggestion=f"Fill in missing '{col_name}' values at rows {rows_str}",
                    severity="warning",
                )
            )

    return warnings
