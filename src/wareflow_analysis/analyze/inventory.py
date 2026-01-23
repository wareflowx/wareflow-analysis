"""Inventory Analysis module.

Analyzes product catalog statistics including:
- Total product count
- Distribution by category
- Distribution by status
- Data quality issues (missing EAN, descriptions, etc.)
"""

import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd


class InventoryAnalysis:
    """Inventory catalog analysis for products table."""

    def __init__(self, db_path: Path):
        """Initialize inventory analysis with database path.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None

    def connect(self) -> Tuple[bool, str]:
        """Establish database connection.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.db_path.exists():
            return False, f"Database not found: {self.db_path}"

        try:
            self.conn = sqlite3.connect(self.db_path)
            return True, "Connected successfully"
        except Exception as e:
            return False, f"Connection failed: {e}"

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def run(self) -> Dict[str, Any]:
        """Execute inventory analysis.

        Returns:
            Dictionary with inventory analysis results including:
            - total_products: Total number of products
            - by_category: Product count per category
            - by_status: Product count per status
            - issues: Data quality issues (missing EAN, descriptions, etc.)
        """
        if not self.conn:
            raise RuntimeError("Not connected to database. Call connect() first.")

        # Check that required table exists
        missing_tables = self._check_missing_tables(["produits"])

        if missing_tables:
            raise RuntimeError(
                f"Required table(s) not found: {', '.join(missing_tables)}\n\n"
                f"Inventory Analysis requires the 'produits' table to be imported.\n\n"
                f"Make sure your Excel file contains product data and run:\n"
                f"  wareflow import-data --init\n"
                f"  wareflow import-data\n\n"
                f"Missing tables: {', '.join(missing_tables)}"
            )

        try:
            results = {}

            # Get total product count
            results["total_products"] = self._get_total_products()

            # Get distribution by category
            results["by_category"] = self._get_distribution_by_category()

            # Get distribution by status
            results["by_status"] = self._get_distribution_by_status()

            # Get data quality issues
            results["issues"] = self._get_data_quality_issues()

            return results

        except sqlite3.OperationalError as e:
            error_msg = str(e)
            if "no such column" in error_msg:
                column = error_msg.split(":")[-1].strip() if ":" in error_msg else "unknown"
                raise RuntimeError(
                    f"Database column error: '{column}'\n\n"
                    f"Expected columns (normalized names):\n"
                    f"  - no_produit\n"
                    f"  - nom_produit\n"
                    f"  - etat (status)\n"
                    f"  - categorie_produit_1\n"
                    f"  - ean_alternatif\n\n"
                    f"Try reimporting your data:\n"
                    f"  rm warehouse.db\n"
                    f"  wareflow import-data\n\n"
                    f"Technical details: {error_msg}"
                )
            else:
                raise RuntimeError(f"Database query failed: {error_msg}")
        except Exception as e:
            raise RuntimeError(f"Analysis failed: {e}")

    def _check_missing_tables(self, required_tables: List[str]) -> List[str]:
        """Check which required tables are missing from the database.

        Args:
            required_tables: List of table names that should exist

        Returns:
            List of missing table names
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        existing_tables = {row[0] for row in cursor.fetchall()}
        missing_tables = [table for table in required_tables if table not in existing_tables]
        return missing_tables

    def _get_total_products(self) -> int:
        """Get total number of products.

        Returns:
            Total product count
        """
        query = "SELECT COUNT(*) FROM produits"
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor.fetchone()[0]

    def _get_distribution_by_category(self) -> List[Dict[str, Any]]:
        """Get product distribution by category.

        Returns:
            List of dicts with category, count, and percentage
        """
        query = """
        SELECT
            COALESCE(categorie_produit_1, 'Uncategorized') as category,
            COUNT(*) as count
        FROM produits
        GROUP BY categorie_produit_1
        ORDER BY count DESC
        """

        df = pd.read_sql_query(query, self.conn)

        # Calculate percentage
        total = df["count"].sum()
        df["percentage"] = (df["count"] / total * 100).round(1)

        return df.to_dict("records")

    def _get_distribution_by_status(self) -> List[Dict[str, Any]]:
        """Get product distribution by status.

        Returns:
            List of dicts with status, count, and percentage
        """
        query = """
        SELECT
            COALESCE(etat, 'Unknown') as status,
            COUNT(*) as count
        FROM produits
        GROUP BY etat
        ORDER BY count DESC
        """

        df = pd.read_sql_query(query, self.conn)

        # Calculate percentage
        total = df["count"].sum()
        df["percentage"] = (df["count"] / total * 100).round(1)

        return df.to_dict("records")

    def _get_data_quality_issues(self) -> Dict[str, int]:
        """Get data quality issues.

        Returns:
            Dict with issue type and count
        """
        issues = {}

        # Products without EAN
        query = """
        SELECT COUNT(*) FROM produits
        WHERE ean_alternatif IS NULL OR ean_alternatif = '' OR TRIM(ean_alternatif) = ''
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        issues["missing_ean"] = cursor.fetchone()[0]

        # Products with missing/empty description
        query = """
        SELECT COUNT(*) FROM produits
        WHERE description IS NULL OR description = '' OR TRIM(description) = ''
        """
        cursor.execute(query)
        issues["missing_description"] = cursor.fetchone()[0]

        # Products with missing name
        query = """
        SELECT COUNT(*) FROM produits
        WHERE nom_produit IS NULL OR nom_produit = '' OR TRIM(nom_produit) = ''
        """
        cursor.execute(query)
        issues["missing_name"] = cursor.fetchone()[0]

        return issues

    def format_output(self, results: Dict[str, Any]) -> str:
        """Format inventory analysis results for terminal output.

        Args:
            results: Analysis results from run()

        Returns:
            Formatted string for terminal display
        """
        lines = []
        lines.append("=" * 60)
        lines.append("INVENTORY ANALYSIS")
        lines.append("=" * 60)
        lines.append("")

        # Total products
        total = results.get("total_products", 0)
        lines.append(f"Total products: {total:,}")
        lines.append("")

        # By category
        lines.append("By Category:")
        for cat in results.get("by_category", [])[:10]:
            lines.append(
                f"  {cat['category'][:30]:<30} {cat['count']:>6,} ({cat['percentage']:>5.1f}%)"
            )
        lines.append("")

        # By status
        lines.append("By Status:")
        for status in results.get("by_status", []):
            lines.append(
                f"  {status['status'][:30]:<30} {status['count']:>6,} ({status['percentage']:>5.1f}%)"
            )
        lines.append("")

        # Issues
        issues = results.get("issues", {})
        if any(issues.values()):
            lines.append("Data Quality Issues:")
            if issues.get("missing_ean", 0) > 0:
                lines.append(f"  ⚠️  {issues['missing_ean']:,} products without EAN")
            if issues.get("missing_description", 0) > 0:
                lines.append(f"  ⚠️  {issues['missing_description']:,} products with missing description")
            if issues.get("missing_name", 0) > 0:
                lines.append(f"  ⚠️  {issues['missing_name']:,} products with missing name")
            lines.append("")
        else:
            lines.append("✅ No data quality issues found!")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)
