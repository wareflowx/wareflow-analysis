"""Main validator orchestrator."""

from pathlib import Path
import time
import pandas as pd

from wareflow_analysis.validation.models import (
    FileValidationResult,
    ValidationResult,
    ValidationError,
)
from wareflow_analysis.validation.schema_parser import SchemaParser
from wareflow_analysis.validation.checks import file_checks
from wareflow_analysis.validation.checks import sheet_checks
from wareflow_analysis.validation.checks import column_checks
from wareflow_analysis.validation.checks import type_checks
from wareflow_analysis.validation.checks import pk_checks
from wareflow_analysis.validation.checks import null_checks


class Validator:
    """Main validator orchestrator for Excel files."""

    def __init__(self, project_dir: Path):
        """Initialize validator.

        Args:
            project_dir: Path to wareflow project directory
        """
        self.project_dir = project_dir
        self.schema_path = project_dir / "schema.sql"
        self.data_dir = project_dir / "data"

        # Parse schema
        self.parser = SchemaParser()
        self.schemas = self.parser.parse(self.schema_path)

    def validate_project(self, strict: bool = False) -> ValidationResult:
        """Validate all Excel files in the project.

        Args:
            strict: If True, treat warnings as errors

        Returns:
            ValidationResult with overall results
        """
        start_time = time.time()

        # Find all Excel files
        excel_files = self._find_excel_files()

        if not excel_files:
            return ValidationResult(
                success=False,
                files_validated=0,
                total_rows=0,
                total_errors=1,
                total_warnings=0,
                file_results=[
                    FileValidationResult(
                        file_path=Path(""),
                        is_valid=False,
                        errors=[
                            ValidationError(
                                sheet="",
                                row=None,
                                column=None,
                                code="NO_FILES",
                                message="No Excel files found in data/ directory",
                                suggestion="Add Excel files to data/ directory",
                                severity="error",
                            )
                        ],
                    )
                ],
                duration_ms=int((time.time() - start_time) * 1000),
            )

        # Validate each file
        file_results = []
        total_errors = 0
        total_warnings = 0
        total_rows = 0

        for file_path in excel_files:
            result = self.validate_file(file_path)
            file_results.append(result)

            total_errors += len(result.errors)
            total_warnings += len(result.warnings)
            total_rows += result.row_count

        # Determine overall success
        if strict:
            success = total_errors == 0 and total_warnings == 0
        else:
            success = total_errors == 0

        return ValidationResult(
            success=success,
            files_validated=len(file_results),
            total_rows=total_rows,
            total_errors=total_errors,
            total_warnings=total_warnings,
            file_results=file_results,
            duration_ms=int((time.time() - start_time) * 1000),
        )

    def validate_file(self, file_path: Path) -> FileValidationResult:
        """Validate a single Excel file.

        Args:
            file_path: Path to Excel file

        Returns:
            FileValidationResult with all issues found
        """
        start_time = time.time()
        errors = []
        warnings = []

        # Phase 1: File-level checks
        errors.extend(file_checks.check_file_exists(file_path))
        errors.extend(file_checks.check_file_format(file_path))

        if any(e.code == "FILE_NOT_FOUND" for e in errors):
            return FileValidationResult(
                file_path=file_path,
                is_valid=False,
                errors=errors,
                warnings=warnings,
                duration_ms=int((time.time() - start_time) * 1000),
            )

        # Phase 2: File readable check
        errors.extend(file_checks.check_file_readable(file_path))

        # Check file size (warning only)
        warnings.extend(file_checks.check_file_size(file_path))

        # Phase 3: Read Excel file
        try:
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
        except Exception as e:
            errors.append(
                ValidationError(
                    sheet="",
                    row=None,
                    column=None,
                    code="CANNOT_READ",
                    message=f"Cannot read Excel file: {e}",
                    suggestion="Check file format and integrity",
                    severity="error",
                )
            )
            return FileValidationResult(
                file_path=file_path,
                is_valid=False,
                errors=errors,
                warnings=warnings,
                duration_ms=int((time.time() - start_time) * 1000),
            )

        # Phase 4: Validate each sheet
        total_rows = 0

        for sheet_name in sheet_names:
            # Map sheet name to table schema
            table_name = sheet_name.lower()
            schema = self.schemas.get(table_name)

            if schema is None:
                # Unknown sheet, warn and skip
                warnings.append(
                    ValidationError(
                        sheet=sheet_name,
                        row=None,
                        column=None,
                        code="UNKNOWN_SHEET",
                        message=f"Sheet '{sheet_name}' doesn't match any table",
                        suggestion="Sheet will be ignored during import",
                        severity="warning",
                    )
                )

                # Still count rows
                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    total_rows += len(df)
                except Exception:
                    pass

                continue

            # Read the sheet
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                total_rows += len(df)
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
                continue

            # Run all checks for this sheet
            errors.extend(sheet_checks.check_sheets_not_empty(file_path, [sheet_name]))
            errors.extend(column_checks.check_required_columns(df, schema, sheet_name))
            warnings.extend(column_checks.check_extra_columns(df, schema, sheet_name))
            warnings.extend(type_checks.check_column_types(df, schema, sheet_name))
            warnings.extend(type_checks.check_numeric_ranges(df, schema, sheet_name))
            errors.extend(pk_checks.check_primary_key_uniqueness(df, schema, sheet_name))
            errors.extend(pk_checks.check_primary_key_exists(df, schema, sheet_name))
            warnings.extend(null_checks.check_null_values(df, schema, sheet_name))

        # Determine if file is valid
        is_valid = len(errors) == 0

        return FileValidationResult(
            file_path=file_path,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            row_count=total_rows,
            duration_ms=int((time.time() - start_time) * 1000),
        )

    def _find_excel_files(self) -> list[Path]:
        """Find all Excel files in data directory.

        Returns:
            List of Excel file paths
        """
        if not self.data_dir.exists():
            return []

        excel_files = []
        for ext in ["*.xlsx", "*.xls"]:
            excel_files.extend(self.data_dir.glob(ext))

        return sorted(excel_files)
