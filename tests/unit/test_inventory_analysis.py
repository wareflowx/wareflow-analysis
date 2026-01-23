"""Unit tests for Inventory Analysis module."""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime

from wareflow_analysis.analyze.inventory import InventoryAnalysis


@pytest.fixture
def sample_database(tmp_path):
    """Create a temporary SQLite database with sample inventory data.

    Args:
        tmp_path: Pytest fixture for temporary directory

    Returns:
        Path to test database
    """
    db_path = tmp_path / "test_inventory.db"

    # Create connection and setup schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create produits table with normalized column names
    cursor.execute("""
        CREATE TABLE produits (
            no_produit TEXT PRIMARY KEY,
            nom_produit TEXT,
            description TEXT,
            classe_produit TEXT,
            categorie_produit_1 TEXT,
            categorie_produit_2 TEXT,
            categorie_produit_3 TEXT,
            etat TEXT,
            configuration TEXT,
            ean_alternatif TEXT
        )
    """)

    # Insert sample data with various categories and statuses
    test_data = [
        # Products in category "Pilote" with status "Actif"
        ("PROD001", "Product 1", "Description 1", "FG", "Pilote", "CASQUES", "DIVERS", "Actif", "Config1", "EAN001"),
        ("PROD002", "Product 2", "Description 2", "FG", "Pilote", "CASQUES", "DIVERS", "Actif", "Config2", "EAN002"),
        ("PROD003", "Product 3", "Description 3", "FG", "Pilote", "CASQUES", "DIVERS", "Actif", "Config3", "EAN003"),
        ("PROD004", "Product 4", "Description 4", "FG", "Pilote", "CASQUES", "DIVERS", "Actif", "Config4", "EAN004"),
        ("PROD005", "Product 5", "Description 5", "FG", "Pilote", "CASQUES", "DIVERS", "Actif", "Config5", "EAN005"),
        # Products in category "Accessoires" with status "Actif"
        ("PROD006", "Product 6", "Description 6", "FG", "Accessoires", "GUANTS", "DIVERS", "Actif", "Config6", "EAN006"),
        ("PROD007", "Product 7", "Description 7", "FG", "Accessoires", "GUANTS", "DIVERS", "Actif", "Config7", "EAN007"),
        # Products with status "Inactif"
        ("PROD008", "Product 8", "Description 8", "FG", "Pilote", "CASQUES", "DIVERS", "Inactif", "Config8", "EAN008"),
        ("PROD009", "Product 9", "Description 9", "FG", "Accessoires", "GUANTS", "DIVERS", "Inactif", "Config9", "EAN009"),
        # Products with status "En rupture"
        ("PROD010", "Product 10", "Description 10", "FG", "Pilote", "CASQUES", "DIVERS", "En rupture", "Config10", "EAN010"),
        # Products with missing EAN
        ("PROD011", "Product 11", "Description 11", "FG", "Pilote", "CASQUES", "DIVERS", "Actif", "Config11", None),
        ("PROD012", "Product 12", "Description 12", "FG", "Pilote", "CASQUES", "DIVERS", "Actif", "Config12", ""),
        # Product with missing description
        ("PROD013", "Product 13", None, "FG", "Accessoires", "GUANTS", "DIVERS", "Actif", "Config13", "EAN013"),
        # Product with missing name
        ("PROD014", None, "Description 14", "FG", "Accessoires", "GUANTS", "DIVERS", "Actif", "Config14", "EAN014"),
        # Product with no category (NULL)
        ("PROD015", "Product 15", "Description 15", "FG", None, "GUANTS", "DIVERS", "Actif", "Config15", "EAN015"),
    ]

    cursor.executemany(
        """INSERT INTO produits VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        test_data
    )

    conn.commit()
    conn.close()

    return db_path


@pytest.fixture
def empty_database(tmp_path):
    """Create a temporary SQLite database with no data.

    Args:
        tmp_path: Pytest fixture for temporary directory

    Returns:
        Path to empty test database
    """
    db_path = tmp_path / "test_empty.db"
    conn = sqlite3.connect(db_path)
    conn.close()
    return db_path


class TestInventoryAnalysis:
    """Test suite for InventoryAnalysis class."""

    def test_connect_success(self, sample_database):
        """Test successful database connection."""
        analyzer = InventoryAnalysis(sample_database)
        success, message = analyzer.connect()

        assert success is True
        assert "Connected successfully" in message
        assert analyzer.conn is not None

        analyzer.close()

    def test_connect_file_not_found(self, tmp_path):
        """Test connection with non-existent database."""
        non_existent = tmp_path / "does_not_exist.db"
        analyzer = InventoryAnalysis(non_existent)
        success, message = analyzer.connect()

        assert success is False
        assert "Database not found" in message

    def test_run_success(self, sample_database):
        """Test successful inventory analysis execution."""
        analyzer = InventoryAnalysis(sample_database)
        analyzer.connect()

        results = analyzer.run()

        # Verify total count
        assert results["total_products"] == 15

        # Verify category distribution
        categories = results["by_category"]
        assert len(categories) == 3  # Pilote, Accessoires, Uncategorized

        # Find Pilote category
        pilote = next((c for c in categories if c["category"] == "Pilote"), None)
        assert pilote is not None
        assert pilote["count"] == 9  # PROD001-005, PROD008, PROD010-012

        # Find Accessoires category
        accessoires = next((c for c in categories if c["category"] == "Accessoires"), None)
        assert accessoires is not None
        assert accessoires["count"] == 5  # PROD006-007, PROD009, PROD013-014

        # Verify status distribution
        statuses = results["by_status"]
        assert len(statuses) == 3  # Actif, Inactif, En rupture

        # Find Actif status
        actif = next((s for s in statuses if s["status"] == "Actif"), None)
        assert actif is not None
        assert actif["count"] == 12  # PROD001-007, PROD011-015

        # Find Inactif status
        inactif = next((s for s in statuses if s["status"] == "Inactif"), None)
        assert inactif is not None
        assert inactif["count"] == 2  # PROD008-009

        # Find En rupture status
        en_rupture = next((s for s in statuses if s["status"] == "En rupture"), None)
        assert en_rupture is not None
        assert en_rupture["count"] == 1

        # Verify data quality issues
        issues = results["issues"]
        assert issues["missing_ean"] == 2  # PROD011, PROD012
        assert issues["missing_description"] == 1  # PROD013
        assert issues["missing_name"] == 1  # PROD014

        analyzer.close()

    def test_run_missing_table(self, empty_database):
        """Test analysis with missing produits table."""
        analyzer = InventoryAnalysis(empty_database)
        analyzer.connect()

        with pytest.raises(RuntimeError) as exc_info:
            analyzer.run()

        assert "Required table(s) not found" in str(exc_info.value)
        assert "produits" in str(exc_info.value)
        assert "wareflow import-data" in str(exc_info.value)

        analyzer.close()

    def test_run_not_connected(self, sample_database):
        """Test running analysis without connecting first."""
        analyzer = InventoryAnalysis(sample_database)

        with pytest.raises(RuntimeError) as exc_info:
            analyzer.run()

        assert "Not connected to database" in str(exc_info.value)

    def test_format_output(self, sample_database):
        """Test formatted output generation."""
        analyzer = InventoryAnalysis(sample_database)
        analyzer.connect()

        results = analyzer.run()
        output = analyzer.format_output(results)

        # Verify output contains key sections
        assert "INVENTORY ANALYSIS" in output
        assert "Total products:" in output
        assert "15" in output
        assert "By Category:" in output
        assert "By Status:" in output
        assert "Data Quality Issues:" in output
        assert "=" * 60 in output

        analyzer.close()

    def test_format_output_no_issues(self, sample_database):
        """Test formatted output when no data quality issues exist."""
        # Create a clean database with no issues
        db_path = sample_database.parent / "test_clean.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE produits (
                no_produit TEXT PRIMARY KEY,
                nom_produit TEXT,
                description TEXT,
                classe_produit TEXT,
                categorie_produit_1 TEXT,
                categorie_produit_2 TEXT,
                categorie_produit_3 TEXT,
                etat TEXT,
                configuration TEXT,
                ean_alternatif TEXT
            )
        """)

        # Insert clean data (no missing values)
        cursor.execute(
            """INSERT INTO produits VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            ("PROD001", "Product 1", "Description 1", "FG", "Pilote", "CASQUES", "DIVERS", "Actif", "Config1", "EAN001")
        )

        conn.commit()
        conn.close()

        analyzer = InventoryAnalysis(db_path)
        analyzer.connect()

        results = analyzer.run()
        output = analyzer.format_output(results)

        # Should show "No data quality issues found!"
        assert "No data quality issues found!" in output

        analyzer.close()

    def test_distribution_percentages(self, sample_database):
        """Test that percentages sum to 100 for each distribution."""
        analyzer = InventoryAnalysis(sample_database)
        analyzer.connect()

        results = analyzer.run()

        # Check category percentages
        category_total = sum(c["percentage"] for c in results["by_category"])
        assert category_total == pytest.approx(100.0, abs=0.1)

        # Check status percentages
        status_total = sum(s["percentage"] for s in results["by_status"])
        assert status_total == pytest.approx(100.0, abs=0.1)

        analyzer.close()

    def test_close_connection(self, sample_database):
        """Test that close properly closes database connection."""
        analyzer = InventoryAnalysis(sample_database)
        analyzer.connect()

        assert analyzer.conn is not None

        analyzer.close()

        assert analyzer.conn is None
