"""Data models for validation results."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ValidationError:
    """Represents a validation error or warning."""

    sheet: str
    row: Optional[int]  # None if sheet-level error
    column: Optional[str]  # None if sheet-level error
    code: str  # Error code (e.g., "COLUMN_MISSING", "DUPLICATE_PK")
    message: str  # Human-readable message
    suggestion: str  # Actionable suggestion
    severity: str  # "error" or "warning"

    def __str__(self) -> str:
        location = self._get_location()
        return f"{location}: {self.message}"

    def _get_location(self) -> str:
        """Get formatted location string."""
        parts = [self.sheet]
        if self.row is not None:
            parts.append(f"row {self.row}")
        if self.column:
            parts.append(f"column '{self.column}'")
        return " > ".join(parts)


@dataclass
class FileValidationResult:
    """Validation result for a single file."""

    file_path: Path
    is_valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)
    row_count: int = 0
    duration_ms: int = 0

    @property
    def total_issues(self) -> int:
        """Get total number of issues (errors + warnings)."""
        return len(self.errors) + len(self.warnings)


@dataclass
class ValidationResult:
    """Overall validation result for a project."""

    success: bool
    files_validated: int
    total_rows: int
    total_errors: int
    total_warnings: int
    file_results: list[FileValidationResult] = field(default_factory=list)
    duration_ms: int = 0

    @property
    def has_errors(self) -> bool:
        """Check if any errors were found."""
        return self.total_errors > 0

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings were found."""
        return self.total_warnings > 0

    @property
    def is_perfect(self) -> bool:
        """Check if validation passed with no issues."""
        return self.success and self.total_warnings == 0
