# Export Command Implementation Plan

## Overview

This document provides a comprehensive analysis of implementing the `export` command for the Wareflow Analysis CLI. This command transforms database content and analysis results into professional Excel reports for business users.

## Current State

**Phase 1 (Completed)**: CLI infrastructure and `init` command ✅
**Phase 2 (In Progress)**: Data processing - `import` command 🔄
**Phase 3 (Planned)**: Data analysis - `analyze` command 📋
**Phase 4 (Next)**: Report generation - `export` command ❌

The `export` command is the **presentation layer** of the system:
- ❌ Cannot run without imported data
- ⚠️ Can run with or without `analyze` results
- ✅ Creates persistent artifacts (Excel files)
- ✅ Delivers value to business users

## Why the `export` Command After `analyze`?

According to the development flow:
```
init → import → analyze → export → run (full pipeline)
```

The `export` command comes after `analyze` because:
1. It can include both raw data AND analysis results
2. It's the final step before reports are usable
3. It completes the data-to-insights-to-reports pipeline
4. Business users consume Excel files, not databases

---

## Command Specifications

### Current Implementation

**File**: `src/wareflow_analysis/cli.py:48-50`

```python
@app.command()
def export() -> None:
    """Generate Excel reports."""
    typer.echo("Export command not implemented yet")
```

**Status**: Skeleton without implementation

### Command Responsibilities

The `export` command must:

#### 1. Database Connection
- **Check database exists**: Verify `warehouse.db` is present
- **Establish connection**: Connect to SQLite database
- **Verify data**: Ensure database has content

#### 2. Data Extraction
- **Read raw tables**: Extract data from SQLite tables
- **Optionally run analyses**: Calculate KPIs if not using `analyze` results
- **Prepare datasets**: Format data for Excel export

#### 3. Excel Generation
- **Create workbook**: Generate multi-sheet Excel file
- **Format content**: Apply professional styling
- **Add charts**: Include visualizations
- **Save file**: Write to output directory

---

## Strategic Decision: Progressive Implementation

### Implementation Approach

We'll use a **progressive implementation strategy**:

| Phase | Approach | Features | Timeline |
|-------|----------|----------|----------|
| **MVP** | Raw data export | Dump tables to Excel | 1-2 days |
| **Enhanced** | Analysis reports | KPIs, formatting, charts | 2-3 days |
| **Advanced** | Template system | Customizable reports | 3-4 days |

**Recommendation**: Start with MVP (raw data), add value incrementally.

### Export Modes

**Mode A: Raw Data Export (MVP)**
```bash
wareflow export --raw-only
```
- Exports database tables as-is
- One sheet per table
- Minimal formatting

**Mode B: Analysis Report (Enhanced)**
```bash
wareflow export
```
- Includes calculated KPIs
- Summary dashboard
- Charts and visualizations

**Mode C: Custom Template (Future)**
```bash
wareflow export --template custom_report
```
- User-defined report structure
- Configurable layouts
- Branded formatting

---

## Technical Architecture to Implement

### Phase 1: MVP Architecture (Initial Implementation)

#### File Structure

```
src/wareflow_analysis/
├── cli.py                      # ✅ Exists (to modify)
├── init.py                     # ✅ Exists
├── import/                     # 🔄 From import phase
├── analyze/                    # 📋 From analyze phase
├── export/                     # 🆕 New module
│   ├── __init__.py
│   ├── exporter.py             # Main export orchestration
│   ├── excel_builder.py        # Excel file generation
│   ├── formatter.py            # Excel styling and formatting
│   └── chart_builder.py        # Chart generation
└── templates/                  # ✅ Exists
```

#### Module Descriptions

**A. Module `exporter.py` - Main Orchestration**

