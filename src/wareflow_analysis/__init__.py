"""Wareflow Analysis - Warehouse data analysis CLI."""

from pathlib import Path

# Get the templates directory
templates_dir = Path(__file__).parent / "templates"

__all__ = ["templates_dir"]
