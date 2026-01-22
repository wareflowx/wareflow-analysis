"""Data type validation checks."""

import pandas as pd
import numpy as np

from wareflow_analysis.validation.models import ValidationError
from wareflow_analysis.validation.schema_parser import TableSchema


def check_column_types(
    df: pd.DataFrame, schema: TableSchema, sheet_name: str
) -> list[ValidationError]:
    """Check if column data types match schema expectations.

    Args:
        df: DataFrame to validate
        schema: Table schema with type definitions
        sheet_name: Sheet name for error reporting

    Returns:
        List of validation warnings
    """
    warnings = []

    for col_name, expected_type in schema.column_types.items():
        if col_name not in df.columns:
            continue

        # Get actual data
        col_data = df[col_name]
        non_null_data = col_data.dropna()

        if len(non_null_data) == 0:
            # All null values, will be checked by null_checks
            continue

        # Check based on expected type
        type_mismatches = 0
        sample_mismatches = []

        if expected_type == "INTEGER":
            # Check if values are integers
            for idx, val in non_null_data.head(100).items():
                if not isinstance(val, (int, np.integer)):
                    if isinstance(val, float) and val.is_integer():
                        continue
                    type_mismatches += 1
                    if len(sample_mismatches) < 5:
                        sample_mismatches.append((idx, type(val).__name__))

        elif expected_type == "REAL":
            # Check if values are numeric
            for idx, val in non_null_data.head(100).items():
                if not isinstance(val, (int, float, np.number)):
                    type_mismatches += 1
                    if len(sample_mismatches) < 5:
                        sample_mismatches.append((idx, type(val).__name__))

        elif expected_type == "TEXT":
            # TEXT accepts anything, but warn if it looks like it should be numeric
            pass

        # Report if significant mismatches
        if type_mismatches > 0:
            samples_str = ", ".join([f"row {idx}: {typ}" for idx, typ in sample_mismatches])
            if type_mismatches > len(sample_mismatches):
                samples_str += f", ... and {type_mismatches - len(sample_mismatches)} more"

            warnings.append(
                ValidationError(
                    sheet=sheet_name,
                    row=None,
                    column=col_name,
                    code="TYPE_MISMATCH",
                    message=f"{type_mismatches} values don't match {expected_type} type",
                    suggestion=f"Ensure all '{col_name}' values are {expected_type}. {samples_str}",
                    severity="warning",
                )
            )

    return warnings


def check_numeric_ranges(
    df: pd.DataFrame, schema: TableSchema, sheet_name: str
) -> list[ValidationError]:
    """Check if numeric values are within reasonable ranges.

    Args:
        df: DataFrame to validate
        schema: Table schema
        sheet_name: Sheet name for error reporting

    Returns:
        List of validation warnings
    """
    warnings = []

    for col_name, col_type in schema.column_types.items():
        if col_name not in df.columns:
            continue

        if col_type in ["INTEGER", "REAL", "NUMERIC"]:
            col_data = df[col_name]
            non_null_data = col_data.dropna()

            if len(non_null_data) == 0:
                continue

            # Check for negative values where they shouldn't be
            # For quantity, stock, etc. (heuristic: column name contains 'quantite', 'stock')
            if any(keyword in col_name.lower() for keyword in ["quantite", "stock", "quant", "montant"]):
                negative_count = (non_null_data < 0).sum()

                if negative_count > 0:
                    warnings.append(
                        ValidationError(
                            sheet=sheet_name,
                            row=None,
                            column=col_name,
                            code="NEGATIVE_VALUE",
                            message=f"{negative_count} negative values found",
                            suggestion="Quantity and stock values should be non-negative",
                            severity="warning",
                        )
                    )

    return warnings