```python
# exporter.py

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import pandas as pd

from export.excel_builder import ExcelBuilder
from export.formatter import CellFormatter

class ReportExporter:
    """Main export orchestrator."""

    def __init__(self, db_path: Path, output_dir: Path = None):
        self.db_path = db_path
        self.output_dir = output_dir or Path("output")
        self.conn = None
        self.builder = None
        self.formatter = CellFormatter()

    def connect(self) -> tuple[bool, str]:
        """Connect to database."""
        if not self.db_path.exists():
            return False, f"Database not found: {self.db_path}"

        try:
            self.conn = sqlite3.connect(self.db_path)
            return True, "Connected successfully"
        except Exception as e:
            return False, f"Connection failed: {e}"

    def verify_data(self) -> tuple[bool, str]:
        """Verify database has data."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM produits")
        count = cursor.fetchone()[0]

        if count == 0:
            return False, "Database is empty"

        return True, f"Data verified ({count} products)"

    def get_output_filename(self, suffix: str = "") -> Path:
        """Generate output filename with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"warehouse_report{suffix}_{timestamp}.xlsx"
        return self.output_dir / filename

    def export_raw_data(self) -> Dict:
        """Export raw database tables."""
        self.builder = ExcelBuilder()

        # Get all tables
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        # Export each table
        table_stats = {}
        for table in tables:
            df = pd.read_sql(f"SELECT * FROM {table}", self.conn)

            # Add sheet
            sheet_name = table[:31]  # Excel limit
            self.builder.add_sheet(sheet_name, df)

            # Basic formatting
            self.builder.format_header(sheet_name)

            table_stats[table] = len(df)

        return {
            "mode": "raw",
            "tables": table_stats,
            "total_rows": sum(table_stats.values())
        }

    def export_analysis_report(self) -> Dict:
        """Export with analysis and KPIs."""
        self.builder = ExcelBuilder()

        # 1. Summary sheet
        summary_data = self._get_summary_data()
        self.builder.add_sheet("Summary", summary_data)
        self.builder.format_summary("Summary")

        # 2. Movement analysis sheet
        movement_df = self._get_movement_analysis()
        self.builder.add_sheet("Movements", movement_df)
        self.builder.format_table("Movements")
        self.builder.add_bar_chart("Movements")

        # 3. Product performance sheet
        product_df = self._get_product_performance()
        self.builder.add_sheet("Products", product_df)
        self.builder.format_table("Products")

        # 4. Order statistics sheet
        order_df = self._get_order_statistics()
        self.builder.add_sheet("Orders", order_df)
        self.builder.format_table("Orders")
        self.builder.add_pie_chart("Orders")

        return {
            "mode": "analysis",
            "sheets": ["Summary", "Movements", "Products", "Orders"]
        }

    def _get_summary_data(self) -> pd.DataFrame:
        """Generate summary dashboard data."""
        cursor = self.conn.cursor()

        # Database overview
        cursor.execute("SELECT COUNT(*) FROM produits")
        products_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM mouvements")
        movements_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM commandes")
        orders_count = cursor.fetchone()[0]

        # Date range
        cursor.execute("SELECT MIN(date_heure), MAX(date_heure) FROM mouvements")
        min_date, max_date = cursor.fetchone()

        # Create summary dataframe
        summary = pd.DataFrame({
            "Metric": [
                "Total Products",
                "Total Movements",
                "Total Orders",
                "Date Range Start",
                "Date Range End"
            ],
            "Value": [
                products_count,
                f"{movements_count:,}",
                orders_count,
                str(min_date) if min_date else "N/A",
                str(max_date) if max_date else "N/A"
            ]
        })

        return summary

    def _get_movement_analysis(self) -> pd.DataFrame:
        """Get movement analysis data."""
        query = """
        SELECT
            type as 'Movement Type',
            COUNT(*) as 'Count',
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as '%',
            SUM(quantite) as 'Total Quantity',
            MIN(date_heure) as 'First Movement',
            MAX(date_heure) as 'Last Movement'
        FROM mouvements
        GROUP BY type
        ORDER BY COUNT(*) DESC
        """
        return pd.read_sql_query(query, self.conn)

    def _get_product_performance(self) -> pd.DataFrame:
        """Get product performance data."""
        query = """
        SELECT
            p.no_produit as 'Product ID',
            p.nom_produit as 'Product Name',
            COUNT(m.oid) as 'Total Movements',
            SUM(CASE WHEN m.type = 'SORTIE' THEN 1 ELSE 0 END) as 'Outbound',
            MAX(m.date_heure) as 'Last Movement'
        FROM produits p
        LEFT JOIN mouvements m ON p.no_produit = m.no_produit
        GROUP BY p.no_produit
        ORDER BY COUNT(m.oid) DESC
        LIMIT 50
        """
        return pd.read_sql_query(query, self.conn)

    def _get_order_statistics(self) -> pd.DataFrame:
        """Get order statistics data."""
        query = """
        SELECT
            etat as 'Status',
            COUNT(*) as 'Count',
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as '%',
            ROUND(AVG(lignes), 1) as 'Avg Lines',
            ROUND(AVG(priorite), 1) as 'Avg Priority'
        FROM commandes
        GROUP BY etat
        ORDER BY COUNT(*) DESC
        """
        return pd.read_sql_query(query, self.conn)

    def save(self, output_path: Path = None) -> Dict:
        """Save Excel file."""
        if output_path is None:
            output_path = self.get_output_filename()

        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save workbook
        file_size = self.builder.save(output_path)

        return {
            "path": output_path,
            "size_mb": round(file_size / (1024 * 1024), 2),
            "sheets": self.builder.sheet_count
        }

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
```

