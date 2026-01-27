# Import and Export Workflows

## Overview

This document describes the complete workflows for importing raw Excel data and exporting formatted Excel reports.

## Import Workflow

### Step-by-Step Process

```
┌─────────────────────────────────────────────────────────────┐
│  1. FILE SELECTION                                           │
│     User selects Excel file(s) via drag & drop or browser    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  2. FILE VALIDATION                                          │
│     ✓ Check file format (.xlsx, .xls)                        │
│     ✓ Check file size (max 100MB)                            │
│     ✓ Check file integrity                                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  3. FILE PARSING                                             │
│     • Parse Excel sheets                                     │
│     • Extract headers and data                               │
│     • Detect data types                                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  4. TEMPLATE MATCHING                                        │
│     • Match columns against known templates                  │
│     • Calculate confidence scores                            │
│     • Suggest best matching template                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  5. MAPPING REVIEW (User Interaction)                        │
│     • Show detected mapping                                  │
│     • Allow user adjustments                                 │
│     • Preview data transformation                            │
│     • Confirm or modify template selection                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  6. DATA VALIDATION                                          │
│     • Validate required columns present                      │
│     • Validate data types                                    │
│     • Check business rules                                   │
│     • Verify referential integrity                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  7. DATA TRANSFORMATION                                     │
│     • Normalize column names                                 │
│     • Convert data types                                     │
│     • Apply transformations                                  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  8. DATABASE LOADING                                         │
│     • Create/update schema                                  │
│     • Batch insert data                                     │
│     • Update indexes                                         │
│     • Create data version                                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  9. POST-IMPORT                                              │
│     • Update available analyses                             │
│     • Calculate base statistics                            │
│     • Create baseline metrics                               │
│     • Generate data quality report                          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  10. COMPLETE                                                │
│      Show summary and next steps                             │
└─────────────────────────────────────────────────────────────┘
```

### Import State Machine

```typescript
type ImportState =
  | 'idle'           // No import in progress
  | 'selecting'      // User selecting files
  | 'validating'     // Validating file format
  | 'parsing'        // Parsing file contents
  | 'matching'       // Matching templates
  | 'reviewing'      // User reviewing mapping
  | 'validating-data'// Validating data
  | 'transforming'   // Transforming data
  | 'loading'        // Loading to database
  | 'finalizing'     // Post-import tasks
  | 'completed'      // Import complete
  | 'failed'         // Import failed

type ImportEvent =
  | { type: 'SELECT_FILES'; files: File[] }
  | { type: 'VALIDATION_PASS' }
  | { type: 'VALIDATION_FAIL'; errors: ImportError[] }
  | { type: 'PARSE_COMPLETE'; data: ParsedData }
  | { type: 'TEMPLATE_SELECTED'; template: DataTemplate }
  | { type: 'MAPPING_CONFIRMED'; mapping: ColumnMapping[] }
  | { type: 'DATA_VALIDATION_PASS' }
  | { type: 'DATA_VALIDATION_FAIL'; errors: ValidationError[] }
  | { type: 'LOAD_COMPLETE'; stats: ImportStats }
  | { type: 'FINALIZE_COMPLETE' }
  | { type: 'ERROR'; error: Error }
```

### Import Progress Tracking

```typescript
interface ImportProgress {
  state: ImportState
  progress: number  // 0-100
  currentStep: string
  totalSteps: number
  currentStepNumber: number

  // Detailed progress
  details: {
    rowsProcessed: number
    totalRows: number
    tablesProcessed: number
    totalTables: number
  }

  // Errors and warnings
  errors: ImportError[]
  warnings: ImportWarning[]

  // Estimated time remaining
  eta: number | null  // seconds
}

// Progress update callback
type ProgressCallback = (progress: ImportProgress) => void
```

### Error Handling

