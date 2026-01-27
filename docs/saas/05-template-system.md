# Template System

## Overview

The Template System is the **bridge between raw Excel data and available analyses**. It defines:
1. What data structure is expected
2. How columns should be mapped
3. Which analyses are automatically enabled
4. What validation rules apply

## Template Philosophy

```
Template = Schema + Mapping + Analyses + Validation
```

A template answers the question:
> "Given this type of warehouse data, what analyses can I run?"

## Template Structure

### Template Definition

```typescript
interface DataTemplate {
  // Identification
  id: string
  name: string
  description: string
  version: string
  category: TemplateCategory

  // Data schema
  schema: {
    tables: Record<string, TableSchema>
    relationships?: RelationshipSchema[]
  }

  // Default column mappings
  defaultMappings: ColumnMappingProfile[]

  // Enabled analyses
  enabledAnalyses: string[]

  // Validation rules
  validationRules: ValidationRule[]

  // Export templates
  exportTemplates: ExportTemplate[]

  // Metadata
  metadata: {
    author?: string
    createdAt: Date
    updatedAt: Date
    tags: string[]
    industries: string[]
  }
}

type TemplateCategory =
  | 'warehouse-basic'      // Single warehouse, basic operations
  | 'warehouse-advanced'   // Multi-warehouse, complex operations
  | 'distribution'         // Distribution center
  | 'retail'               // Retail back-of-house
  | 'manufacturing'        // Manufacturing warehouse
  | 'custom'               // User-defined
```

### Table Schema

```typescript
interface TableSchema {
  name: string
  description: string
  required: boolean

  // Column definitions
  columns: ColumnSchema[]

  // Primary key
  primaryKey: string

  // Foreign keys
  foreignKeys?: {
    column: string
    references: {
      table: string
      column: string
    }
  }[]

  // Constraints
  constraints?: {
    unique?: string[]       // Columns that must be unique
    minRows?: number        // Minimum required rows
    maxRows?: number        // Maximum allowed rows
  }
}

interface ColumnSchema {
  name: string
  type: 'integer' | 'float' | 'text' | 'date' | 'boolean'
  required: boolean
  nullable: boolean

  // Validation
  validation?: {
    min?: number
    max?: number
    pattern?: string
    enum?: string[]
  }

  // Aliases for fuzzy matching
  aliases?: string[]

  // Description
  description?: string
}
```

### Column Mapping Profile

```typescript
interface ColumnMappingProfile {
  // Source pattern (from Excel)
  sourcePattern: {
    // Exact match
    exact?: string[]

    // Fuzzy match (Levenshtein distance)
    fuzzy?: string[]

    // Pattern match (regex)
    pattern?: string

    // Synonyms
    synonyms?: string[]
  }

  // Target column (in schema)
  targetColumn: string

  // Transformation
  transformation?: {
    type: 'date' | 'number' | 'text' | 'custom'
    customFn?: string  // For custom transformations
  }

  // Confidence score (0-1)
  confidence: number
}
```

## Built-in Templates

### Template 1: Basic Warehouse

