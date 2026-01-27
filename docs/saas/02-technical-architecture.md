# Technical Architecture

## System Architecture Overview

Wareflow SaaS follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  React UI Components  │  Data Tables  │  Visualizations  │  Forms │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│  State Management  │  Analysis Engine  │  Template Manager      │
│  Query Builder     │  Export Engine    │  Import Coordinator    │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                          DOMAIN LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  Analysis Definitions  │  Template Schemas  │  Validation Rules  │
│  Data Transformations  │  Export Templates  │  Domain Models     │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                       DATA ACCESS LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│  Prisma ORM  │  Query Builder  │  Repository Pattern  │  Cache  │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                        DATA STORAGE LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL/SQLite  │  File System  │  Index Store  │  Cache    │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Frontend Stack

```yaml
Framework: React 18.3+
Language: TypeScript 5.3+
Build Tool: Vite 5.0+

State Management:
  Library: Zustand 4.5+
  Server State: TanStack Query 5.0+

UI Components:
  Base: shadcn/ui (Radix UI primitives)
  Styling: Tailwind CSS 3.4+
  Icons: Lucide React

Data Visualization:
  Charts: Recharts 2.10+
  Scientific: Plotly.js (optional)
  Maps: Leaflet (if warehouse maps needed)

Data Tables:
  Library: TanStack Table 8.0+
  Features: Virtualization, sorting, filtering

File Processing:
  Excel: SheetJS (xlsx) or ExcelJS
  CSV: PapaParse
  Validation: Zod
```

### Backend Stack

```yaml
Runtime: Node.js 20 LTS
Framework: Fastify 4.0+
Language: TypeScript 5.3+

Database:
  Production: PostgreSQL 15+
  Development: SQLite 3.40+
  ORM: Prisma 5.0+

Job Queue:
  Library: BullMQ 5.0+
  Backend: Redis 7.0+

Caching:
  Session: Redis
  Query: Redis or in-memory

API:
  Protocol: REST (internal)
  Validation: Zod
  Documentation: OpenAPI 3.1
```

### Desktop Packaging

```yaml
Framework: Electron 28+
Packager: electron-builder
Updater: electron-updater

Build Targets:
  - Windows: NSIS installer + portable
  - macOS: DMG + PKG
  - Linux: AppImage + deb

Distribution:
  Channel: GitHub Releases (initially)
  Auto-update: Enabled by default
```

## Component Architecture

### 1. Data Import System

```
┌─────────────────────────────────────────────────────────┐
│                    Import Coordinator                    │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ File Parser  │→│ Column Mapper │→│ Data Validator│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    Template Engine                        │
├─────────────────────────────────────────────────────────┤
│  Schema Detection  │  Auto-mapping  │  Validation Rules │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    Database Loader                        │
├─────────────────────────────────────────────────────────┤
│  Batch Insert  │  Transaction Mgmt  │  Error Handling   │
└─────────────────────────────────────────────────────────┘
```

**Key Components**:
- `FileParser`: Reads Excel/CSV files
- `ColumnMapper`: Maps columns to schema using fuzzy matching
- `DataValidator`: Validates data against schema rules
- `TemplateEngine`: Detects template and enables analyses
- `DatabaseLoader`: Batch loads data with error recovery

### 2. Analysis Engine

```typescript
// Core analysis engine interface
interface AnalysisEngine {
  // Registry of all analyses
  registry: AnalysisRegistry

  // Execute an analysis
  execute(analysisId: string, context: AnalysisContext): Promise<AnalysisResult>

  // Check if analysis can run
  canExecute(analysisId: string, data: DataSet): boolean

  // List available analyses
  listAvailable(data: DataSet): AnalysisDefinition[]

  // Register new analysis (extensibility)
  register(analysis: AnalysisDefinition): void
}

// Analysis definition structure
interface AnalysisDefinition {
  id: string
  name: string
  description: string
  category: AnalysisCategory
  version: string

  // Data requirements
  requirements: {
    tables: string[]
    columns: Record<string, string[]>
    minRows?: number
  }

  // Configuration schema
  configSchema: z.ZodType

  // Execution function
  execute(context: AnalysisContext): Promise<AnalysisResult>

  // Output template
  outputTemplate: ExportTemplate
}
```

**Component Breakdown**:

```
src/analysis/
├── core/
│   ├── engine.ts              # Main orchestration
│   ├── registry.ts            # Analysis registration
│   ├── executor.ts            # Execution with dependency resolution
│   └── validator.ts           # Pre-condition validation
├── data/
│   ├── dataset.ts             # DataSet interface
│   ├── query-builder.ts       # Query construction
│   └── transformations.ts     # Common transformations
├── results/
│   ├── result.ts              # Result types
│   ├── exporter.ts            # Export formatting
│   └── visualizer.ts          # Visualization helpers
└── plugins/
    ├── loader.ts              # Dynamic plugin loading
    ├── api.ts                 # Plugin API surface
    └── registry.ts            # Plugin registry
```

### 3. Template System

```typescript
// Template definition
interface DataTemplate {
  id: string
  name: string
  description: string
  version: string

  // Schema definition
  schema: {
    tables: Record<string, TableSchema>
    relationships?: RelationshipSchema[]
  }

  // Default column mappings
  defaultMappings: ColumnMapping[]

  // Enabled analyses
  enabledAnalyses: string[]

  // Validation rules
  validationRules: ValidationRule[]

  // Export templates
  exportTemplates: ExportTemplate[]
}

// Template resolution flow
Template Resolution:
1. User uploads file
2. Detect columns and data types
3. Match against available templates
4. Present best match with confidence score
5. User confirms or adjusts mapping
6. Lock template and enable analyses
```

