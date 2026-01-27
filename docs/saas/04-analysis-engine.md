# Analysis Engine Architecture

## Overview

The Analysis Engine is a **pure TypeScript framework** for executing warehouse analyses. It is designed to be:
- **Extensible**: Add new analyses without recompilation
- **Type-safe**: Full TypeScript type checking
- **Performant**: Optimized for large datasets
- **Testable**: Pure functions and dependency injection

## Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Analysis Engine                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Registry   │  │   Executor   │  │   Validator  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Data Access  │  │  Transform   │  │   Result     │     │
│  │   Layer      │  │   Builder    │  │  Formatter   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Analysis Plugins                        │
├─────────────────────────────────────────────────────────────┤
│  Flux  │  Persons  │  Products  │  Custom (User-defined)   │
└─────────────────────────────────────────────────────────────┘
```

## Core Interfaces

### Analysis Engine

```typescript
interface AnalysisEngine {
  /**
   * Register a new analysis
   */
  register(analysis: AnalysisDefinition): void

  /**
   * Unregister an analysis
   */
  unregister(analysisId: string): void

  /**
   * Execute an analysis
   */
  execute(
    analysisId: string,
    context: AnalysisContext
  ): Promise<AnalysisResult>

  /**
   * Check if an analysis can execute
   */
  canExecute(analysisId: string, data: DataSet): boolean

  /**
   * List all available analyses
   */
  listAvailable(data: DataSet): AnalysisDefinition[]

  /**
   * List analyses by category
   */
  listByCategory(category: AnalysisCategory, data: DataSet): AnalysisDefinition[]

  /**
   * Get analysis metadata
   */
  getMetadata(analysisId: string): AnalysisDefinition | undefined
}
```

### Analysis Definition

```typescript
interface AnalysisDefinition {
  // Identification
  id: string
  name: string
  description: string
  version: string

  // Categorization
  category: AnalysisCategory
  tags: string[]

  // Data requirements
  requirements: {
    tables: string[]
    columns: Record<string, string[]>  // table -> columns
    minRows?: number
    maxRows?: number
    dateRange?: {
      column: string
      minDays?: number
      maxDays?: number
    }
  }

  // Configuration schema
  configSchema: z.ZodType<any>

  // Execution
  execute: (context: AnalysisContext) => Promise<AnalysisResult>

  // Output
  outputTemplate: ExportTemplate

  // UI hints
  ui: {
    icon: string
    color: string
    defaultConfig?: any
    estimatedDuration?: (rows: number) => number
  }

  // Metadata
  author?: string
  createdAt: Date
  updatedAt: Date
}

type AnalysisCategory =
  | 'flux'        // Movement/flow analysis
  | 'personnes'   // People/team analysis
  | 'produits'    // Product/inventory analysis
  | 'commandes'   // Order analysis
  | 'fournisseurs' // Supplier analysis
  | 'custom'      // User-defined analyses
```

### Analysis Context

```typescript
interface AnalysisContext {
  // Data source
  data: DataSet

  // Configuration
  config: any

  // Execution metadata
  metadata: {
    analysisId: string
    executedAt: Date
    userId?: string
  }

  // Services
  services: {
    query: QueryBuilder
    transform: TransformBuilder
    export: ExportService
    logger: Logger
  }

  // Progress callback
  onProgress?: (progress: number, message: string) => void
}
```

### Data Set

```typescript
interface DataSet {
  // Tables available
  tables: {
    [tableName: string]: DataTable
  }

  // Schema information
  schema: DataSchema

  // Metadata
  metadata: {
    importedAt: Date
    sourceTemplate: string
    totalRows: number
  }

  // Query builder
  query: QueryBuilder
}

interface DataTable {
  name: string
  columns: Column[]
  rowCount: number

  // Query interface
  findMany(options?: FindManyOptions): Promise<any[]>
  findOne(options: FindOneOptions): Promise<any | null>
  count(where?: WhereClause): Promise<number>
  aggregate(aggregations: Aggregation[]): Promise<any[]>
}