```typescript
const basicWarehouseTemplate: DataTemplate = {
  id: 'basic-warehouse',
  name: 'Basic Warehouse',
  description: 'Simple warehouse with products and movements',
  version: '1.0.0',
  category: 'warehouse-basic',

  schema: {
    tables: {
      produits: {
        name: 'produits',
        description: 'Product catalog',
        required: true,
        primaryKey: 'no_produit',
        columns: [
          {
            name: 'no_produit',
            type: 'integer',
            required: true,
            nullable: false,
            aliases: ['id', 'product_id', 'product_id', 'sku', 'ref']
          },
          {
            name: 'nom_produit',
            type: 'text',
            required: true,
            nullable: false,
            aliases: ['name', 'product_name', 'libelle', 'designation']
          },
          {
            name: 'description',
            type: 'text',
            required: false,
            nullable: true
          },
          {
            name: 'categorie_1',
            type: 'text',
            required: false,
            nullable: true,
            aliases: ['category', 'cat', 'category_1']
          },
          {
            name: 'etat',
            type: 'text',
            required: false,
            nullable: true,
            aliases: ['status', 'state', 'product_status'],
            validation: {
              enum: ['Active', 'Inactive', 'Discontinued']
            }
          }
        ]
      },
      mouvements: {
        name: 'mouvements',
        description: 'Stock movements',
        required: true,
        primaryKey: 'oid',
        foreignKeys: [
          {
            column: 'no_produit',
            references: { table: 'produits', column: 'no_produit' }
          }
        ],
        columns: [
          {
            name: 'oid',
            type: 'integer',
            required: true,
            nullable: false,
            aliases: ['id', 'movement_id']
          },
          {
            name: 'no_produit',
            type: 'integer',
            required: true,
            nullable: false,
            aliases: ['product_id', 'produit', 'sku']
          },
          {
            name: 'type',
            type: 'text',
            required: true,
            nullable: false,
            aliases: ['movement_type', 'transaction_type'],
            validation: {
              enum: ['SORTIE', 'ENTREE', 'TRANSFERT']
            }
          },
          {
            name: 'quantite',
            type: 'integer',
            required: true,
            nullable: false,
            aliases: ['quantity', 'qty', 'qte']
          },
          {
            name: 'date_heure',
            type: 'date',
            required: true,
            nullable: false,
            aliases: ['date', 'datetime', 'timestamp', 'movement_date']
          },
          {
            name: 'usager',
            type: 'text',
            required: false,
            nullable: true,
            aliases: ['user', 'operator', 'employee']
          }
        ]
      }
    }
  },

  defaultMappings: [
    // Products mappings
    {
      sourcePattern: {
        exact: ['no_produit', 'product_id'],
        fuzzy: ['produit', 'product', 'ref', 'sku'],
        synonyms: ['id produit', 'product no']
      },
      targetColumn: 'no_produit',
      confidence: 0.9
    },
    {
      sourcePattern: {
        exact: ['nom_produit', 'product_name'],
        fuzzy: ['name', 'libelle', 'designation'],
        synonyms: ['product', 'produit', 'libellé']
      },
      targetColumn: 'nom_produit',
      confidence: 0.85
    },
    // Movements mappings
    {
      sourcePattern: {
        exact: ['quantite', 'quantity'],
        fuzzy: ['qty', 'qte'],
        synonyms: ['quantité']
      },
      targetColumn: 'quantite',
      confidence: 0.95
    },
    {
      sourcePattern: {
        exact: ['date_heure', 'datetime'],
        fuzzy: ['date', 'timestamp'],
        synonyms: ['date et heure', 'movement date']
      },
      targetColumn: 'date_heure',
      confidence: 0.9
    }
  ],

  enabledAnalyses: [
    'abc-classification',
    'inventory-overview'
  ],

  validationRules: [
    {
      id: 'unique-product-ids',
      table: 'produits',
      column: 'no_produit',
      rule: 'unique',
      severity: 'error'
    },
    {
      id: 'positive-quantities',
      table: 'mouvements',
      column: 'quantite',
      rule: 'min',
      value: 0,
      severity: 'error'
    },
    {
      id: 'valid-dates',
      table: 'mouvements',
      column: 'date_heure',
      rule: 'dateNotFuture',
      severity: 'warning'
    }
  ],

  exportTemplates: [
    abcReportTemplate,
    inventoryReportTemplate
  ],

  metadata: {
    createdAt: new Date('2025-01-26'),
    tags: ['basic', 'simple', 'starter'],
    industries: ['retail', 'distribution', 'manufacturing']
  }
}
```

### Template 2: Full Analytics