```typescript
interface ImportError {
  type: 'file' | 'sheet' | 'column' | 'row' | 'value' | 'database'
  severity: 'error' | 'warning' | 'info'

  // Location
  file?: string
  sheet?: string
  row?: number
  column?: string

  // Error details
  code: string
  message: string
  suggestion?: string

  // Recovery
  canContinue: boolean
  recoveryAction?: string
}

// Error categories
const ERROR_CODES = {
  // File errors
  FILE_NOT_FOUND: 'E001',
  FILE_TOO_LARGE: 'E002',
  INVALID_FORMAT: 'E003',
  CORRUPT_FILE: 'E004',

  // Sheet errors
  NO_SHEETS: 'E101',
  EMPTY_SHEET: 'E102',
  SHEET_NOT_FOUND: 'E103',

  // Column errors
  REQUIRED_COLUMN_MISSING: 'E201',
  COLUMN_TYPE_MISMATCH: 'E202',
  DUPLICATE_COLUMN: 'E203',

  // Row errors
  DUPLICATE_PRIMARY_KEY: 'E301',
  MISSING_FOREIGN_KEY: 'E302',
  INVALID_VALUE: 'E303',

  // Database errors
  CONNECTION_FAILED: 'E401',
  CONSTRAINT_VIOLATION: 'E402',
  TRANSACTION_FAILED: 'E403'
}
```

## Export Workflow

### Export Process

```
┌─────────────────────────────────────────────────────────────┐
│  1. SELECT EXPORT                                           │
│     User chooses analysis result to export                  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  2. SELECT TEMPLATE                                         │
│     User selects export template or uses default            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  3. CONFIGURE EXPORT                                        │
│     • Choose output filename                                │
│     • Choose output location                                │
│     • Configure formatting options                          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  4. GENERATE EXCEL                                          │
│     • Apply template formatting                             │
│     • Create sheets                                         │
│     • Add data                                              │
│     • Add charts and visualizations                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  5. SAVE FILE                                               │
│     Write Excel file to disk                                │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  6. COMPLETE                                                │
│     Show success message and open location                  │
└─────────────────────────────────────────────────────────────┘
```

### Export Template Structure

```typescript
interface ExportTemplate {
  id: string
  name: string
  description: string

  // Sheets configuration
  sheets: SheetConfig[]

  // Global formatting
  formatting: {
    // Metadata
    title?: string
    subtitle?: string
    logo?: string
    author?: string
    generatedAt?: boolean

    // Styles
    headerFont: { name: string; size: number; bold: boolean; color: string }
    rowFont: { name: string; size: number; bold: boolean; color: string }

    // Colors
    headerBgColor: string
    alternateRowColor: string

    // Borders
    borderStyle: 'thin' | 'medium' | 'thick'
    borderColor: string
  }
}

interface SheetConfig {
  name: string
  type: 'data' | 'summary' | 'chart' | 'pivot'

  // Data source
  dataSource: {
    analysisId?: string
    tableName?: string
    query?: string
  }

  // Layout
  layout: {
    freezeHeader: boolean
    autoFilter: boolean
    autoFitColumns: boolean
    columnWidths?: Record<string, number>
  }

  // Content
  columns?: ColumnConfig[]
  rows?: RowConfig[]
  charts?: ChartConfig[]

  // Highlighting rules
  highlights?: HighlightRule[]
}

interface ColumnConfig {
  key: string
  header: string
  width?: number
  format?: 'text' | 'number' | 'date' | 'currency' | 'percentage'
  numberFormat?: string
  alignment?: 'left' | 'center' | 'right'
}

interface HighlightRule {
  condition: (row: any) => boolean
  style: {
    bgColor?: string
    fontColor?: string
    bold?: boolean
    italic?: boolean
  }
}

interface ChartConfig {
  type: 'bar' | 'line' | 'pie' | 'scatter' | 'heatmap'
  title: string
  dataSource: {
    xAxis: string
    yAxis: string
    groupBy?: string
  }
  position: {
    row: number
    column: number
    height: number
    width: number
  }
  style: {
    colors?: string[]
    showLegend: boolean
    showDataLabels: boolean
  }
}
```

### Export Engine

