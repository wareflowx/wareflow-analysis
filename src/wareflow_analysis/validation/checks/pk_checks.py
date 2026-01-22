"""Primary key validation checks."""

import pandas as pd

from wareflow_analysis.validation.models import ValidationError
from wareflow_analysis.validation.schema_parser import TableSchema


def check_primary_key_uniqueness(
    df: pd.DataFrame, schema: TableSchema, sheet_name: str
) -> list[ValidationError]:
    """Check if primary key column has unique values.

    Args:
        df: DataFrame to validate
        schema: Table schema with PK definition
        sheet_name: Sheet name for error reporting

    Returns:
        List of validation errors
    """
    errors = []

    if not schema.primary_key:
        # No primary key defined, skip check
        return errors

    if schema.primary_key not in df.columns:
        # Missing column error will be caught by column_checks
        return errors

    pk_column = schema.primary_key
    pk_data = df[pk_column]

    # Check for duplicates
    duplicate_mask = pk_data.duplicated(keep=False)
    duplicate_count = duplicate_mask.sum()

    if duplicate_count > 0:
        # Get sample duplicates
        duplicates = df[duplicate_mask]
        dup_values = duplicates[pk_column].unique()[:10]

        samples = []
        for dup_val in dup_values:
            dup_rows = df[df[pk_column] == dup_val].index.tolist()[:3]
            rows_str = ", ".join([str(r + 2) for r in dup_rows])  # +2 for Excel 1-indexing + header
            samples.append(f"PK '{dup_val}' at rows {rows_str}")

        samples_str = "; ".join(samples)
        if len(dup_values) > 10:
            samples_str += f"; ... and {duplicate_count - 10} more"

        errors.append(
            ValidationError(
                sheet=sheet_name,
                row=None,
                column=pk_column,
                code="DUPLICATE_PK",
                message=f"{duplicate_count} duplicate primary key values found",
                suggestion=f"Remove duplicate {pk_column} values. {samples_str}",
                severity="error",
            )
        )

    return errors


def check_primary_key_exists(
    df: pd.DataFrame, schema: TableSchema, sheet_name: str
) -> list[ValidationError]:
    """Check if primary key column has null values.

    Args:
        df: DataFrame to validate
        schema: Table schema with PK definition
        sheet_name: Sheet name for error reporting

    Returns:
        List of validation errors
    """
    errors = []

    if not schema.primary_key:
        return errors

    if schema.primary_key not in df.columns:
        return errors

    pk_column = schema.primary_key
    null_count = df[pk_column].isna().sum()

    if null_count > 0:
        errors.append(
            ValidationError(
                sheet=sheet_name,
                row=None,
                column=pk_column,
                code="PK_NULL_VALUES",
                message=f"{null_count} null values in primary key column",
                suggestion=f"Fill in missing {pk_column} values",
                severity="error",
            )
        )

    return errors