```typescript
const fullAnalyticsTemplate: DataTemplate = {
  id: 'full-analytics',
  name: 'Full Analytics Warehouse',
  description: 'Complete warehouse with orders, receptions, and users',
  version: '1.0.0',
  category: 'warehouse-advanced',

  schema: {
    tables: {
      // ... all tables from basic warehouse ...
      commandes: { /* order table schema */ },
      receptions: { /* reception table schema */ },
      usagers: { /* users table schema */ }
    }
  },

  enabledAnalyses: [
    // Basic analyses
    'abc-classification',
    'inventory-overview',

    // Flux analyses
    'flux-temporal',
    'flux-spatial',
    'flux-operational',

    // Personnes analyses
    'personnes-productivity',
    'personnes-teams',
    'personnes-performance',

    // Product analyses
    'produits-lifecycle',
    'produits-stock',

    // Order analyses
    'commandes-fulfillment',
    'commandes-lead-time',

    // Supplier analyses
    'fournisseurs-performance'
  ],

  validationRules: [
    // ... all basic warehouse rules ...
    // Additional rules for advanced tables
  ],

  exportTemplates: [
    // All report templates
  ],

  metadata: {
    createdAt: new Date('2025-01-26'),
    tags: ['advanced', 'complete', 'full-featured'],
    industries: ['retail', 'distribution', 'manufacturing', 'logistics']
  }
}
```

## Template Matching Algorithm

### Matching Process

```typescript
class TemplateMatcher {
  /**
   * Find best matching template for uploaded data
   */
  findBestMatch(
    detectedData: DetectedData,
    availableTemplates: DataTemplate[]
  ): TemplateMatchResult {
    const matches = availableTemplates.map(template => ({
      template,
      score: this.calculateMatchScore(detectedData, template),
      missingTables: this.findMissingTables(detectedData, template),
      missingColumns: this.findMissingColumns(detectedData, template),
      confidence: this.calculateConfidence(detectedData, template)
    }))

    // Sort by score descending
    matches.sort((a, b) => b.score - a.score)

    return {
      bestMatch: matches[0],
      alternatives: matches.slice(1),
      confidence: matches[0].confidence
    }
  }

  /**
   * Calculate match score (0-100)
   */
  private calculateMatchScore(
    data: DetectedData,
    template: DataTemplate
  ): number {
    let score = 0
    let maxScore = 0

    // Check tables
    for (const [tableName, tableSchema] of Object.entries(template.schema.tables)) {
      maxScore += 10

      if (tableName in data.tables) {
        score += 5 // Table present

        const table = data.tables[tableName]

        // Check columns
        for (const column of tableSchema.columns) {
          maxScore += 1

          if (this.hasColumn(table, column)) {
            score += 1 // Column present
          }
        }
      }
    }

    return (score / maxScore) * 100
  }

  /**
   * Check if table has column (fuzzy matching)
   */
  private hasColumn(table: DetectedTable, column: ColumnSchema): boolean {
    // Exact match
    if (column.name in table.columns) {
      return true
    }

    // Check aliases
    if (column.aliases) {
      for (const alias of column.aliases) {
        if (alias in table.columns) {
          return true
        }
      }
    }

    // Fuzzy match
    for (const detectedCol of Object.keys(table.columns)) {
      if (this.fuzzyMatch(detectedCol, column.name)) {
        return true
      }
    }

    return false
  }

  /**
   * Fuzzy string matching
   */
  private fuzzyMatch(str1: string, str2: string): boolean {
    const distance = levenshteinDistance(
      str1.toLowerCase(),
      str2.toLowerCase()
    )

    // Allow max 2 edits for short strings, or 30% difference for long strings
    const maxEdits = Math.min(2, Math.max(str1.length, str2.length) * 0.3)

    return distance <= maxEdits
  }
}
```

### Template Matching Result

```typescript
interface TemplateMatchResult {
  bestMatch: TemplateMatch
  alternatives: TemplateMatch[]
  confidence: number  // 0-1
}

interface TemplateMatch {
  template: DataTemplate
  score: number  // 0-100
  missingTables: string[]
  missingColumns: Record<string, string[]>  // table -> columns
  confidence: number  // 0-1

  // Can data be imported with this template?
  canImport: boolean

  // Would some analyses be unavailable?
  unavailableAnalyses?: string[]
}
```

## Template-Based Analysis Unlocking

### Automatic Analysis Activation

