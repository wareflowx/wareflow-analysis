"""Output reporters for validation results."""

from wareflow_analysis.validation.models import (
    FileValidationResult,
    ValidationResult,
    ValidationError,
)


class ValidationReporter:
    """Format and display validation results."""

    def __init__(self, verbose: bool = True):
        """Initialize reporter.

        Args:
            verbose: Enable detailed output
        """
        self.verbose = verbose

    def print_result(self, result: ValidationResult) -> None:
        """Print validation result to console.

        Args:
            result: ValidationResult to display
        """
        if result.is_perfect:
            self._print_success(result)
        elif result.success and result.has_warnings:
            self._print_warnings(result)
        else:
            self._print_errors(result)

    def _print_success(self, result: ValidationResult) -> None:
        """Print success message.

        Args:
            result: ValidationResult
        """
        print("\n" + "=" * 60)
        print("[OK] VALIDATION PASSED")
        print("=" * 60)
        print(f"\nAll files are valid and ready for import.")
        print(f"\nFiles validated: {result.files_validated}")
        print(f"Total rows: {result.total_rows:,}")
        print(f"Errors found: {result.total_errors}")
        print(f"Warnings: {result.total_warnings}")
        print("\n" + "=" * 60)
        print("\nNext step:")
        print("  Run 'wareflow import-data' to import data")
        print("\n" + "=" * 60)

    def _print_warnings(self, result: ValidationResult) -> None:
        """Print warnings message.

        Args:
            result: ValidationResult
        """
        print("\n" + "=" * 60)
        print("[!] VALIDATION PASSED WITH WARNINGS")
        print("=" * 60)
        print(f"\nFiles validated: {result.files_validated}")
        print(f"Total rows: {result.total_rows:,}")
        print(f"Errors: {result.total_errors}")
        print(f"Warnings: {result.total_warnings}")
        print("\n" + "-" * 60)

        # Print per-file summary
        for file_result in result.file_results:
            if file_result.total_issues > 0:
                print(
                    f"\n{file_result.file_path.name}: {len(file_result.errors)} errors, {len(file_result.warnings)} warnings"
                )

        print("\n" + "-" * 60)
        print("\nReview warnings above before importing")
        print("Errors will cause import to fail")
        print("\nNext step:")
        print("  Run 'wareflow import-data' to import (warnings will be ignored)")
        print("\n" + "=" * 60)

    def _print_errors(self, result: ValidationResult) -> None:
        """Print errors message.

        Args:
            result: ValidationResult
        """
        print("\n" + "=" * 60)
        print("[X] VALIDATION FAILED")
        print("=" * 60)
        print(f"\nFiles validated: {result.files_validated}")
        print(f"Errors found: {result.total_errors}")
        print(f"Warnings: {result.total_warnings}")
        print("\n" + "=" * 60)
        print("\nERRORS (must fix before import):")
        print("=" * 60)

        # Group errors by file
        for file_result in result.file_results:
            if file_result.errors:
                print(f"\n{file_result.file_path.name}:\n")

                for error in file_result.errors[:10]:  # Limit to first 10
                    print(f"  [{error.code}] {error.sheet}")
                    if error.column:
                        print(f"      Column: {error.column}")
                    if error.row is not None:
                        print(f"      {error.message}")
                    else:
                        print(f"      {error.message}")
                    print(f"      Suggestion: {error.suggestion}")

                if len(file_result.errors) > 10:
                    print(f"\n  ... and {len(file_result.errors) - 10} more errors")

        print("\n" + "=" * 60)
        print("\nSolutions:")
        print("  1. Fix column names in Excel files")
        print("  2. Remove duplicate primary keys")
        print("  3. Correct data types in Excel")
        print("  4. Ensure all sheets have data")
        print("  5. Re-run validation after fixes")
        print("\nCannot proceed with import until errors are fixed")
        print("\n" + "=" * 60)

    def print_file_details(self, file_result: FileValidationResult) -> None:
        """Print detailed validation result for a single file.

        Args:
            file_result: FileValidationResult to display
        """
        print(f"\n{'=' * 60}")
        print(f"File: {file_result.file_path.name}")
        print(f"{'=' * 60}")
        print(f"\nValid: {'[OK]' if file_result.is_valid else '[X] FAILED'}")
        print(f"Rows: {file_result.row_count:,}")
        print(f"Duration: {file_result.duration_ms}ms")

        if file_result.errors:
            print(f"\nErrors ({len(file_result.errors)}):")
            for error in file_result.errors:
                print(f"  - {error}")

        if file_result.warnings:
            print(f"\nWarnings ({len(file_result.warnings)}):")
            for warning in file_result.warnings[:20]:  # Limit to 20
                print(f"  - {warning}")

        print("\n" + "=" * 60)
