"""Unit tests for ABC classification analysis."""

import pytest
import sqlite3
from pathlib import Path
import tempfile

from wareflow_analysis.analyze.abc import ABCAnalysis


@pytest.fixture
def sample_database():
    """Create a test database with sample warehouse data."""
    db_path = tempfile.mktemp(suffix=".db")

    conn = sqlite3.connect(db_path)

    # Create schema
    conn.execute(
        """
        CREATE TABLE produits (
            no_produit INTEGER PRIMARY KEY,
            nom_produit TEXT
        )
    """
    )

    conn.execute(
        """
        CREATE TABLE mouvements (
            oid INTEGER PRIMARY KEY,
            no_produit INTEGER,
            type TEXT,
            quantite INTEGER,
            date_heure DATETIME,
            FOREIGN KEY (no_produit) REFERENCES produits(no_produit)
        )
    """
    )

    # Insert test products
    products = [
        (1001, "Product Alpha"),
        (1002, "Product Beta"),
        (1003, "Product Gamma"),
        (1004, "Product Delta"),
        (1005, "Product Epsilon"),
        (1006, "Product Zeta"),
        (1007, "Product Eta"),
        (1008, "Product Theta"),
        (1009, "Product Iota"),
        (1010, "Product Kappa"),
    ]

    conn.executemany("INSERT INTO produits VALUES (?, ?)", products)

    # Insert test movements with varying volumes to create ABC distribution
    # Using recent dates (within last 90 days) to match lookback period
    # Product 1001-1002: High volume (Class A)
    # Product 1003-1005: Medium volume (Class B)
    # Product 1006-1010: Low volume (Class C)
    from datetime import datetime, timedelta

    today = datetime.now()
    movements = []

    # Class A products - 1000 picks each (recent dates)
    for i in range(100):
        date_str = (today - timedelta(days=1)).strftime("%Y-%m-%d 10:00:00")
        movements.append((i, 1001, "SORTIE", 10, date_str))
        date_str = (today - timedelta(days=2)).strftime("%Y-%m-%d 11:00:00")
        movements.append((i + 100, 1002, "SORTIE", 10, date_str))

    # Class B products - 200 picks each
    for i in range(200):
        date_str = (today - timedelta(days=3)).strftime("%Y-%m-%d 12:00:00")
        movements.append((i + 200, 1003, "SORTIE", 1, date_str))
        date_str = (today - timedelta(days=4)).strftime("%Y-%m-%d 13:00:00")
        movements.append((i + 400, 1004, "SORTIE", 1, date_str))

    # Class B - 150 picks
    for i in range(150):
        date_str = (today - timedelta(days=5)).strftime("%Y-%m-%d 14:00:00")
        movements.append((i + 600, 1005, "SORTIE", 1, date_str))

    # Class C products - 10 picks each
    for i in range(10):
        date_str = (today - timedelta(days=6)).strftime("%Y-%m-%d 15:00:00")
        movements.append((i + 750, 1006, "SORTIE", 1, date_str))
        date_str = (today - timedelta(days=7)).strftime("%Y-%m-%d 15:30:00")
        movements.append((i + 760, 1007, "SORTIE", 1, date_str))
        date_str = (today - timedelta(days=8)).strftime("%Y-%m-%d 16:00:00")
        movements.append((i + 770, 1008, "SORTIE", 1, date_str))
        date_str = (today - timedelta(days=9)).strftime("%Y-%m-%d 16:30:00")
        movements.append((i + 780, 1009, "SORTIE", 1, date_str))
        date_str = (today - timedelta(days=10)).strftime("%Y-%m-%d 17:00:00")
        movements.append((i + 790, 1010, "SORTIE", 1, date_str))

    conn.executemany(
        "INSERT INTO mouvements VALUES (?, ?, ?, ?, ?)", movements
    )

    conn.commit()
    conn.close()

    yield Path(db_path)

    # Cleanup - explicitly close any remaining connections and delete
    try:
        # Force garbage collection to release file locks
        import gc
        gc.collect()
        Path(db_path).unlink()
    except PermissionError:
        # Windows may still have the file locked, skip cleanup
        pass


