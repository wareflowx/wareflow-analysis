"""Database Manager module for clean and reset operations.

This module provides safe database operations with backup, confirmation,
and rollback capabilities.
"""

from pathlib import Path
from typing import List, Tuple, Optional
import sqlite3
import shutil
from datetime import datetime


class DatabaseManager:
    """Manage database operations for wareflow projects."""

    def __init__(self, db_path: Path, project_dir: Path):
        """Initialize database manager.

        Args:
            db_path: Path to SQLite database file
            project_dir: Path to project directory
        """
        self.db_path = db_path
        self.project_dir = project_dir

    def database_exists(self) -> bool:
        """Check if database file exists.

        Returns:
            True if database exists, False otherwise
        """
        return self.db_path.exists()

    def get_table_info(self) -> List[dict]:
        """Get information about all tables in the database.

        Returns:
            List of dictionaries with table names and row counts
        """
        if not self.database_exists():
            return []

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            # Get row counts
            table_info = []
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM '{table}'")
                count = cursor.fetchone()[0]
                table_info.append({"name": table, "rows": count})

            conn.close()
            return table_info

        except Exception as e:
            raise RuntimeError(f"Failed to get table info: {e}")

    def backup_database(self) -> Path:
        """Create a backup of the database file.

        Returns:
            Path to the backup file
        """
        if not self.database_exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.db_path.parent / f"{self.db_path.stem}.backup_{timestamp}{self.db_path.suffix}"

        # Copy database file
        shutil.copy2(self.db_path, backup_path)

        return backup_path

    def clean_table(self, table_name: str) -> int:
        """Delete all data from a specific table.

        Args:
            table_name: Name of the table to clean

        Returns:
            Number of rows deleted

        Raises:
            ValueError: If table doesn't exist
        """
        if not self.database_exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Table '{table_name}' does not exist")

        # Get row count before deleting
        cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
        row_count = cursor.fetchone()[0]

        # Delete all rows
        cursor.execute(f"DELETE FROM '{table_name}'")
        conn.commit()

        # Vacuum to reclaim space
        cursor.execute("VACUUM")
        conn.commit()

        conn.close()

        return row_count

    def clean_all_tables(self) -> dict:
        """Delete all data from all tables (preserves schema).

        Returns:
            Dictionary with table names and rows deleted

        Raises:
            FileNotFoundError: If database doesn't exist
        """
        if not self.database_exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        table_info = self.get_table_info()
        deleted_rows = {}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for table in table_info:
            table_name = table["name"]
            row_count = table["rows"]

            # Delete all rows
            cursor.execute(f"DELETE FROM '{table_name}'")
            deleted_rows[table_name] = row_count

        conn.commit()

        # Vacuum to reclaim space
        cursor.execute("VACUUM")
        conn.commit()

        conn.close()

        return deleted_rows

    def delete_database(self) -> None:
        """Delete the database file.

        Raises:
            FileNotFoundError: If database doesn't exist
        """
        if not self.database_exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        self.db_path.unlink()

    def get_database_size(self) -> int:
        """Get database file size in bytes.

        Returns:
            File size in bytes, or 0 if file doesn't exist
        """
        if self.database_exists():
            return self.db_path.stat().st_size
        return 0

    def get_available_tables(self) -> List[str]:
        """Get list of available table names.

        Returns:
            List of table names
        """
        table_info = self.get_table_info()
        return [t["name"] for t in table_info]

    def confirm_action(self, prompt: str, force: bool = False) -> bool:
        """Ask user for confirmation.

        Args:
            prompt: Confirmation message to display
            force: If True, skip confirmation

        Returns:
            True if user confirms, False otherwise
        """
        if force:
            return True

        try:
            response = input(f"\n{prompt}\nType 'yes' to confirm: ")
            return response.strip().lower() == "yes"
        except (EOFError, KeyboardInterrupt):
            return False

    def format_size(self, size_bytes: int) -> str:
        """Format byte size to human-readable string.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted size string (e.g., "12.4 MB")
        """
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                if unit == "B":
                    return f"{size_bytes} {unit}"
                else:
                    return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
