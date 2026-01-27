# Data Models and Import System

## Data Model Philosophy

The data model follows these principles:
1. **Normalize on Import**: Transform raw data into clean, normalized schema
2. **Preserve Raw Data**: Keep original data accessible for debugging
3. **Flexible Schema**: Support multiple warehouse data formats
4. **Version Controlled**: Track schema changes over time

## Core Data Entities

### Entity Relationship Diagram

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   produits   │────────<│  mouvements  │>────────│   usagers    │
│              │  (1:N)  │              │  (N:1)  │              │
└──────────────┘         └──────────────┘         └──────────────┘
       │                       │
       │                       │
       v                       v
┌──────────────┐         ┌──────────────┐
│  categories  │         │  commandes   │
└──────────────┘         └──────────────┘
                                │
                                v
                         ┌──────────────┐
                         │  receptions  │
                         └──────────────┘
```

### Core Tables

#### 1. Products (produits)

```sql
CREATE TABLE produits (
  -- Primary key
  no_produit INTEGER PRIMARY KEY,

  -- Basic information
  nom_produit TEXT NOT NULL,
  description TEXT,

  -- Categorization (3 levels)
  classe_produit TEXT,
  categorie_1 TEXT,
  categorie_2 TEXT,
  categorie_3 TEXT,

  -- Status and configuration
  etat TEXT,  -- Active, Inactive, Discontinued
  configuration TEXT,

  -- Identifiers
  ean_alternatif TEXT,

  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  -- Indexes
  INDEX idx_produits_nom (nom_produit),
  INDEX idx_produits_categorie1 (categorie_1),
  INDEX idx_produits_etat (etat),
  INDEX idx_produits_ean (ean_alternatif)
);
```

**Usage**:
- Master product catalog
- Reference for all movements
- Basis for inventory analysis

#### 2. Movements (mouvements)

```sql
CREATE TABLE mouvements (
  -- Primary key
  oid INTEGER PRIMARY KEY,

  -- Product reference
  no_produit INTEGER NOT NULL,
  nom_produit TEXT NOT NULL,

  -- Movement type
  type TEXT NOT NULL,  -- SORTIE, ENTREE, TRANSFERT

  -- Source location (for outbound/transfer)
  site_source TEXT,
  zone_source TEXT,
  localisation_source TEXT,
  conteneur_source TEXT,

  -- Target location (for inbound/transfer)
  site_cible TEXT,
  zone_cible TEXT,
  localisation_cible TEXT,
  conteneur_cible TEXT,

  -- Quantity
  quantite_uoi TEXT,  -- Unit of issue
  quantite INTEGER NOT NULL,
  unite TEXT,

  -- Timestamp
  date_heure DATETIME NOT NULL,
  date_heure_2 TEXT,  -- Alternative format

  -- User and reason
  usager TEXT,
  raison REAL,
  lot_expiration REAL,
  date_expiration REAL,

  -- Foreign keys
  FOREIGN KEY (no_produit) REFERENCES produits(no_produit),

  -- Indexes
  INDEX idx_mouvements_produit (no_produit),
  INDEX idx_mouvements_date (date_heure),
  INDEX idx_mouvements_type (type),
  INDEX idx_mouvements_usager (usager)
);
```

**Usage**:
- Core operational data
- Basis for ABC analysis
- Source for flux analysis

#### 3. Orders (commandes)

```sql
CREATE TABLE commandes (
  -- Primary key
  commande TEXT PRIMARY KEY,

  -- Order type
  type_commande TEXT,

  -- Parties involved
  demandeur TEXT,
  destinataire TEXT,
  no_destinataire INTEGER,

  -- Priority and scheduling
  priorite INTEGER,
  vague TEXT,
  date_requise DATETIME,

  -- Order details
  lignes INTEGER,  -- Number of lines
  chargement TEXT,
  transporteur TEXT,

  -- Status tracking
  etat_inferieur TEXT,
  etat_superieur TEXT,
  etat TEXT,
  statut_prepositionnement_max TEXT,
  statut_prepositionnement_actuel TEXT,

  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Usage**:
- Order fulfillment analysis
- Demandeur performance
- Lead time analysis

#### 4. Receptions (receptions)

```sql
CREATE TABLE receptions (
  -- Primary key
  no_reference INTEGER PRIMARY KEY,

  -- Reception reference
  reception INTEGER,

  -- Quantity and product
  quantite_recue INTEGER NOT NULL,
  produit INTEGER NOT NULL,

  -- Supplier information
  fournisseur TEXT,

  -- Location
  site TEXT,
  localisation_reception TEXT,

  -- Timing
  date_reception DATETIME NOT NULL,

  -- User and status
  utilisateur TEXT,
  etat TEXT,

  -- Lot tracking
  numero_lot REAL,
  date_expiration REAL,

  -- Foreign keys
  FOREIGN KEY (produit) REFERENCES produits(no_produit),

  -- Indexes
  INDEX idx_receptions_produit (produit),
  INDEX idx_receptions_fournisseur (fournisseur),
  INDEX idx_receptions_date (date_reception)
);
```

**Usage**:
- Supplier performance
- Lot/expiration tracking
- Receipt analysis

#### 5. Users (usagers) - Virtual Table

Users are typically extracted from movement data rather than stored separately:

```typescript
// Virtual user table
interface UserStats {
  usager: string
  total_movements: number
  first_movement: Date
  last_movement: Date
  avg_movements_per_day: number
}
```

## Import System Architecture

### Import Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  1. FILE UPLOAD                                              │
│     - Drag & drop Excel file                                 │
│     - File validation (size, format)                         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  2. PARSE & DETECT                                           │
│     - Parse Excel sheets                                     │
│     - Detect columns (fuzzy matching)                        │
│     - Detect data types                                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  3. TEMPLATE MATCHING                                        │
│     - Match against known templates                          │
│     - Calculate confidence scores                            │
│     - Suggest best template                                  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  4. MAPPING UI                                               │
│     - Show detected mapping                                  │
│     - Allow user adjustments                                 │
│     - Preview data transformation                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  5. VALIDATION                                               │
│     - Check required columns                                 │
│     - Validate data types                                    │
│     - Check referential integrity                            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  6. DATA LOAD                                                │
│     - Batch insert to database                               │
│     - Update indexes                                         │
│     - Create data version                                    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  7. POST-IMPORT                                              │
│     - Update available analyses                              │
│     - Generate statistics                                   │
│     - Create baseline metrics                               │
└─────────────────────────────────────────────────────────────┘
```

### Column Detection and Mapping

```typescript
// Column detection with fuzzy matching
interface ColumnMapping {
  sourceColumn: string      // Original column name from Excel
  targetColumn: string      // Normalized column name in schema
  confidence: number        // 0-1 score
  transformation?: string   // Optional transformation
}

// Detection algorithm
class ColumnDetector {
  detectColumns(
    headers: string[],
    schema: TableSchema
  ): ColumnMapping[] {
    return headers.map(header => {
      const match = this.findBestMatch(header, schema.columns)
      return {
        sourceColumn: header,
        targetColumn: match.column,
        confidence: match.score,
        transformation: this.suggestTransformation(header, match.column)
      }
    })
  }

  private findBestMatch(header: string, columns: string[]): ColumnMatch {
    // Fuzzy matching using Levenshtein distance
    // + synonym detection
    // + pattern matching
  }
}
```

### Data Validation Rules

```typescript
// Validation rule structure
interface ValidationRule {
  id: string
  name: string
  severity: 'error' | 'warning' | 'info'

  // Rule definition
  check: (data: any[]) => ValidationResult[]

  // Error message
  message: string
  suggestion?: string
}

// Common validation rules
const validationRules = {
  // Primary key uniqueness
  uniquePrimaryKeys: {
    id: 'unique-pk',
    name: 'Unique Primary Keys',
    severity: 'error',
    check: (data, primaryKey) => {
      const duplicates = findDuplicates(data, primaryKey)
      return duplicates.map(d => ({
        row: d.row,
        message: `Duplicate primary key: ${d[primaryKey]}`,
        suggestion: 'Remove or renumber duplicate rows'
      }))
    }
  },

  // Required columns
  requiredColumns: {
    id: 'required-columns',
    name: 'Required Columns Present',
    severity: 'error',
    check: (data, requiredCols) => {
      const missing = requiredCols.filter(col => !(col in data[0]))
      return missing.map(col => ({
        message: `Required column missing: ${col}`,
        suggestion: 'Add column to Excel file'
      }))
    }
  },

  // Data types
  dataTypes: {
    id: 'data-types',
    name: 'Valid Data Types',
    severity: 'error',
    check: (data, schema) => {
      // Check each column matches expected type
    }
  },

  // Referential integrity
  foreignKeys: {
    id: 'foreign-keys',
    name: 'Valid Foreign Keys',
    severity: 'error',
    check: (data, fkTable, fkColumn) => {
      // Check all FK values exist in referenced table
    }
  },

  // Date ranges
  dateRanges: {
    id: 'date-ranges',
    name: 'Reasonable Date Ranges',
    severity: 'warning',
    check: (data, dateColumn) => {
      const futureDates = data.filter(row =>
        row[dateColumn] > new Date()
      )
      return futureDates.map(d => ({
        row: d._row,
        message: `Future date detected: ${d[dateColumn]}`,
        suggestion: 'Verify date is correct'
      }))
    }
  },

  // Business rules
  businessRules: {
    id: 'business-rules',
    name: 'Business Rule Validation',
    severity: 'warning',
    check: (data) => {
      // Example: movements with quantity <= 0
      const invalidQty = data.filter(row => row.quantite <= 0)
      return invalidQty.map(d => ({
        row: d._row,
        message: `Invalid quantity: ${d.quantite}`,
        suggestion: 'Quantity must be greater than 0'
      }))
    }
  }
}
```

### Template Matching

```typescript
// Template matching algorithm
class TemplateMatcher {
  match(data: DetectedData, templates: DataTemplate[]): TemplateMatch[] {
    return templates.map(template => {
      const score = this.calculateMatchScore(data, template)
      return {
        template,
        score,
        missingTables: this.findMissingTables(data, template),
        missingColumns: this.findMissingColumns(data, template)
      }
    }).sort((a, b) => b.score - a.score)
  }

  private calculateMatchScore(data: DetectedData, template: DataTemplate): number {
    let score = 0
    let maxScore = 0

    // Check tables
    for (const [tableName, tableSchema] of Object.entries(template.schema.tables)) {
      maxScore += 10

      if (tableName in data.tables) {
        score += 5 // Table present

        const table = data.tables[tableName]
        for (const column of tableSchema.columns) {
          maxScore += 1
          if (column.name in table.columns) {
            score += 1 // Column present
          }
        }
      }
    }

    return score / maxScore
  }
}
```

## Data Transformations

### Normalization

```typescript
// Data normalization pipeline
class DataNormalizer {
  normalize(rawData: any[], schema: TableSchema): any[] {
    return rawData.map(row => this.normalizeRow(row, schema))
  }

  private normalizeRow(row: any, schema: TableSchema): any {
    const normalized: any = {}

    for (const column of schema.columns) {
      const value = row[column.name]

      normalized[column.name] = this.normalizeValue(value, column.type)
    }

    return normalized
  }

  private normalizeValue(value: any, type: string): any {
    switch (type) {
      case 'integer':
        return this.toInteger(value)
      case 'float':
        return this.toFloat(value)
      case 'date':
        return this.toDate(value)
      case 'text':
        return this.toText(value)
      default:
        return value
    }
  }
}
```

### Type Conversion

```typescript
// Type conversion utilities
class TypeConverter {
  static toInteger(value: any): number | null {
    if (value === null || value === undefined || value === '') {
      return null
    }

    const num = typeof value === 'number'
      ? value
      : parseFloat(String(value).replace(/[^0-9.-]/g, ''))

    return isNaN(num) ? null : Math.floor(num)
  }

  static toDate(value: any): Date | null {
    if (value === null || value === undefined || value === '') {
      return null
    }

    if (value instanceof Date) {
      return isNaN(value.getTime()) ? null : value
    }

    // Try Excel date format
    if (typeof value === 'number') {
      return excelDateToJSDate(value)
    }

    // Try string parsing
    const parsed = new Date(value)
    return isNaN(parsed.getTime()) ? null : parsed
  }

  static toText(value: any): string | null {
    if (value === null || value === undefined) {
      return null
    }

    const text = String(value).trim()
    return text === '' ? null : text
  }
}
```

## Data Quality Monitoring

```typescript
// Data quality metrics
interface DataQualityMetrics {
  completeness: {
    totalRows: number
    completeRows: number
    completenessRatio: number
  }

  accuracy: {
    invalidValues: number
    accuracyRatio: number
  }

  consistency: {
    duplicateRecords: number
    referentialIntegrityViolations: number
  }

  timeliness: {
    oldestDate: Date | null
    newestDate: Date | null
    dataAge: number // days
  }
}

// Quality calculator
class DataQualityCalculator {
  calculate(data: any[], schema: TableSchema): DataQualityMetrics {
    return {
      completeness: this.calculateCompleteness(data, schema),
      accuracy: this.calculateAccuracy(data, schema),
      consistency: this.calculateConsistency(data, schema),
      timeliness: this.calculateTimeliness(data, schema)
    }
  }
}
```

## Import Error Handling

```typescript
// Structured import errors
interface ImportError {
  type: 'file' | 'sheet' | 'column' | 'row' | 'value'
  severity: 'error' | 'warning'

  // Location
  sheet?: string
  row?: number
  column?: string

  // Error details
  code: string
  message: string
  suggestion?: string

  // Recovery options
  canContinue: boolean
  recoveryAction?: () => Promise<void>
}

// Import result
interface ImportResult {
  success: boolean
  rowsProcessed: number
  rowsInserted: number
  rowsFailed: number

  errors: ImportError[]
  warnings: ImportError[]

  dataQuality: DataQualityMetrics
}
```

---

**Version**: 1.0.0
**Last Updated**: 2025-01-26
**Status**: Draft
