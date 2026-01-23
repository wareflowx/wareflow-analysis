"""Inventory Report Exporter.

Exports inventory analysis results to formatted Excel workbook.
"""

from pathlib import Path
from datetime import datetime
import pandas as pd

from wareflow_analysis.export.excel_builder import ExcelBuilder
from wareflow_analysis.export.formatters import ExcelFormatter


class InventoryReportExporter:
    """Export inventory analysis results to Excel."""

    def __init__(self):
        """Initialize inventory report exporter."""
        self.builder = None
        self.formatter = None

    def export(self, results: dict, output_path: Path) -> None:
        """Export inventory analysis results to Excel file.

        Args:
            results: Dictionary with inventory analysis results
            output_path: Path where to save the Excel file
        """
        # Initialize builder and formatter
        self.builder = ExcelBuilder()
        self.formatter = ExcelFormatter()

        # Create summary sheet
        self._create_summary_sheet(results)

        # Create category distribution sheet
        self._create_category_sheet(results)

        # Create status distribution sheet
        self._create_status_sheet(results)

        # Remove default empty sheet if exists
        self.builder.remove_default_sheet()

        # Save the workbook
        self.builder.save(output_path)

    def _create_summary_sheet(self, results: dict) -> None:
        """Create the summary sheet with overview statistics.

        Args:
            results: Inventory analysis results
        """
        sheet_name = "Résumé"
        total_products = results.get("total_products", 0)
        by_category = results.get("by_category", [])
        by_status = results.get("by_status", [])
        issues = results.get("issues", {})

        # Create sheet
        self.builder.add_sheet_with_key_value(
            sheet_name=sheet_name,
            data={
                "Total produits": total_products,
                "Nombre de catégories": len(by_category),
                "États différents": len(by_status),
            },
            title=f"ANALYSE D'INVENTAIRE - {datetime.now().strftime('%Y-%m-%d')}",
        )

        # Get the sheet to add more content
        sheet = self.builder.workbook[sheet_name]

        # Current row for adding content
        current_row = 6  # After title and summary data

        # Add category section
        self.formatter.add_title(sheet, current_row, "Par Catégorie:")
        current_row += 2

        # Add category headers
        headers = ["Catégorie", "Nombre", "%"]
        self.formatter.format_data_table(
            sheet,
            current_row,
            headers,
            [[cat["category"], cat["count"], f"{cat['percentage']:.1f}%"] for cat in by_category[:10]],
        )
        current_row += len(by_category) + 2

        # Add status section
        self.formatter.add_title(sheet, current_row, "Par État:")
        current_row += 2

        # Add status headers
        headers = ["État", "Nombre", "%"]
        self.formatter.format_data_table(
            sheet,
            current_row,
            headers,
            [[status["status"], status["count"], f"{status['percentage']:.1f}%"] for status in by_status],
        )
        current_row += len(by_status) + 2

        # Add issues section
        if any(issues.values()):
            self.formatter.add_title(sheet, current_row, "Problèmes de Qualité:")
            current_row += 2

            if issues.get("missing_ean", 0) > 0:
                self.formatter.add_warning_row(
                    sheet,
                    current_row,
                    f"⚠️  {issues['missing_ean']:,} produits sans code EAN",
                )
                current_row += 1

            if issues.get("missing_description", 0) > 0:
                self.formatter.add_warning_row(
                    sheet,
                    current_row,
                    f"⚠️  {issues['missing_description']:,} produits sans description",
                )
                current_row += 1

            if issues.get("missing_name", 0) > 0:
                self.formatter.add_warning_row(
                    sheet,
                    current_row,
                    f"⚠️  {issues['missing_name']:,} produits sans nom",
                )
                current_row += 1
        else:
            self.formatter.add_title(sheet, current_row, "✅ Aucun problème de qualité détecté!")

        # Auto-adjust columns
        self.builder.auto_adjust_columns(sheet_name)

    def _create_category_sheet(self, results: dict) -> None:
        """Create detailed category distribution sheet.

        Args:
            results: Inventory analysis results
        """
        sheet_name = "Par Catégorie"
        by_category = results.get("by_category", [])

        if not by_category:
            return

        # Convert to DataFrame
        df = pd.DataFrame(by_category)

        # Add sheet with title
        title = f"Distribution par Catégorie - Total: {sum(c['count'] for c in by_category):,} produits"
        self.builder.add_sheet_from_dataframe(sheet_name, df, title=title)

        # Get sheet and format
        sheet = self.builder.workbook[sheet_name]

        # Format percentage column
        for row in range(3, len(by_category) + 3):
            cell = sheet.cell(row=row, column=3)
            cell.number_format = "0.0"
            cell.alignment = self.formatter.PERCENTAGE_STYLE["alignment"]

        # Auto-adjust columns
        self.builder.auto_adjust_columns(sheet_name)

        # Freeze header row
        self.builder.freeze_panes(sheet_name, row=3)

    def _create_status_sheet(self, results: dict) -> None:
        """Create detailed status distribution sheet.

        Args:
            results: Inventory analysis results
        """
        sheet_name = "Par État"
        by_status = results.get("by_status", [])

        if not by_status:
            return

        # Convert to DataFrame
        df = pd.DataFrame(by_status)

        # Add sheet with title
        title = f"Distribution par État - Total: {sum(s['count'] for s in by_status):,} produits"
        self.builder.add_sheet_from_dataframe(sheet_name, df, title=title)

        # Get sheet and format
        sheet = self.builder.workbook[sheet_name]

        # Format percentage column
        for row in range(3, len(by_status) + 3):
            cell = sheet.cell(row=row, column=3)
            cell.number_format = "0.0"
            cell.alignment = self.formatter.PERCENTAGE_STYLE["alignment"]

        # Auto-adjust columns
        self.builder.auto_adjust_columns(sheet_name)

        # Freeze header row
        self.builder.freeze_panes(sheet_name, row=3)