**B. Module `excel_builder.py` - Excel Generation**

```python
# excel_builder.py

from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.chart import BarChart, PieChart, Reference
import pandas as pd

class ExcelBuilder:
    """Build Excel workbooks with multiple sheets."""

    def __init__(self):
        self.wb = Workbook()
        self._remove_default_sheet()

    def _remove_default_sheet(self):
        """Remove default 'Sheet' if it exists."""
        if "Sheet" in self.wb.sheetnames:
            self.wb.remove(self.wb["Sheet"])

    def add_sheet(self, name: str, df: pd.DataFrame):
        """Add a sheet with DataFrame data."""
        ws = self.wb.create_sheet(title=name)

        # Write data
        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
            for c_idx, value in enumerate(row, 1):
                ws.cell(row=r_idx, column=c_idx, value=value)

    def format_header(self, sheet_name: str):
        """Apply basic header formatting."""
        from export.formatter import CellFormatter
        formatter = CellFormatter()
        ws = self.wb[sheet_name]
        formatter.format_header_row(ws)

    def format_table(self, sheet_name: str):
        """Format as data table."""
        from export.formatter import CellFormatter
        formatter = CellFormatter()
        ws = self.wb[sheet_name]
        formatter.format_data_table(ws)

    def format_summary(self, sheet_name: str):
        """Format summary sheet with dashboard style."""
        from export.formatter import CellFormatter
        formatter = CellFormatter()
        ws = self.wb[sheet_name]
        formatter.format_dashboard(ws)

    def add_bar_chart(self, sheet_name: str):
        """Add bar chart to sheet."""
        ws = self.wb[sheet_name]

        # Find data range
        max_row = ws.max_row
        max_col = ws.max_column

        # Create chart
        chart = BarChart()
        chart.title = "Movement Analysis"
        chart.style = 10

        # Data and categories
        data = Reference(ws, min_col=2, min_row=1, max_row=max_row, max_col=2)
        cats = Reference(ws, min_col=1, min_row=2, max_row=max_row)

        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)

        # Position chart
        ws.add_chart(chart, f"A{max_row + 2}")

    def add_pie_chart(self, sheet_name: str):
        """Add pie chart to sheet."""
        ws = self.wb[sheet_name]

        max_row = ws.max_row

        # Create chart
        chart = PieChart()
        chart.title = "Status Distribution"

        # Data and categories
        data = Reference(ws, min_col=2, min_row=1, max_row=max_row, max_col=2)
        cats = Reference(ws, min_col=1, min_row=2, max_row=max_row)

        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)

        # Position chart
        ws.add_chart(chart, f"A{max_row + 2}")

    def save(self, output_path) -> int:
        """Save workbook and return file size."""
        self.wb.save(output_path)
        return output_path.stat().st_size

    @property
    def sheet_count(self) -> int:
        """Return number of sheets."""
        return len(self.wb.sheetnames)
```

**C. Module `formatter.py` - Excel Styling**

