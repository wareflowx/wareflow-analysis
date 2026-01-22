"""Sheet-level validation checks."""

from pathlib import Path
import pandas as pd

from wareflow_analysis.validation.models import ValidationError


def check_sheets_exist(
    file_path: Path, required_sheets: list[str]
) -> list[ValidationError]:
    """Check if required sheets exist in Excel file.

    Args:
        file_path: Path to Excel file
        required_sheets: List of required sheet names

    Returns:
        List of validation errors
    """
    errors = []

    try:
        excel_file = pd.ExcelFile(file_path)
        available_sheets = excel_file.sheet_names

        for sheet_name in required_sheets:
            if sheet_name not in available_sheets:
                errors.append(
                    ValidationError(
                        sheet=sheet_name,
                        row=None,
                        column=None,
                        code="SHEET_MISSING",
                        message=f"Required sheet '{sheet_name}' not found",
                        suggestion=f"Available sheets: {', '.join(available_sheets)}",
                        severity="error",
                    )
                )
    except Exception as e:
        errors.append(
            ValidationError(
                sheet="",
                row=None,
                column=None,
                code="SHEET_READ_ERROR",
                message=f"Cannot read sheets: {e}",
                suggestion="Check file format",
                severity="error",
            )
        )

    return errors


def check_sheets_not_empty(
    file_path: Path, sheets_to_check: list[str]
) -> list[ValidationError]:
    """Check if sheets contain data.

    Args:
        file_path: Path to Excel file
        sheets_to_check: List of sheet names to check

    Returns:
        List of validation errors
    """
    errors = []

    for sheet_name in sheets_to_check:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            if df.empty:
                errors.append(
                    ValidationError(
                        sheet=sheet_name,
                        row=None,
                        column=None,
                        code="SHEET_EMPTY",
                        message=f"Sheet '{sheet_name}' has no data",
                        suggestion="Add data rows to the sheet",
                        severity="error",
                    )
                )
        except Exception as e:
            errors.append(
                ValidationError(
                    sheet=sheet_name,
                    row=None,
                    column=None,
                    code="SHEET_READ_ERROR",
                    message=f"Cannot read sheet '{sheet_name}': {e}",
                    suggestion="Check sheet format",
                    severity="error",
                )
            )

    return errors


def check_extra_sheets(
    file_path: Path, expected_sheets: list[str]
) -> list[ValidationError]:
    """Check for extra sheets that will be ignored.

    Args:
        file_path: Path to Excel file
        expected_sheets: List of expected sheet names

    Returns:
        List of validation warnings
    """
    warnings = []

    try:
        excel_file = pd.ExcelFile(file_path)
        available_sheets = excel_file.sheet_names

        # Find sheets that aren't in expected list
        extra_sheets = [s for s in available_sheets if s not in expected_sheets]

        for sheet_name in extra_sheets:
            warnings.append(
                ValidationError(
                    sheet=sheet_name,
                    row=None,
                    column=None,
                    code="EXTRA_SHEET",
                    message=f"Extra sheet '{sheet_name}' will be ignored",
                    suggestion="Remove sheet if not needed",
                    severity="warning",
                )
            )
    except Exception:
        # Error will be caught by other checks
        pass

    return warnings


def get_sheet_row_count(file_path: Path, sheet_name: str) -> int:
    """Get row count for a sheet.

    Args:
        file_path: Path to Excel file
        sheet_name: Sheet name

    Returns:
        Number of rows (0 if sheet cannot be read)
    """
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        return len(df)
    except Exception:
        return 0
