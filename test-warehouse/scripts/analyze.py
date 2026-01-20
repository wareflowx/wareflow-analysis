"""Wareflow Analyze Script
Run analysis views on database
"""
import sqlite3
from pathlib import Path


def run_analyses() -> None:
    """Run all analysis views."""
    db_path = Path("warehouse.db")

    if not db_path.exists():
        print("Error: warehouse.db not found!")
        print("Run 'wareflow import' first.")
        return

    print("Running analyses...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get table info
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print(f"\nTables in database: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")

    # Get row counts
    print("\nRow counts:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  {table[0]}: {count:,} rows")

    conn.close()
    print("\nAnalyses completed!")


if __name__ == "__main__":
    run_analyses()
