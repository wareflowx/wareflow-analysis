"""Unit tests for Database Manager module."""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime

from wareflow_analysis.database.manager import DatabaseManager


class TestDatabaseManager:
    """Test suite for DatabaseManager class."""

    @pytest.fixture
    def sample_database(self, tmp_path):
        """Create a temporary SQLite database with sample data.

        Args:
            tmp_path: Pytest fixture for temporary directory

        Returns:
            Path to test database
        """
        db_path = tmp_path / "test.db"

        # Create database with sample tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create produits table
        cursor.execute("""
            CREATE TABLE produits (
                no_produit TEXT PRIMARY KEY,
                nom_produit TEXT,
                categorie TEXT
            )
        """)

        # Create mouvements table
        cursor.execute("""
            CREATE TABLE mouvements (
                id INTEGER PRIMARY KEY,
                no_produit TEXT,
                quantite INTEGER
            )
        """)

        # Insert sample data
        cursor.executemany(
            "INSERT INTO produits VALUES (?, ?, ?)",
            [
                ("PROD001", "Product 1", "A"),
                ("PROD002", "Product 2", "B"),
                ("PROD003", "Product 3", "A"),
            ]
        )

        cursor.executemany(
            "INSERT INTO mouvements VALUES (?, ?, ?)",
            [
                (1, "PROD001", 100),
                (2, "PROD002", 200),
                (3, "PROD003", 150),
                (4, "PROD001", 50),
            ]
        )

        conn.commit()
        conn.close()

        return db_path

    @pytest.fixture
    def empty_project_dir(self, tmp_path):
        """Create empty project directory.

        Args:
            tmp_path: Pytest fixture for temporary directory

        Returns:
            Path to empty project directory
        """
        return tmp_path

    def test_initialization(self, sample_database):
        """Test DatabaseManager initialization."""
        manager = DatabaseManager(sample_database, sample_database.parent)
        assert manager.db_path == sample_database
        assert manager.project_dir == sample_database.parent

    def test_database_exists_true(self, sample_database):
        """Test database_exists returns True when database exists."""
        manager = DatabaseManager(sample_database, sample_database.parent)
        assert manager.database_exists() is True

    def test_database_exists_false(self, empty_project_dir):
        """Test database_exists returns False when database doesn't exist."""
        db_path = empty_project_dir / "nonexistent.db"
        manager = DatabaseManager(db_path, empty_project_dir)
        assert manager.database_exists() is False

    def test_get_table_info(self, sample_database):
        """Test getting table information."""
        manager = DatabaseManager(sample_database, sample_database.parent)

        table_info = manager.get_table_info()

        assert len(table_info) == 2

        # Check produits table
        produits = next((t for t in table_info if t["name"] == "produits"), None)
        assert produits is not None
        assert produits["rows"] == 3

        # Check mouvements table
        mouvements = next((t for t in table_info if t["name"] == "mouvements"), None)
        assert mouvements is not None
        assert mouvements["rows"] == 4

    def test_backup_database(self, sample_database):
        """Test database backup creation."""
        manager = DatabaseManager(sample_database, sample_database.parent)

        backup_path = manager.backup_database()

        # Verify backup was created
        assert backup_path.exists()
        assert backup_path.name.startswith("test.backup_")
        assert backup_path.suffix == ".db"

        # Verify backup has same content
        original_conn = sqlite3.connect(sample_database)
        backup_conn = sqlite3.connect(backup_path)

        original_cursor = original_conn.cursor()
        backup_cursor = backup_conn.cursor()

        original_cursor.execute("SELECT COUNT(*) FROM produits")
        backup_cursor.execute("SELECT COUNT(*) FROM produits")

        assert original_cursor.fetchone()[0] == backup_cursor.fetchone()[0]

        original_cursor.close()
        backup_cursor.close()
        original_conn.close()
        backup_conn.close()

    def test_clean_table(self, sample_database):
        """Test cleaning a specific table."""
        manager = DatabaseManager(sample_database, sample_database.parent)

        # Clean mouvements table
        deleted = manager.clean_table("mouvements")

        assert deleted == 4

        # Verify table is empty but exists
        conn = sqlite3.connect(sample_database)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM mouvements")
        assert cursor.fetchone()[0] == 0

        # Verify produits table is untouched
        cursor.execute("SELECT COUNT(*) FROM produits")
        assert cursor.fetchone()[0] == 3

        conn.close()

    def test_clean_table_not_found(self, sample_database):
        """Test cleaning non-existent table raises error."""
        manager = DatabaseManager(sample_database, sample_database.parent)

        with pytest.raises(ValueError, match="does not exist"):
            manager.clean_table("unknown_table")

    def test_clean_all_tables(self, sample_database):
        """Test cleaning all tables."""
        manager = DatabaseManager(sample_database, sample_database.parent)

        # Clean all tables
        deleted_rows = manager.clean_all_tables()

        # Verify all tables were cleaned
        assert "produits" in deleted_rows
        assert "mouvements" in deleted_rows
        assert deleted_rows["produits"] == 3
        assert deleted_rows["mouvements"] == 4

        # Verify tables are empty but exist
        conn = sqlite3.connect(sample_database)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM produits")
        assert cursor.fetchone()[0] == 0

        cursor.execute("SELECT COUNT(*) FROM mouvements")
        assert cursor.fetchone()[0] == 0

        conn.close()

    def test_clean_all_tables_no_database(self, empty_project_dir):
        """Test cleaning when database doesn't exist."""
        db_path = empty_project_dir / "nonexistent.db"
        manager = DatabaseManager(db_path, empty_project_dir)

        with pytest.raises(FileNotFoundError):
            manager.clean_all_tables()

    def test_delete_database(self, sample_database):
        """Test deleting database file."""
        manager = DatabaseManager(sample_database, sample_database.parent)

        assert manager.database_exists() is True

        manager.delete_database()

        assert manager.database_exists() is False
        assert not sample_database.exists()

    def test_get_database_size(self, sample_database):
        """Test getting database file size."""
        manager = DatabaseManager(sample_database, sample_database.parent)

        size = manager.get_database_size()

        assert size > 0
        assert isinstance(size, int)

    def test_get_database_size_no_database(self, empty_project_dir):
        """Test getting size when database doesn't exist."""
        db_path = empty_project_dir / "nonexistent.db"
        manager = DatabaseManager(db_path, empty_project_dir)

        size = manager.get_database_size()

        assert size == 0

    def test_get_available_tables(self, sample_database):
        """Test getting list of available tables."""
        manager = DatabaseManager(sample_database, sample_database.parent)

        tables = manager.get_available_tables()

        assert len(tables) == 2
        assert "produits" in tables
        assert "mouvements" in tables

    def test_format_size(self):
        """Test size formatting."""
        manager = DatabaseManager(Path("test.db"), Path("."))

        # Test various sizes
        assert "B" in manager.format_size(512)
        assert "KB" in manager.format_size(1024)
        assert "MB" in manager.format_size(1024 * 1024)
        assert "GB" in manager.format_size(1024 * 1024 * 1024)

    def test_confirm_action_with_force(self, tmp_path):
        """Test confirmation bypass with force=True."""
        manager = DatabaseManager(tmp_path / "test.db", tmp_path)

        # With force=True, should return True without prompting
        assert manager.confirm_action("Test prompt", force=True) is True

    def test_backup_creates_new_file(self, sample_database):
        """Test that backup creates a separate file."""
        import time
        manager = DatabaseManager(sample_database, sample_database.parent)

        backup1 = manager.backup_database()
        time.sleep(1)  # Delay to ensure different timestamp (at least 1 second)
        backup2 = manager.backup_database()

        # Should create two different backup files
        assert backup1 != backup2
        assert backup1.exists()
        assert backup2.exists()

        # Original database should still exist
        assert sample_database.exists()