```python
# formatter.py

from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side,
    NamedStyle
)
from openpyxl.utils import get_column_letter

class CellFormatter:
    """Format Excel cells and ranges."""

    # Styles
    HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
    HEADER_ALIGNMENT = Alignment(horizontal="center", vertical="center")

    DATA_ALIGNMENT = Alignment(horizontal="left", vertical="center")
    NUMBER_ALIGNMENT = Alignment(horizontal="right", vertical="center")

    THIN_BORDER = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    def format_header_row(self, ws):
        """Format the header row of a sheet."""
        for cell in ws[1]:
            cell.fill = self.HEADER_FILL
            cell.font = self.HEADER_FONT
            cell.alignment = self.HEADER_ALIGNMENT
            cell.border = self.THIN_BORDER

    def format_data_table(self, ws):
        """Format as a data table with borders and alternating rows."""
        # Apply borders to all cells
        for row in ws.iter_rows():
            for cell in row:
                cell.border = self.THIN_BORDER
                if cell.row == 1:
                    continue
                cell.alignment = self.DATA_ALIGNMENT

        # Auto-fit columns
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)

            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass

            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

    def format_dashboard(self, ws):
        """Format as a dashboard summary."""
        # Title
        ws['A1'].font = Font(bold=True, size=14, color="2F5597")
        ws['A1'].alignment = Alignment(horizontal="left", vertical="center")

        # Metrics
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            for cell in row:
                if cell.row == 1:
                    continue
                cell.border = self.THIN_BORDER

                # Metric name
                if cell.column == 1:
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal="left", vertical="center")
                # Value
                else:
                    cell.font = Font(size=12)
                    cell.alignment = Alignment(horizontal="left", vertical="center")
```

---

## Complete Execution Flow

### `export` Command Algorithm

```
┌─────────────────────────────────────┐
│ 1. Check Database                   │
│    - warehouse.db exists?           │
│    - Can connect?                   │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 2. Verify Data                      │
│    - Tables have data?              │
│    - Not empty?                     │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 3. Determine Export Mode           │
│    - Raw data only?                 │
│    - Include analyses?              │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 4. Extract Data                    │
│    ┌─────────────────────────────┐  │
│    │ a. Read tables from DB       │  │
│    │ b. Run analysis queries      │  │
│    │ c. Prepare DataFrames        │  │
│    └─────────────────────────────┘  │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 5. Build Excel Workbook            │
│    ┌─────────────────────────────┐  │
│    │ a. Create workbook           │  │
│    │ b. Add sheets                │  │
│    │ c. Apply formatting          │  │
│    │ d. Add charts (optional)     │  │
│    └─────────────────────────────┘  │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 6. Save File                       │
│    - Create output directory       │
│    - Write Excel file              │
│    - Report file info              │
└─────────────────────────────────────┘
```

---

## Report Structure

### MVP Report Structure (Raw Export)

**File**: `output/raw_data_YYYYMMDD_HHMMSS.xlsx`

| Sheet | Content | Rows | Format |
|-------|---------|------|--------|
| produits | Raw products table | ~1,234 | Basic |
| mouvements | Raw movements table | ~45,678 | Basic |
| commandes | Raw orders table | ~789 | Basic |
| receptions | Raw receptions table | ~234 | Basic |

**Formatting**:
- Headers: Blue background, white bold text
- Columns: Auto-width
- Numbers: Right-aligned
- Text: Left-aligned

### Enhanced Report Structure (Analysis)

**File**: `output/warehouse_report_YYYYMMDD_HHMMSS.xlsx`

#### Sheet 1: Summary (Dashboard)

```
┌────────────────────────────────────────────────────┐
│         WAREHOUSE ANALYSIS REPORT                 │
│         Generated: 2025-01-21 14:30:45           │
├────────────────────────────────────────────────────┤
│                                                    │
│  DATABASE OVERVIEW                                 │
│  ─────────────────                                 │
│  Total Products:           1,234                  │
│  Total Movements:         45,678                  │
│  Total Orders:              789                   │
│                                                    │
│  TIME RANGE                                        │
│  ───────────                                        │
│  First Movement:    2024-01-01 08:00:00          │
│  Last Movement:     2025-01-21 17:30:00          │
│  Span:              386 days                     │
│                                                    │
│  KEY PERFORMANCE INDICATORS                       │
│  ────────────────────────────────                  │
│  Avg Movements/Day:          118                   │
│  Active Products:        1,078 (87%)              │
│  Completion Rate:           58%                    │
└────────────────────────────────────────────────────┘
```

#### Sheet 2: Movements