```typescript
class ExportEngine {
  /**
   * Export analysis result to Excel
   */
  async exportToExcel(
    result: AnalysisResult,
    template: ExportTemplate,
    outputPath: string
  ): Promise<void> {

    // Create workbook
    const workbook = new ExcelJS.Workbook()

    // Add metadata
    this.addMetadata(workbook, template, result)

    // Create sheets
    for (const sheetConfig of template.sheets) {
      const sheet = workbook.addWorksheet(sheetConfig.name)

      // Add content based on sheet type
      switch (sheetConfig.type) {
        case 'data':
          await this.addDataTable(sheet, result, sheetConfig)
          break
        case 'summary':
          await this.addSummarySheet(sheet, result, sheetConfig)
          break
        case 'chart':
          await this.addChartSheet(sheet, result, sheetConfig)
          break
      }

      // Apply formatting
      this.applySheetFormatting(sheet, sheetConfig)
    }

    // Save workbook
    await workbook.xlsx.writeFile(outputPath)
  }

  /**
   * Add data table to sheet
   */
  private async addDataTable(
    sheet: ExcelJS.Worksheet,
    result: AnalysisResult,
    config: SheetConfig
  ): Promise<void> {
    // Add header row
    const headers = config.columns!.map(col => col.header)
    sheet.addRow(headers)

    // Style header
    const headerRow = sheet.getRow(1)
    headerRow.font = { bold: true, color: { argb: 'FFFFFFFF' } }
    headerRow.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF4472C4' } }

    // Add data rows
    const data = this.extractData(result, config.dataSource)
    for (const row of data) {
      sheet.addRow(config.columns!.map(col => row[col.key]))
    }

    // Apply highlights
    if (config.highlights) {
      this.applyHighlights(sheet, data, config.highlights)
    }

    // Auto-fit columns
    if (config.layout.autoFitColumns) {
      sheet.columns.forEach((column, index) => {
        const maxLength = column.values.reduce(
          (max, value) => Math.max(max, String(value).length),
          0
        )
        column.width = maxLength + 2
      })
    }

    // Freeze header
    if (config.layout.freezeHeader) {
      sheet.views = [{ state: 'frozen', ySplit: 1 }]
    }

    // Auto filter
    if (config.layout.autoFilter) {
      sheet.autoFilter = {
        from: { row: 1, column: 1 },
        to: { row: sheet.rowCount, column: headers.length }
      }
    }
  }

  /**
   * Add metadata to workbook
   */
  private addMetadata(
    workbook: ExcelJS.Workbook,
    template: ExportTemplate,
    result: AnalysisResult
  ): void {
    workbook.creator = template.formatting.author || 'Wareflow SaaS'
    workbook.created = new Date()

    if (template.formatting.title) {
      workbook.properties.title = template.formatting.title
    }
  }

  /**
   * Apply highlights to rows
   */
  private applyHighlights(
    sheet: ExcelJS.Worksheet,
    data: any[],
    rules: HighlightRule[]
  ): void {
    data.forEach((row, rowIndex) => {
      const rowNumber = rowIndex + 2 // +2 for header and 0-index

      for (const rule of rules) {
        if (rule.condition(row)) {
          const sheetRow = sheet.getRow(rowNumber)

          if (rule.style.bgColor) {
            sheetRow.fill = {
              type: 'pattern',
              pattern: 'solid',
              fgColor: { argb: rule.style.bgColor }
            }
          }

          if (rule.style.fontColor) {
            sheetRow.font = { color: { argb: rule.style.fontColor } }
          }

          if (rule.style.bold) {
            sheetRow.font = { ...sheetRow.font, bold: true }
          }
        }
      }
    })
  }
}
```

## File Format Support

### Import Formats

| Format | Extension | Status | Notes |
|--------|-----------|--------|-------|
| Excel | .xlsx, .xls | ✅ Supported | Primary format |
| CSV | .csv | 🔄 Planned | With delimiter detection |
| JSON | .json | 🔄 Planned | For API imports |
| XML | .xml | ❌ Not planned | Too complex for warehouse data |

### Export Formats

| Format | Extension | Status | Notes |
|--------|-----------|--------|-------|
| Excel | .xlsx | ✅ Supported | With formatting |
| CSV | .csv | 🔄 Planned | Plain data export |
| PDF | .pdf | ❌ Not planned | Use Excel export + PDF converter |

## Batch Operations

### Batch Import

```typescript
interface BatchImportOptions {
  files: File[]
  template?: DataTemplate
  continueOnError: boolean
  onProgress?: (progress: BatchImportProgress) => void
}

interface BatchImportProgress {
  totalFiles: number
  completedFiles: number
  failedFiles: number
  currentFile: string
  overallProgress: number  // 0-100
}
```

### Batch Export

```typescript
interface BatchExportOptions {
  results: AnalysisResult[]
  template: ExportTemplate
  outputDirectory: string
  namingPattern: string  // e.g., "{analysis_id}_{timestamp}.xlsx"
  onProgress?: (progress: BatchExportProgress) => void
}

interface BatchExportProgress {
  totalExports: number
  completedExports: number
  currentExport: string
  overallProgress: number  // 0-100
}
```

---

**Version**: 1.0.0
**Last Updated**: 2025-01-26
**Status**: Draft