### 4. Export Engine

```typescript
// Export engine interface
interface ExportEngine {
  // Export to Excel
  exportToExcel(
    data: AnalysisResult,
    template: ExportTemplate,
    options: ExportOptions
  ): Promise<Buffer>

  // Export to other formats
  export(data: AnalysisResult, format: ExportFormat): Promise<Buffer>
}

// Export template structure
interface ExportTemplate {
  id: string
  name: string
  format: 'excel' | 'csv' | 'pdf'

  // Sheets/tabs configuration
  sheets: SheetConfig[]

  // Formatting
  formatting: {
    header: HeaderStyle
    rows: RowStyle
    highlights: HighlightRule[]
  }

  // Metadata
  metadata: {
    title?: string
    author?: string
    logo?: string
    generatedAt?: boolean
  }
}
```

## Data Flow

### Import Flow

```
User uploads Excel
    ↓
FileParser reads file
    ↓
ColumnDetector identifies columns
    ↓
TemplateMatcher suggests template
    ↓
User reviews/adjusts mapping
    ↓
DataValidator validates
    ↓
DatabaseLoader inserts data
    ↓
AnalysisEngine updates available analyses
    ↓
UI updates dashboard
```

### Analysis Flow

```
User selects analysis
    ↓
AnalysisEngine.checkRequirements()
    ↓
Gather configuration from user
    ↓
AnalysisEngine.execute()
    ↓
Query data from database
    ↓
Apply transformations
    ↓
Calculate results
    ↓
Format results
    ↓
Return to UI
```

### Export Flow

```
User clicks export
    ↓
Select export template
    ↓
Apply formatting
    ↓
Generate Excel file
    ↓
Download to user location
```

## Database Schema Strategy

### Schema Versioning

```sql
-- Schema version tracking
CREATE TABLE schema_migrations (
  version VARCHAR(14) PRIMARY KEY,
  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data versioning
CREATE TABLE data_versions (
  id SERIAL PRIMARY KEY,
  version VARCHAR(14),
  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  description TEXT
);

-- Template application tracking
CREATE TABLE applied_templates (
  id SERIAL PRIMARY KEY,
  template_id VARCHAR(255),
  applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  schema_version VARCHAR(14)
);
```

### Multi-Tenancy (Future)

```sql
-- Tenant isolation
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add tenant_id to all data tables
ALTER TABLE produits ADD COLUMN tenant_id UUID REFERENCES tenants(id);
CREATE INDEX idx_produits_tenant ON produits(tenant_id);
```

## Performance Considerations

### 1. Virtual Scrolling

```typescript
// For large datasets
import { useVirtualizer } from '@tanstack/react-virtual'

function DataTable({ rows }: { rows: Row[] }) {
  const parentRef = useRef<HTMLDivElement>(null)

  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
    overscan: 10
  })

  // Only render visible rows
}
```

### 2. Lazy Loading

```typescript
// Load analyses on-demand
const analyses = await import('./analyses/abc-analysis')
```

### 3. Background Processing

```typescript
// Long-running analyses in worker
const worker = new Worker('analysis-worker.js')
worker.postMessage({ analysisId, data })
worker.onmessage = (event) => {
  setResults(event.data)
}
```

### 4. Database Indexing

```sql
-- Critical indexes for performance
CREATE INDEX idx_mouvements_produit ON mouvements(no_produit);
CREATE INDEX idx_mouvements_date ON mouvements(date_heure);
CREATE INDEX idx_mouvements_type ON mouvements(type);
CREATE INDEX idx_mouvements_usager ON mouvements(usager);
CREATE INDEX idx_produits_categorie ON produits(categorie_1);
```

## Security Considerations

### 1. Input Validation

```typescript
// All user inputs validated with Zod
import { z } from 'zod'

const AnalysisConfigSchema = z.object({
  lookbackDays: z.number().min(1).max(365),
  category: z.enum(['A', 'B', 'C']),
  includeInactive: z.boolean().default(false)
})
```

### 2. SQL Injection Prevention

```typescript
// Always use parameterized queries via Prisma
const products = await prisma.produits.findMany({
  where: {
    no_produit: productId  // Automatically parameterized
  }
})
```

### 3. File Upload Security

```typescript
// Validate file uploads
const MAX_FILE_SIZE = 100 * 1024 * 1024 // 100MB
const ALLOWED_TYPES = [
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
]
```

## Error Handling Strategy

```typescript
// Structured error handling
class AnalysisError extends Error {
  constructor(
    public code: string,
    message: string,
    public suggestions: string[]
  ) {
    super(message)
  }
}

// Usage
try {
  await analysis.execute(context)
} catch (error) {
  if (error instanceof AnalysisError) {
    showErrorDialog({
      title: error.code,
      message: error.message,
      suggestions: error.suggestions
    })
  }
}
```

## Testing Strategy

```yaml
Unit Tests:
  Framework: Vitest
  Coverage: > 80%
  Focus: Business logic, transformations

Integration Tests:
  Framework: Vitest + Playwright
  Coverage: Critical paths
  Focus: Import → Analyze → Export

E2E Tests:
  Framework: Playwright
  Coverage: Key workflows
  Focus: User journeys

Performance Tests:
  Tool: k6
  Scenarios: Large dataset handling
```

---

**Version**: 1.0.0
**Last Updated**: 2025-01-26
**Status**: Draft