| Movement Type | Count | % | Total Quantity | First Movement | Last Movement |
|---------------|-------|---|----------------|----------------|---------------|
| SORTIE | 28,901 | 63.3% | 156,789 | 2024-01-01 08:00 | 2025-01-21 17:30 |
| ENTRÉE | 12,345 | 27.0% | 98,765 | 2024-01-02 09:15 | 2025-01-20 16:45 |
| TRANSFERT | 4,432 | 9.7% | 12,345 | 2024-01-05 10:00 | 2025-01-19 14:20 |

**Chart**: Bar chart showing movement distribution

#### Sheet 3: Products

| Product ID | Product Name | Total Movements | Outbound | Last Movement |
|------------|--------------|-----------------|----------|---------------|
| 1001 | Product Alpha | 1,234 | 892 | 2025-01-21 15:30 |
| 1045 | Product Beta | 987 | 765 | 2025-01-21 14:15 |
| 1123 | Product Gamma | 876 | 654 | 2025-01-21 13:00 |
| ... | ... | ... | ... | ... |

**Formatting**: Top 50 products by activity

#### Sheet 4: Orders

| Status | Count | % | Avg Lines | Avg Priority |
|--------|-------|---|-----------|--------------|
| TERMINÉ | 456 | 57.8% | 15.2 | 2.1 |
| EN_COURS | 234 | 29.7% | 8.3 | 3.2 |
| EN_ATTENTE | 89 | 11.3% | 5.1 | 2.8 |
| ANNULÉ | 10 | 1.3% | 2.0 | 1.5 |

**Chart**: Pie chart showing status distribution

---

## User Experience Design

### Scenario 1: First Export After Import

**Context**: User just completed `wareflow import`

```bash
$ wareflow export --raw-only
```

**Output**:
```
✓ Starting export process...

🔗 Database: warehouse.db
📊 Verifying data...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ produits sheet created        1,234 rows [0.3s]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ mouvements sheet created     45,678 rows [1.2s]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ commandes sheet created        789 rows [0.2s]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ receptions sheet created       234 rows [0.1s]


✅ Export completed successfully!

📄 Report: output/raw_data_20250121_143045.xlsx
   Size: 3.2 MB
   Sheets: 4
   Rows: 47,935

💡 Next steps:
  open output/raw_data_*.xlsx    # View in Excel
  wareflow analyze               # Generate analysis first
```

---

### Scenario 2: Full Analysis Export

**Context**: User ran `wareflow analyze` and wants a complete report

```bash
$ wareflow export
```

**Output**:
```
✓ Starting export process...

🔗 Database: warehouse.db
📊 Including analysis results...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ Summary dashboard created              [0.4s]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ Movements analysis & chart created     [0.8s]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ Products performance created           [0.5s]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ Orders statistics & chart created      [0.4s]


✅ Export completed successfully!

📄 Report: output/warehouse_report_20250121_143108.xlsx
   Size: 2.8 MB
   Sheets: 4

📊 Report includes:
   • Summary dashboard with KPIs
   • Movement analysis with bar chart
   • Product performance ranking (top 50)
   • Order status distribution with pie chart

💡 Next steps:
  open output/warehouse_report_*.xlsx    # View report
```

---

### Scenario 3: Export Without Data

**Context**: User tries to export before importing

```bash
$ wareflow export
```

**Output**:
```
❌ Error: No data to export

Database is empty or missing.

💡 Solution:
  1. Run 'wareflow import' to load data from Excel files
  2. Verify import completed successfully
  3. Check database status: wareflow status
```

---

### Scenario 4: Custom Output Location

**Context**: User wants to export to specific location

```bash
$ wareflow export --output ./reports
```

**Output**:
```
✓ Starting export process...

📁 Output directory: ./reports
🔗 Database: warehouse.db

[Export progress...]

✅ Export completed successfully!

📄 Report: ./reports/warehouse_report_20250121_143500.xlsx
   Size: 2.8 MB
   Sheets: 4
```

---

### Scenario 5: Export Multiple Formats

**Context**: User needs different formats

```bash
$ wareflow export --format xlsx
✅ Exported to XLSX: output/warehouse_report_*.xlsx

$ wareflow export --format csv
✅ Exported to CSV:
   output/produits_20250121_143500.csv
   output/mouvements_20250121_143500.csv
   output/commandes_20250121_143500.csv
```

---

