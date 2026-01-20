"""Wareflow Export Script
Generate Excel reports from database
"""
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd


def run_export() -> None:
    """Generate Excel reports."""
    db_path = Path("warehouse.db")

    if not db_path.exists():
        print("Error: warehouse.db not found!")
        print("Run 'wareflow import' first.")
        return

    print("Generating Excel reports...")
    conn = sqlite3.connect(db_path)

    # Simple export: all tables
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"report_{timestamp}.xlsx"

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for table in tables:
            df = pd.read_sql(f"SELECT * FROM {table} LIMIT 1000", conn)
            df.to_excel(writer, sheet_name=table[:31], index=False)  # Excel limit

    conn.close()
    print(f"Report generated: {output_file}")


if __name__ == "__main__":
    run_export()