interface Column {
  name: string
  type: 'integer' | 'float' | 'text' | 'date' | 'boolean'
  nullable: boolean
  primaryKey?: boolean
  foreignKey?: {
    table: string
    column: string
  }
}
```

### Analysis Result

```typescript
interface AnalysisResult<T = any> {
  // Result metadata
  metadata: {
    analysisId: string
    analysisName: string
    executedAt: Date
    executionTime: number  // milliseconds
    dataVersion: string
  }

  // Result data
  data: T

  // Statistics
  stats: {
    rowsAnalyzed: number
    tablesUsed: string[]
    filtersApplied?: Filter[]
  }

  // Visualization hints
  visualization?: {
    type: 'table' | 'chart' | 'heatmap' | 'distribution'
    config: any
  }

  // Export template
  exportTemplate: ExportTemplate

  // Quality indicators
  quality?: {
    completeness: number
    confidence: number
    warnings?: string[]
  }
}
```

## Implementation Structure

```
src/analysis/
├── core/
│   ├── engine.ts              # Main AnalysisEngine class
│   ├── registry.ts            # AnalysisRegistry
│   ├── executor.ts            # AnalysisExecutor
│   ├── validator.ts           # RequirementsValidator
│   └── context.ts             # AnalysisContext builder
│
├── data/
│   ├── dataset.ts             # DataSet interface
│   ├── query-builder.ts       # QueryBuilder
│   ├── transform-builder.ts   # TransformBuilder
│   └── aggregations.ts        # Common aggregations
│
├── results/
│   ├── result.ts              # AnalysisResult types
│   ├── formatter.ts           # Result formatting
│   └── exporter.ts            # Export integration
│
├── analyses/
│   ├── flux/
│   │   ├── temporal.ts
│   │   ├── spatial.ts
│   │   └── operational.ts
│   ├── personnes/
│   │   ├── productivity.ts
│   │   ├── teams.ts
│   │   └── performance.ts
│   ├── produits/
│   │   ├── abc.ts
│   │   ├── lifecycle.ts
│   │   └── stock.ts
│   └── commandes/
│       ├── fulfillment.ts
│       └── lead-time.ts
│
├── plugins/
│   ├── loader.ts              # Dynamic plugin loading
│   ├── api.ts                 # Plugin API surface
│   └── registry.ts            # Plugin registry
│
├── types/
│   ├── analysis.ts
│   ├── data.ts
│   └── result.ts
│
└── utils/
    ├── validation.ts
    ├── transformations.ts
    └── statistics.ts
```

## Example Analysis Implementation

### ABC Analysis

```typescript
// analyses/produits/abc.ts
import { z } from 'zod'