## Error Handling Strategy

### Validation Errors

| Error Type | Check | Action | Message |
|------------|-------|--------|---------|
| Database not found | File exists | Exit with error | "Database not found: run import first" |
| Empty database | Row count = 0 | Exit with error | "Database is empty: no data to export" |
| Output permission | Write access | Exit with error | "Cannot write to output directory" |
| Disk full | Space check | Exit with error | "Insufficient disk space" |

### Error Messages

```python
ERROR_MESSAGES = {
    "no_database": """
❌ Error: Database not found

  File: warehouse.db does not exist

💡 Solution:
  Run 'wareflow import' to create and populate the database.
""",

    "empty_database": """
❌ Error: Database is empty

  All tables are empty or missing data

💡 Solution:
  1. Verify Excel files are in data/ directory
  2. Run 'wareflow import' to load data
  3. Check import completed successfully
""",

    "cannot_write": """
❌ Error: Cannot write to output directory

  Directory: {output_dir}

💡 Solution:
  1. Check directory exists and is writable
  2. Use --output to specify different location
  3. Check disk space available
""",

    "disk_full": """
❌ Error: Insufficient disk space

  Required: {required_mb} MB
  Available: {available_mb} MB

💡 Solution:
  1. Free up disk space
  2. Use --raw-only for smaller export
  3. Export to different drive
"""
}
```

---

## Command Options

| Option | Purpose | When to Use |
|--------|---------|-------------|
| `--raw-only` | Export raw tables only | Quick data dump, no analysis |
| `--output PATH` | Custom output directory | Export to specific location |
| `--format FORMAT` | Output format (xlsx/csv) | Need different file format |
| `--name NAME` | Custom filename | Specific naming convention |
| `--no-charts` | Skip chart generation | Faster export, no visuals |
| `--max-rows N` | Limit rows per sheet | Large datasets, performance |
| `--template TEMPLATE` | Use custom template (future) | Branded/custom reports |

---

## Performance Considerations

### Optimization Strategies

1. **Chunk Writing**
   - Write large tables in chunks
   - Reduce memory footprint
   - Show progress

2. **Conditional Formatting**
   - Skip charts if not needed (`--no-charts`)
   - Optional advanced formatting

3. **Streaming for Large Data**
   - Use generators for large datasets
   - Avoid loading all data in memory

4. **Async Operations** (future)
   - Parallel sheet generation
   - Background chart creation

### Performance Targets

| Operation | Rows | Target Time |
|-----------|------|-------------|
| Small export | < 5,000 | < 5 seconds |
| Medium export | 5,000 - 50,000 | < 30 seconds |
| Large export | 50,000 - 500,000 | < 2 minutes |
| With charts | Any | + 5-10 seconds |

---

## Tests to Implement

### Unit Tests

```python
# tests/test_export_excel_builder.py
def test_create_workbook()
def test_add_sheet()
def test_format_header()
def test_add_bar_chart()
def test_add_pie_chart()
def test_save_workbook()

# tests/test_export_formatter.py
def test_format_header_row()
def test_format_data_table()
def test_format_dashboard()
def test_auto_column_width()

# tests/test_export_exporter.py
def test_connect_to_database()
def test_verify_data_with_empty_db()
def test_export_raw_data()
def test_export_analysis_report()
def test_get_summary_data()
```

### Integration Tests

```python
# tests/test_export_integration.py
def test_full_export_flow()
def test_export_after_import()
def test_export_with_analyze()
def test_export_without_import()
def test_custom_output_directory()
```

---

## Success Metrics

### Functional Objectives

- ✅ Successfully export database tables to Excel
- ✅ Include analysis results when requested
- ✅ Apply professional formatting
- ✅ Generate charts and visualizations
- ✅ Handle large datasets efficiently

### Technical Objectives

- ✅ Support XLSX format (openpyxl)
- ✅ Optional CSV format
- ✅ Memory efficient (< 500MB for 100K rows)
- ✅ Proper Excel compatibility

### Quality Objectives

- ✅ Test coverage > 80%
- ✅ Clean Excel output (no warnings)
- ✅ Professional appearance
- ✅ Cross-platform compatibility

---

## Future Enhancements

### Template System (Future)

Enable customizable report templates:

```yaml
# templates/monthly_report.yaml
name: "Monthly Warehouse Report"
sheets:
  - name: "Executive Summary"
    type: "dashboard"
    content:
      - kpi: "total_movements"
        label: "Total This Month"
        formula: "COUNT(mouvements)"
      - kpi: "completion_rate"
        label: "Order Completion"
        formula: "AVG(completion)"

  - name: "Top Products"
    type: "table"
    query: "SELECT * FROM top_products LIMIT 20"
    chart: "bar"

  - name: "Trends"
    type: "chart"
    chart_type: "line"
    query: "SELECT date, COUNT(*) FROM movements GROUP BY date"
```

### Advanced Formatting (Future)

- Conditional formatting (color scales)
- Pivot tables
- Sparklines
- Custom themes
- Company branding

### Multiple Output Formats (Future)

- PDF export
- HTML report
- Power BI integration
- Email reports

---

## Dependencies with Other Commands

### Dependency on `import`

**Critical**: Cannot export without imported data

```bash
wareflow import   # MUST run first
wareflow export   # Then can export
```

### Optional Dependency on `analyze`

**Two approaches**:

**Option A**: Standalone export
```bash
wareflow import
wareflow export   # Runs its own analysis queries
```

**Option B**: Export with analyze results
```bash
wareflow import
wareflow analyze  # Stores analysis results
wareflow export   # Uses stored results
```

**Recommendation**: Start with Option A, add Option B as enhancement.

### Integration with `run`

**Full pipeline**:
```bash
wareflow run  # → import → analyze → export
```

The `run` command completes the full pipeline and produces the final report.

---

## Expected Deliverables

### Code
- 4 Python modules in `src/wareflow_analysis/export/`
- Modified `cli.py` with export command
- Excel styling templates

### Tests
- 15+ unit tests
- 4+ integration tests
- Sample Excel outputs

### Documentation
- Complete docstrings
- User guide for export command
- Report format documentation

### Artifacts
- Sample Excel reports
- Style guide for reports
- Performance benchmarks

---

## Implementation Phases

### Phase 1: MVP - Raw Export (Day 1-2)
1. Create `export/` module structure
2. Implement basic Excel generation
3. Export all tables as-is
4. Basic formatting only
5. CLI integration

### Phase 2: Enhanced Reports (Day 3-5)
6. Add summary dashboard
7. Include analysis queries
8. Implement charts
9. Professional formatting
10. Multiple export modes

### Phase 3: Polish & Advanced Features (Day 6-7)
11. Performance optimization
12. CSV format support
13. Error handling
14. Complete testing
15. Documentation

---

## Best Practices

### Excel Generation

1. **Memory Management**
   - Process tables sequentially
   - Close connections properly
   - Clear large objects when done

2. **Performance**
   - Use efficient data structures
   - Minimize style operations
   - Batch cell updates

3. **Compatibility**
   - Test with Microsoft Excel
   - Test with LibreOffice Calc
   - Test with Google Sheets (import)

4. **User Experience**
   - Progress feedback for large exports
   - Clear file naming
   - Reasonable file sizes

### Report Design

1. **Clarity**
   - Clear titles and labels
   - Logical sheet organization
   - Consistent formatting

2. **Relevance**
   - Most important data first
   - Summary before details
   - KPIs prominently displayed

3. **Visual Appeal**
   - Professional color scheme
   - Readable fonts
   - Appropriate chart types

---

## Conclusion

The `export` command is the **presentation layer** that makes warehouse data accessible and actionable for business users. It completes the data pipeline by transforming technical database content into professional Excel reports.

**Implementation Philosophy**:
1. **Start simple**: Raw table export
2. **Add intelligence**: Analysis and KPIs
3. **Enhance presentation**: Formatting and charts
4. **Customize later**: Templates and branding

**Value Delivered**:
- Business users get Excel reports (familiar format)
- Shareable insights via email or shared drives
- Professional appearance for stakeholder communication
- Persistent artifacts for historical tracking

**Next Steps After Export**:
1. Implement `run` command for full pipeline automation
2. Gather user feedback on report formats
3. Enhance based on real usage patterns
4. Consider template system for customization

---

*Document created: 2025-01-21*
*Status: Implementation Plan - Ready for Development*
*Priority: HIGH - Final layer of data pipeline*
