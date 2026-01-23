"""Unit tests for Excel Formatters module."""

import pytest

from wareflow_analysis.export.formatters import ExcelFormatter
from wareflow_analysis.export.excel_builder import ExcelBuilder


class TestExcelFormatter:
    """Test suite for ExcelFormatter class."""

    def test_formatter_initialization(self):
        """Test formatter initialization."""
        formatter = ExcelFormatter()
        assert formatter is not None

    def test_predefined_styles_exist(self):
        """Test that all predefined styles are available."""
        formatter = ExcelFormatter()

        assert hasattr(formatter, "HEADER_STYLE")
        assert hasattr(formatter, "NUMBER_STYLE")
        assert hasattr(formatter, "PERCENTAGE_STYLE")
        assert hasattr(formatter, "WARNING_STYLE")
        assert hasattr(formatter, "TITLE_STYLE")

        # Verify style structure
        assert "font" in formatter.HEADER_STYLE
        assert "fill" in formatter.HEADER_STYLE
        assert "alignment" in formatter.HEADER_STYLE
        assert "border" in formatter.HEADER_STYLE

    def test_apply_style_to_cell(self, tmp_path):
        """Test applying style to a specific cell."""
        builder = ExcelBuilder()
        formatter = ExcelFormatter()

        data = [{"value": 100}]
        builder.add_sheet_from_dict("Test", data)

        sheet = builder.workbook["Test"]
        formatter.apply_style_to_cell(sheet, 2, 1, formatter.WARNING_STYLE)

        # Save to verify no errors
        output_path = tmp_path / "test_style.xlsx"
        builder.save(output_path)
        assert output_path.exists()

    def test_apply_header_style_to_row(self, tmp_path):
        """Test applying header style to entire row."""
        builder = ExcelBuilder()
        formatter = ExcelFormatter()

        data = [{"col1": "a", "col2": "b", "col3": "c"}]
        builder.add_sheet_from_dict("Test", data)

        sheet = builder.workbook["Test"]
        formatter.apply_header_style_to_row(sheet, 2, 3)

        output_path = tmp_path / "test_header_row.xlsx"
        builder.save(output_path)
        assert output_path.exists()

    def test_format_summary_table(self, tmp_path):
        """Test formatting a summary table."""
        builder = ExcelBuilder()
        formatter = ExcelFormatter()

        builder.add_sheet_with_key_value("Summary", {}, title="Test")

        sheet = builder.workbook["Summary"]

        data = {
            "Total Products": 1000,
            "Active": 950,
            "Inactive": 50,
        }

        rows_written = formatter.format_summary_table(sheet, 3, data)
        assert rows_written == 3

        output_path = tmp_path / "test_summary_table.xlsx"
        builder.save(output_path)
        assert output_path.exists()

    def test_format_data_table(self, tmp_path):
        """Test formatting a data table."""
        builder = ExcelBuilder()
        formatter = ExcelFormatter()

        builder.add_sheet_from_dict("Data", [{}])

        sheet = builder.workbook["Data"]

        headers = ["Category", "Count", "Percentage"]
        data_rows = [
            ["A", 100, 33.3],
            ["B", 200, 66.7],
        ]

        rows_written = formatter.format_data_table(sheet, 2, headers, data_rows)
        assert rows_written == 3  # 1 header + 2 data rows

        output_path = tmp_path / "test_data_table.xlsx"
        builder.save(output_path)
        assert output_path.exists()

    def test_add_warning_row(self, tmp_path):
        """Test adding a warning row."""
        builder = ExcelBuilder()
        formatter = ExcelFormatter()

        builder.add_sheet_from_dict("Warnings", [{}])

        sheet = builder.workbook["Warnings"]
        formatter.add_warning_row(sheet, 2, "⚠️  Warning: Missing EAN codes")

        output_path = tmp_path / "test_warning.xlsx"
        builder.save(output_path)
        assert output_path.exists()

    def test_add_title(self, tmp_path):
        """Test adding a title."""
        builder = ExcelBuilder()
        formatter = ExcelFormatter()

        builder.add_sheet_from_dict("Title", [{}])

        sheet = builder.workbook["Title"]
        formatter.add_title(sheet, 2, "Inventory Analysis Report")

        output_path = tmp_path / "test_title.xlsx"
        builder.save(output_path)
        assert output_path.exists()

    def test_apply_borders_to_range(self, tmp_path):
        """Test applying borders to a range of cells."""
        builder = ExcelBuilder()
        formatter = ExcelFormatter()

        data = [{"a": 1, "b": 2, "c": 3} for _ in range(5)]
        builder.add_sheet_from_dict("Borders", data)

        sheet = builder.workbook["Borders"]
        formatter.apply_borders_to_range(sheet, 2, 1, 7, 3)

        output_path = tmp_path / "test_borders.xlsx"
        builder.save(output_path)
        assert output_path.exists()

    def test_number_formatting(self):
        """Test that number formatting is correctly defined."""
        formatter = ExcelFormatter()

        assert "#,##0" in formatter.NUMBER_STYLE["number_format"]
        assert "0.0" in formatter.PERCENTAGE_STYLE["number_format"]

    def test_alignment_settings(self):
        """Test that alignment settings are properly defined."""
        formatter = ExcelFormatter()

        # Header should be centered
        assert formatter.HEADER_STYLE["alignment"].horizontal == "center"
        assert formatter.HEADER_STYLE["alignment"].vertical == "center"

        # Number should be right-aligned
        assert formatter.NUMBER_STYLE["alignment"].horizontal == "right"

        # Warning should be left-aligned
        assert formatter.WARNING_STYLE["alignment"].horizontal == "left"