export const abcAnalysis: AnalysisDefinition = {
  id: 'abc-classification',
  name: 'ABC Classification',
  description: 'Classify products by movement value using Pareto principle',
  version: '1.0.0',
  category: 'produits',
  tags: ['pareto', 'inventory', 'classification'],

  requirements: {
    tables: ['produits', 'mouvements'],
    columns: {
      produits: ['no_produit', 'nom_produit'],
      mouvements: ['no_produit', 'type', 'quantite', 'date_heure']
    },
    minRows: 1,
    dateRange: {
      column: 'date_heure',
      minDays: 1
    }
  },

  configSchema: z.object({
    lookbackDays: z.number().min(1).max(365).default(90),
    classBoundaries: z.tuple([
      z.number().min(1).max(100),
      z.number().min(1).max(100)
    ]).default([20, 50]),  // A: 0-20%, B: 20-50%, C: 50-100%
    includeInactive: z.boolean().default(false)
  }),

  ui: {
    icon: '📊',
    color: '#3b82f6',
    defaultConfig: {
      lookbackDays: 90,
      classBoundaries: [20, 50],
      includeInactive: false
    },
    estimatedDuration: (rows) => rows * 0.001  // ~1ms per row
  },

  execute: async (context) => {
    const { data, config, services } = context
    const { lookbackDays, classBoundaries } = config

    // Build query
    const query = services.query
      .from('mouvements')
      .join('produits', 'no_produit')
      .where('date_heure', '>=', daysAgo(lookbackDays))
      .where('type', '=', 'SORTIE')

    // Execute query
    const movements = await query.findMany()

    // Group by product and sum quantities
    const productMovements = services.transform
      .groupBy(movements, 'no_produit')
      .aggregate({
        totalPicked: sum('quantite'),
        movementCount: count(),
        lastMovement: max('date_heure')
      })
      .sort('totalPicked', 'desc')

    // Calculate percentiles
    const totalPicked = productMovements.reduce((sum, p) => sum + p.totalPicked, 0)
    let cumulativePct = 0

    const classified = productMovements.map((product, index) => {
      const pct = (product.totalPicked / totalPicked) * 100
      cumulativePct += pct

      let abcClass: 'A' | 'B' | 'C'
      if (cumulativePct <= classBoundaries[0]) {
        abcClass = 'A'
      } else if (cumulativePct <= classBoundaries[1]) {
        abcClass = 'B'
      } else {
        abcClass = 'C'
      }

      return {
        ...product,
        abcClass,
        percentage: pct,
        cumulativePercentage: cumulativePct
      }
    })

    // Calculate summary statistics
    const summary = {
      A: calculateClassStats(classified, 'A'),
      B: calculateClassStats(classified, 'B'),
      C: calculateClassStats(classified, 'C')
    }

    return {
      metadata: {
        analysisId: 'abc-classification',
        analysisName: 'ABC Classification',
        executedAt: new Date(),
        executionTime: performance.now(),
        dataVersion: data.metadata.sourceTemplate
      },
      data: {
        classification: classified,
        summary,
        totalProducts: classified.length,
        totalPicked,
        lookbackPeriod: lookbackDays
      },
      stats: {
        rowsAnalyzed: movements.length,
        tablesUsed: ['produits', 'mouvements']
      },
      visualization: {
        type: 'chart',
        config: {
          chartType: 'bar',
          xAxis: 'abcClass',
          yAxis: 'totalPicked',
          groupBy: 'abcClass',
          colors: { A: '#22c55e', B: '#f59e0b', C: '#ef4444' }
        }
      },
      exportTemplate: abcExportTemplate,
      quality: {
        completeness: 1.0,
        confidence: 0.95
      }
    }
  }
}

// Helper functions
function calculateClassStats(products: any[], className: 'A' | 'B' | 'C') {
  const classProducts = products.filter(p => p.abcClass === className)
  const totalPicked = classProducts.reduce((sum, p) => sum + p.totalPicked, 0)

  return {
    count: classProducts.length,
    picked: totalPicked,
    percentage: (totalPicked / products.reduce((sum, p) => sum + p.totalPicked, 0)) * 100
  }
}
```

## Query Builder

```typescript
// Type-safe query builder
class QueryBuilder {
  private query: QueryConfig = {}

  from(table: string): this {
    this.query.table = table
    return this
  }

  join(table: string, on: string): this {
    this.query.joins = this.query.joins || []
    this.query.joins.push({ table, on, type: 'INNER' })
    return this
  }

  where(column: string, operator: string, value: any): this {
    this.query.where = this.query.where || []
    this.query.where.push({ column, operator, value })
    return this
  }

  groupBy(...columns: string[]): this {
    this.query.groupBy = columns
    return this
  }

  orderBy(column: string, direction: 'asc' | 'desc' = 'asc'): this {
    this.query.orderBy = { column, direction }
    return this
  }

  limit(count: number): this {
    this.query.limit = count
    return this
  }

  async findMany(): Promise<any[]> {
    // Execute query via Prisma
  }

  async findOne(): Promise<any | null> {
    // Execute query and return first result
  }

  async count(): Promise<number> {
    // Execute count query
  }
}
```

## Transform Builder

```typescript
// Data transformation builder
class TransformBuilder {
  private transformations: Transformation[] = []