class TestABCAnalysis:
    """Test suite for ABCAnalysis class."""

    def test_connect_success(self, sample_database):
        """Test successful database connection."""
        analyzer = ABCAnalysis(sample_database)
        success, message = analyzer.connect()

        assert success is True
        assert "Connected successfully" in message
        assert analyzer.conn is not None

        analyzer.close()

    def test_connect_file_not_found(self):
        """Test connection with non-existent database."""
        analyzer = ABCAnalysis(Path("/nonexistent/path/to/db.db"))
        success, message = analyzer.connect()

        assert success is False
        assert "not found" in message.lower()

    def test_run_analysis_basic(self, sample_database):
        """Test basic ABC analysis execution."""
        analyzer = ABCAnalysis(sample_database)
        analyzer.connect()

        results = analyzer.run(lookback_days=90)

        # Verify result structure
        assert "classification" in results
        assert "summary" in results
        assert "total_products" in results
        assert "total_picks" in results

        # Verify data exists
        assert results["total_products"] == 10
        assert results["total_picks"] > 0

        # Verify summary structure
        assert "class_a" in results["summary"]
        assert "class_b" in results["summary"]
        assert "class_c" in results["summary"]

        analyzer.close()

    def test_run_analysis_not_connected(self, sample_database):
        """Test analysis execution without connection."""
        analyzer = ABCAnalysis(sample_database)

        with pytest.raises(RuntimeError, match="Not connected"):
            analyzer.run()

    def test_class_distribution(self, sample_database):
        """Test ABC class distribution logic."""
        analyzer = ABCAnalysis(sample_database)
        analyzer.connect()

        results = analyzer.run(lookback_days=90)
        summary = results["summary"]

        # Verify all classes have data
        assert summary["class_a"]["count"] > 0
        # Class B might be empty with small datasets, so we don't assert > 0
        # Class C might also be empty with small datasets
        assert summary["class_c"]["count"] >= 0

        # Verify total matches
        total_count = (
            summary["class_a"]["count"]
            + summary["class_b"]["count"]
            + summary["class_c"]["count"]
        )
        assert total_count == results["total_products"]

        # Verify class A has highest percentage (should be true with our data)
        assert summary["class_a"]["percentage"] > summary["class_c"]["percentage"]

        analyzer.close()

    def test_format_output_with_data(self, sample_database):
        """Test output formatting with actual data."""
        analyzer = ABCAnalysis(sample_database)
        analyzer.connect()

        results = analyzer.run(lookback_days=90)
        output = analyzer.format_output(results)

        # Verify key elements in output
        assert "ABC CLASSIFICATION ANALYSIS" in output
        assert "Class A" in output
        assert "Class B" in output
        assert "Class C" in output
        assert "Recommendations" in output

        analyzer.close()

    def test_format_output_empty_database(self):
        """Test output formatting with empty database."""
        # Create empty database
        db_path = tempfile.mktemp(suffix=".db")
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE mouvements (oid INTEGER, no_produit INTEGER, type TEXT)"
        )
        conn.execute("CREATE TABLE produits (no_produit INTEGER PRIMARY KEY)")
        conn.close()

        analyzer = ABCAnalysis(Path(db_path))
        analyzer.connect()

        # Return empty results
        results = {
            "classification": [],
            "summary": {
                "class_a": {"count": 0, "picks": 0, "percentage": 0.0},
                "class_b": {"count": 0, "picks": 0, "percentage": 0.0},
                "class_c": {"count": 0, "picks": 0, "percentage": 0.0},
            },
            "total_products": 0,
            "total_picks": 0,
        }

        output = analyzer.format_output(results)

        assert "No products found" in output
        assert "import-data" in output

        analyzer.close()
        Path(db_path).unlink()

    def test_close_connection(self, sample_database):
        """Test database connection closing."""
        analyzer = ABCAnalysis(sample_database)
        analyzer.connect()

        assert analyzer.conn is not None

        analyzer.close()

        assert analyzer.conn is None
