"""Unit tests for Excel Builder module."""

import pytest
from pathlib import Path
import pandas as pd

from wareflow_analysis.export.excel_builder import ExcelBuilder


class TestExcelBuilder:
    """Test suite for ExcelBuilder class."""

    def test_create_workbook(self):
        """Test workbook creation."""
        builder = ExcelBuilder()
        assert builder.workbook is not None
        assert builder.default_sheet is not None
        assert builder.default_sheet.title == "Sheet1"

    def test_add_sheet_from_dict(self, tmp_path):
        """Test adding sheet from dictionary data."""
        builder = ExcelBuilder()

        data = [
            {"name": "Product A", "count": 100, "price": 10.5},
            {"name": "Product B", "count": 200, "price": 20.0},
        ]

        builder.add_sheet_from_dict("Products", data, title="Product List")

        # Verify sheet was created
        assert "Products" in builder.workbook.sheetnames

        # Save and verify
        output_path = tmp_path / "test.xlsx"
        builder.save(output_path)
        assert output_path.exists()

    def test_add_sheet_from_dataframe(self, tmp_path):
        """Test adding sheet from DataFrame."""
        builder = ExcelBuilder()

        df = pd.DataFrame({
            "category": ["A", "B", "C"],
            "count": [100, 200, 300],
            "percentage": [33.3, 66.7, 100.0]
        })

        builder.add_sheet_from_dataframe("Categories", df, title="Category Distribution")

        # Verify sheet was created
        assert "Categories" in builder.workbook.sheetnames

        # Save and verify
        output_path = tmp_path / "test_dataframe.xlsx"
        builder.save(output_path)
        assert output_path.exists()

    def test_add_sheet_with_key_value(self, tmp_path):
        """Test adding sheet from key-value dictionary."""
        builder = ExcelBuilder()

        data = {
            "Total Products": 1000,
            "Active": 950,
            "Inactive": 50,
        }

        builder.add_sheet_with_key_value("Summary", data, title="Inventory Summary")

        # Verify sheet was created
        assert "Summary" in builder.workbook.sheetnames

        # Save and verify
        output_path = tmp_path / "test_keyvalue.xlsx"
        builder.save(output_path)
        assert output_path.exists()

    def test_auto_adjust_columns(self, tmp_path):
        """Test column width auto-adjustment."""
        builder = ExcelBuilder()

        data = [
            {"category": "Very Long Category Name", "count": 100},
            {"category": "Short", "count": 200},
        ]

        builder.add_sheet_from_dict("Test", data)
        builder.auto_adjust_columns("Test")

        # Save to verify no errors
        output_path = tmp_path / "test_autowidth.xlsx"
        builder.save(output_path)
        assert output_path.exists()

    def test_freeze_panes(self, tmp_path):
        """Test freeze panes functionality."""
        builder = ExcelBuilder()

        data = [{"col1": "value1"} for _ in range(10)]
        builder.add_sheet_from_dict("TestSheet", data)
        builder.freeze_panes("TestSheet", row=2)

        # Save to verify no errors
        output_path = tmp_path / "test_freeze.xlsx"
        builder.save(output_path)
        assert output_path.exists()

    def test_remove_default_sheet(self, tmp_path):
        """Test removal of default empty sheet."""
        builder = ExcelBuilder()

        # Add a custom sheet
        data = [{"name": "Test"}]
        builder.add_sheet_from_dict("Custom", data)

        # Remove default sheet
        builder.remove_default_sheet()

        # Verify default sheet is removed
        assert "Sheet1" not in builder.workbook.sheetnames
        assert "Custom" in builder.workbook.sheetnames

        # Save and verify
        output_path = tmp_path / "test_remove_default.xlsx"
        builder.save(output_path)
        assert output_path.exists()

    def test_save_creates_directory(self, tmp_path):
        """Test that save creates output directory if needed."""
        builder = ExcelBuilder()

        data = [{"test": "value"}]
        builder.add_sheet_from_dict("Test", data)

        # Create path with non-existent subdirectories
        output_path = tmp_path / "subdir1" / "subdir2" / "test.xlsx"
        builder.save(output_path)

        assert output_path.exists()
        assert output_path.parent.exists()

    def test_empty_dataframe(self, tmp_path):
        """Test handling of empty DataFrame."""
        builder = ExcelBuilder()

        df = pd.DataFrame()
        builder.add_sheet_from_dataframe("Empty", df)

        # Verify sheet was created
        assert "Empty" in builder.workbook.sheetnames

        output_path = tmp_path / "test_empty.xlsx"
        builder.save(output_path)
        assert output_path.exists()

    def test_multiple_sheets(self, tmp_path):
        """Test workbook with multiple sheets."""
        builder = ExcelBuilder()

        # Add multiple sheets
        builder.add_sheet_from_dict("Sheet1", [{"a": 1}])
        builder.add_sheet_from_dict("Sheet2", [{"b": 2}])
        builder.add_sheet_from_dict("Sheet3", [{"c": 3}])

        # Verify all sheets exist
        assert "Sheet1" in builder.workbook.sheetnames
        assert "Sheet2" in builder.workbook.sheetnames
        assert "Sheet3" in builder.workbook.sheetnames

        output_path = tmp_path / "test_multiple.xlsx"
        builder.save(output_path)
        assert output_path.exists()
