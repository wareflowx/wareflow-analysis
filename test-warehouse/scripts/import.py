"""Wareflow Import Script
Import Excel files to SQLite database
"""
import subprocess
import sys
from pathlib import Path


def run_import() -> None:
    """Run excel-to-sql import."""
    config_path = Path("config.yaml")

    if not config_path.exists():
        print("Error: config.yaml not found!")
        print("Are you in a wareflow project directory?")
        sys.exit(1)

    print("Importing data from Excel files...")
    result = subprocess.run(
        ["excel-to-sql", "import", "--config", "config.yaml"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"Import failed: {result.stderr}")
        sys.exit(1)

    print("Import completed!")
    print(result.stdout)


if __name__ == "__main__":
    run_import()