```typescript
class AnalysisUnlocker {
  /**
   * Determine which analyses are available based on imported data
   */
  unlockAnalyses(
    data: DataSet,
    template: DataTemplate,
    allAnalyses: AnalysisDefinition[]
  ): AvailableAnalysis[] {
    return template.enabledAnalyses
      .map(analysisId => allAnalyses.find(a => a.id === analysisId))
      .filter(Boolean)
      .map(analysis => {
        const canExecute = this.checkRequirements(analysis!, data)

        return {
          analysis: analysis!,
          available: canExecute.success,
          reason: canExecute.reason,
          missingData: canExecute.missing
        }
      })
      .filter(result => result.available)
  }

  /**
   * Check if analysis requirements are met
   */
  private checkRequirements(
    analysis: AnalysisDefinition,
    data: DataSet
  ): { success: boolean; reason?: string; missing?: string[] } {
    const missing: string[] = []

    // Check tables
    for (const table of analysis.requirements.tables) {
      if (!(table in data.tables)) {
        missing.push(`Table: ${table}`)
      }
    }

    // Check columns
    for (const [table, columns] of Object.entries(analysis.requirements.columns)) {
      if (table in data.tables) {
        const tableData = data.tables[table]

        for (const column of columns) {
          if (!(column in tableData.columns)) {
            missing.push(`Column: ${table}.${column}`)
          }
        }
      } else {
        missing.push(`Table: ${table}`)
      }
    }

    if (missing.length > 0) {
      return {
        success: false,
        reason: 'Missing required data',
        missing
      }
    }

    // Check row count
    if (analysis.requirements.minRows) {
      const rows = Object.values(data.tables)
        .reduce((sum, table) => sum + table.rowCount, 0)

      if (rows < analysis.requirements.minRows) {
        return {
          success: false,
          reason: `Insufficient data (need ${analysis.requirements.minRows} rows)`
        }
      }
    }

    return { success: true }
  }
}
```

## Custom Templates

### Template Builder UI

```typescript
// Template builder for custom templates
interface TemplateBuilder {
  // Start new template
  create(): TemplateBuilder

  // Add table
  addTable(schema: TableSchema): TemplateBuilder

  // Add column mapping
  addMapping(mapping: ColumnMappingProfile): TemplateBuilder

  // Enable analysis
  enableAnalysis(analysisId: string): TemplateBuilder

  // Add validation rule
  addValidation(rule: ValidationRule): TemplateBuilder

  // Build template
  build(): DataTemplate
}

// Usage
const customTemplate = new TemplateBuilder()
  .create()
  .addTable(productsTableSchema)
  .addTable(movementsTableSchema)
  .addMapping({
    sourcePattern: { exact: ['ProductID'] },
    targetColumn: 'no_produit',
    confidence: 1.0
  })
  .enableAnalysis('abc-classification')
  .build()
```

### Template Sharing

```typescript
// Template marketplace (future)
interface TemplateMarketplace {
  // List available templates
  listTemplates(): Promise<DataTemplate[]>

  // Download template
  downloadTemplate(templateId: string): Promise<DataTemplate>

  // Upload custom template
  uploadTemplate(template: DataTemplate): Promise<void>

  // Rate template
  rateTemplate(templateId: string, rating: number): Promise<void>
}
```

## Template Versioning

### Version Management

```typescript
interface TemplateVersion {
  templateId: string
  version: string
  changelog: string
  createdAt: Date
  migrationRequired: boolean
  migrationScript?: string
}

class TemplateVersionManager {
  /**
   * Migrate data from old template version to new
   */
  async migrateData(
    data: DataSet,
    fromVersion: string,
    toVersion: string
  ): Promise<DataSet> {
    const migration = this.findMigration(fromVersion, toVersion)

    if (!migration) {
      throw new Error(`No migration path from ${fromVersion} to ${toVersion}`)
    }

    return migration.migrate(data)
  }
}
```

---

**Version**: 1.0.0
**Last Updated**: 2025-01-26
**Status**: Draft
