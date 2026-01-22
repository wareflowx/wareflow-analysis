"""File-level validation checks."""

from pathlib import Path
import pandas as pd

from wareflow_analysis.validation.models import ValidationError


def check_file_exists(file_path: Path) -> list[ValidationError]:
    """Check if Excel file exists.

    Args:
        file_path: Path to Excel file

    Returns:
        List of validation errors (empty if file exists)
    """
    errors = []

    if not file_path.exists():
        errors.append(
            ValidationError(
                sheet="",
                row=None,
                column=None,
                code="FILE_NOT_FOUND",
                message=f"File not found: {file_path}",
                suggestion="Check that the file path is correct",
                severity="error",
            )
        )

    return errors


def check_file_readable(file_path: Path) -> list[ValidationError]:
    """Check if Excel file is readable.

    Args:
        file_path: Path to Excel file

    Returns:
        List of validation errors (empty if readable)
    """
    errors = []

    try:
        # Try to read the file
        excel_file = pd.ExcelFile(file_path)
        # Check if it has sheets
        if len(excel_file.sheet_names) == 0:
            errors.append(
                ValidationError(
                    sheet="",
                    row=None,
                    column=None,
                    code="EMPTY_FILE",
                    message="Excel file has no sheets",
                    suggestion="Add at least one sheet with data",
                    severity="error",
                )
            )
    except Exception as e:
        errors.append(
            ValidationError(
                sheet="",
                row=None,
                column=None,
                code="FILE_CORRUPT",
                message=f"Cannot read file: {e}",
                suggestion="Check file integrity and format",
                severity="error",
            )
        )

    return errors


def check_file_format(file_path: Path) -> list[ValidationError]:
    """Check if file is a valid Excel file.

    Args:
        file_path: Path to check

    Returns:
        List of validation errors (empty if valid Excel)
    """
    errors = []

    # Check file extension
    valid_extensions = [".xlsx", ".xls"]
    if file_path.suffix.lower() not in valid_extensions:
        errors.append(
            ValidationError(
                sheet="",
                row=None,
                column=None,
                code="NOT_EXCEL_FILE",
                message=f"Invalid file format: {file_path.suffix}",
                suggestion="Use .xlsx or .xls file format",
                severity="error",
            )
        )

    return errors


def check_file_size(file_path: Path) -> list[ValidationError]:
    """Check if file size is reasonable.

    Args:
        file_path: Path to check

    Returns:
        List of validation warnings (empty if size OK)
    """
    warnings = []

    try:
        size_mb = file_path.stat().st_size / (1024 * 1024)

        # Warn if file is very large (> 100 MB)
        if size_mb > 100:
            warnings.append(
                ValidationError(
                    sheet="",
                    row=None,
                    column=None,
                    code="LARGE_FILE",
                    message=f"Large file: {size_mb:.1f} MB",
                    suggestion="Validation may take longer",
                    severity="warning",
                )
            )
    except Exception:
        # File not accessible, will be caught by other checks
        pass

    return warnings
