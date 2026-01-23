"""ABC Classification analysis module.

Implements Pareto analysis for warehouse inventory:
- Class A: Top 20% of products = 80% of movements
- Class B: Next 30% of products = 15% of movements
- Class C: Bottom 50% of products = 5% of movements
"""

import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd


class ABCAnalysis:
    """ABC Classification analysis using Pareto principle (80/20 rule)."""

    def __init__(self, db_path: Path):
        """Initialize ABC analysis with database path.

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

    def run(self, lookback_days: int = 90) -> Dict[str, Any]:
        """Execute ABC classification analysis.

        Args:
            lookback_days: Analysis period in days (default: 90)

        Returns:
            Dictionary with classification results including:
            - classification: List of products with ABC class
            - summary: Statistics per class (count, picks, percentage)
            - total_products: Total number of products analyzed
            - total_picks: Total movements across all products
        """
        if not self.conn:
            raise RuntimeError("Not connected to database. Call connect() first.")

        query = f"""
        WITH product_movement AS (
            SELECT
                m.no_produit,
                p.nom_produit,
                COUNT(*) as total_movements,
                SUM(CASE WHEN m.type = 'SORTIE' THEN 1 ELSE 0 END) as outbound_count,
                SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite ELSE 0 END) as total_picked,
                MAX(m.date_heure) as last_movement
            FROM mouvements m
            JOIN produits p ON m.no_produit = p.no_produit
            WHERE m.date_heure >= date('now', '-{lookback_days} days')
            GROUP BY m.no_produit
        ),
        with_percentile AS (
            SELECT *,
                NTILE(100) OVER (ORDER BY total_picked DESC) as percentile_rank
            FROM product_movement
        )
        SELECT
            no_produit,
            nom_produit,
            total_movements,
            total_picked,
            percentile_rank,
            CASE
                WHEN percentile_rank <= 20 THEN 'A'
                WHEN percentile_rank <= 50 THEN 'B'
                ELSE 'C'
            END as abc_class,
            last_movement
        FROM with_percentile
        ORDER BY total_picked DESC
        """

        try:
            df = pd.read_sql_query(query, self.conn)

            if df.empty:
                return {
                    "classification": [],
                    "summary": {
                        "class_a": {"count": 0, "picks": 0, "percentage": 0.0},
                        "class_b": {"count": 0, "picks": 0, "percentage": 0.0},
                        "class_c": {"count": 0, "picks": 0, "percentage": 0.0},
                    },
                    "total_products": 0,
                    "total_picks": 0,
                }

            # Calculate summary statistics
            total_picks = int(df["total_picked"].sum())

            summary = {
                "class_a": self._calculate_class_stats(df, "A", total_picks),
                "class_b": self._calculate_class_stats(df, "B", total_picks),
                "class_c": self._calculate_class_stats(df, "C", total_picks),
            }

            return {
                "classification": df.to_dict("records"),
                "summary": summary,
                "total_products": len(df),
                "total_picks": total_picks,
            }

        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}")

    def _calculate_class_stats(
        self, df: pd.DataFrame, abc_class: str, total_picks: int
    ) -> Dict[str, Any]:
        """Calculate statistics for a specific ABC class.

        Args:
            df: DataFrame with classification results
            abc_class: Class to calculate stats for ('A', 'B', or 'C')
            total_picks: Total picks across all classes

        Returns:
            Dictionary with count, picks, and percentage
        """
        class_df = df[df["abc_class"] == abc_class]
        picks = int(class_df["total_picked"].sum())
        percentage = (picks / total_picks * 100) if total_picks > 0 else 0.0

        return {
            "count": len(class_df),
            "picks": picks,
            "percentage": round(percentage, 1),
        }

    def format_output(self, results: Dict[str, Any]) -> str:
        """Format analysis results for terminal display.

        Args:
            results: Results dictionary from run()

        Returns:
            Formatted string for terminal output
        """
        if results["total_products"] == 0:
            return (
                "\n" + "=" * 60 + "\n"
                "📊 ABC CLASSIFICATION ANALYSIS\n"
                + "=" * 60 + "\n\n"
                "No products found in the specified period.\n"
                "Ensure you have imported data with 'wareflow import-data'.\n"
                + "=" * 60 + "\n"
            )

        summary = results["summary"]
        total = results["total_picks"]
        total_products = results["total_products"]

        output = []
        output.append("\n" + "=" * 60)
        output.append("📊 ABC CLASSIFICATION ANALYSIS")
        output.append("=" * 60)
        output.append(f"\nPeriod: Last 90 days")
        output.append(f"Total Products: {total_products:,}")
        output.append(f"Total Picks: {total:,}")

        # Class A
        a = summary["class_a"]
        output.append(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        output.append(f"Class A (Top 20% = High Priority)")
        output.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        output.append(f"  Products: {a['count']:,} ({a['count']/total_products*100:.1f}%)")
        output.append(f"  Picks: {a['picks']:,} ({a['percentage']}%)")
        output.append(f"  Avg picks/product: {a['picks']//a['count'] if a['count'] > 0 else 0:,}")
        self._append_top_products(output, results["classification"], "A", 3)

        # Class B
        b = summary["class_b"]
        output.append(f"\nClass B (Next 30% = Medium Priority)")
        output.append(f"  Products: {b['count']:,} ({b['count']/total_products*100:.1f}%)")
        output.append(f"  Picks: {b['picks']:,} ({b['percentage']}%)")
        output.append(f"  Avg picks/product: {b['picks']//b['count'] if b['count'] > 0 else 0:,}")

        # Class C
        c = summary["class_c"]
        output.append(f"\nClass C (Bottom 50% = Low Priority)")
        output.append(f"  Products: {c['count']:,} ({c['count']/total_products*100:.1f}%)")
        output.append(f"  Picks: {c['picks']:,} ({c['percentage']}%)")
        output.append(f"  Avg picks/product: {c['picks']//c['count'] if c['count'] > 0 else 0:,}")

        # Distribution
        output.append(f"\n{'='*60}")
        output.append("Distribution:")
        output.append(f"  A: {'█' * int(a['percentage']/2)} {a['percentage']}%")
        output.append(f"  B: {'█' * int(b['percentage']/2)} {b['percentage']}%")
        output.append(f"  C: {'█' * int(c['percentage']/2)} {c['percentage']}%")

        # Recommendations
        output.append(f"\n{'='*60}")
        output.append("💡 Recommendations:")
        output.append("  • Store Class A products near shipping area")
        output.append("  • Implement cycle counting for Class A items")
        output.append("  • Review Class C products for obsolescence")
        output.append(f"{'='*60}\n")

        return "\n".join(output)

    def _append_top_products(
        self, output: List[str], classification: List[Dict], abc_class: str, limit: int
    ) -> None:
        """Append top products to output list.

        Args:
            output: List to append to
            classification: List of product classifications
            abc_class: Class to filter ('A', 'B', or 'C')
            limit: Number of top products to show
        """
        class_products = [p for p in classification if p["abc_class"] == abc_class]
        top_products = class_products[:limit]

        if top_products:
            output.append(f"  Top {limit} examples:")
            for product in top_products:
                output.append(
                    f"    - [{product['no_produit']}] {product['nom_produit']}: "
                    f"{product['total_picked']:,} picks"
                )

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