  static from(data: any[]): TransformBuilder {
    const builder = new TransformBuilder()
    builder.data = data
    return builder
  }

  groupBy(column: string): TransformBuilder {
    this.transformations.push({
      type: 'group',
      column
    })
    return this
  }

  aggregate(aggregations: Record<string, AggregationFn>): TransformBuilder {
    this.transformations.push({
      type: 'aggregate',
      aggregations
    })
    return this
  }

  sort(column: string, order: 'asc' | 'desc' = 'asc'): TransformBuilder {
    this.transformations.push({
      type: 'sort',
      column,
      order
    })
    return this
  }

  filter(predicate: (item: any) => boolean): TransformBuilder {
    this.transformations.push({
      type: 'filter',
      predicate
    })
    return this
  }

  map(fn: (item: any) => any): TransformBuilder {
    this.transformations.push({
      type: 'map',
      fn
    })
    return this
  }

  async exec(): Promise<any[]> {
    let result = this.data

    for (const transform of this.transformations) {
      result = await this.applyTransform(result, transform)
    }

    return result
  }

  private async applyTransform(data: any[], transform: Transformation): Promise<any[]> {
    switch (transform.type) {
      case 'group':
        return this.group(data, transform.column)
      case 'aggregate':
        return this.aggregateData(data, transform.aggregations)
      case 'sort':
        return this.sortData(data, transform.column, transform.order)
      case 'filter':
        return data.filter(transform.predicate)
      case 'map':
        return data.map(transform.fn)
      default:
        return data
    }
  }
}
```

## Plugin System

### Plugin API

```typescript
// Plugin interface
interface AnalysisPlugin {
  id: string
  name: string
  version: string

  // Analyses provided by this plugin
  analyses: AnalysisDefinition[]

  // Initialization
  init?(engine: AnalysisEngine): Promise<void>

  // Cleanup
  destroy?(): Promise<void>
}

// Plugin loader
class PluginLoader {
  private plugins: Map<string, AnalysisPlugin> = new Map()

  async loadPlugin(pluginPath: string): Promise<void> {
    const plugin: AnalysisPlugin = await import(pluginPath)

    // Validate plugin
    this.validatePlugin(plugin)

    // Register analyses
    for (const analysis of plugin.analyses) {
      engine.register(analysis)
    }

    // Initialize plugin
    if (plugin.init) {
      await plugin.init(engine)
    }

    this.plugins.set(plugin.id, plugin)
  }

  async unloadPlugin(pluginId: string): Promise<void> {
    const plugin = this.plugins.get(pluginId)
    if (!plugin) {
      throw new Error(`Plugin not found: ${pluginId}`)
    }

    // Cleanup
    if (plugin.destroy) {
      await plugin.destroy()
    }

    // Unregister analyses
    for (const analysis of plugin.analyses) {
      engine.unregister(analysis.id)
    }

    this.plugins.delete(pluginId)
  }

  private validatePlugin(plugin: AnalysisPlugin): void {
    // Validate plugin structure
    if (!plugin.id || !plugin.name || !plugin.analyses) {
      throw new Error('Invalid plugin structure')
    }
  }
}
```

### Custom Plugin Example

```typescript
// custom-analyses-plugin.ts
const customAnalysesPlugin: AnalysisPlugin = {
  id: 'my-custom-analyses',
  name: 'My Custom Analyses',
  version: '1.0.0',

  analyses: [
    {
      id: 'custom-movement-analysis',
      name: 'Custom Movement Analysis',
      category: 'custom',
      requirements: {
        tables: ['mouvements'],
        columns: { mouvements: ['no_produit', 'type', 'quantite', 'date_heure'] }
      },
      configSchema: z.object({
        threshold: z.number()
      }),
      execute: async (context) => {
        // Custom analysis logic
      },
      outputTemplate: customExportTemplate,
      ui: { icon: '🔧', color: '#8b5cf6' }
    }
  ]
}

export default customAnalysesPlugin
```

---

**Version**: 1.0.0
**Last Updated**: 2025-01-26
**Status**: Draft
