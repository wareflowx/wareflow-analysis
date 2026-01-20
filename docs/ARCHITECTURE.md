# Wareflow Analysis - Architecture Documentation

## Overview

This document outlines the strategic architecture for separating **data infrastructure** from **analysis layer**, enabling infinite extensibility of analyses without impacting data operations.

### Core Principle

**Complete isolation through contract-based design**:
- Each layer defines a stable contract (interface)
- Layers can evolve independently as long as contracts are respected
- Adding new analyses requires zero changes to existing code

---

## Architecture Layers

### Layer Separation

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: DATA INFRASTRUCTURE (Stable, Slow-changing)       │
│  - Import ETL                                               │
│  - Data transformation                                       │
│  - Database schema                                          │
│  - Data quality                                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ ⬇ SCHEMA CONTRACT ⬇
                         │
┌────────────────────────┴────────────────────────────────────┐
│  LAYER 2: DATA ACCESS LAYER (Stable API)                    │
│  - Standardized views                                       │
│  - Materialized views                                       │
│  - Stored procedures                                        │
│  - Data catalog                                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ ⬇ DATA CONTRACT ⬇
                         │
┌────────────────────────┴────────────────────────────────────┐
│  LAYER 3: ANALYSIS ENGINE (Extensible, Fast-changing)       │
│  - KPI calculations                                         │
│  - Statistical analysis                                     │
│  - Business logic                                           │
│  - Report templates                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ ⬇ RESULTS CONTRACT ⬇
                         │
┌────────────────────────┴────────────────────────────────────┐
│  LAYER 4: EXPORT LAYER (Pluggable)                          │
│  - Excel generators                                         │
│  - Report formatters                                        │
│  - Chart builders                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 1: Data Infrastructure

### Responsibilities

- ✅ Import Excel/CSV files
- ✅ Transform raw data
- ✅ Clean and validate data
- ✅ Load into database
- ✅ Incremental updates

### What It Does NOT Do

- ❌ No KPI calculations
- ❌ No business logic
- ❌ No report generation

### Database Schema (The Contract)

**Base tables (never modified without migration)**:
```sql
-- Source tables (stable)
products (sku, description, category, dimensions, weight, ...)
movements (id, movement_type, sku, quantity, from_zone, to_zone, ...)
orders (order_id, customer_id, status, priority, ...)

-- Relational tables (stable)
order_lines (line_id, order_id, sku, quantity, ...)
```

**Golden Rule**: These tables have STABLE columns. Adding a column = schema migration.

### Extension Point: Views

Instead of modifying base tables, create **views** for each analysis need:

```sql
-- View for movement analysis
CREATE VIEW v_movements_for_analysis AS
SELECT
    m.*,
    p.description as product_name,
    p.category as product_category,
    p.abc_class
FROM movements m
JOIN products p ON m.sku = p.sku;

-- View for order analysis
CREATE VIEW v_orders_for_analysis AS
SELECT
    o.*,
    COUNT(ol.line_id) as line_count,
    SUM(ol.quantity) as total_quantity
FROM orders o
LEFT JOIN order_lines ol ON o.order_id = ol.order_id
GROUP BY o.order_id;
```

**Benefit**: Analyses use views, not direct tables. Data layer can evolve.

---

## Layer 2: Data Access Layer

### Responsibilities

- ✅ Provide stable API to analyses
- ✅ Manage performance (indexes, materialized views)
- ✅ Document available data
- ✅ Version changes

### The Contract: Data Catalog

**File `data_catalog.yaml`**:
```yaml
# CONTRACT VERSION
version: "1.0.0"

# DATA AVAILABLE FOR ANALYSES
datasets:
  products:
    description: "Product master data with ABC classification"
    fields:
      sku: "string (PK) - Product identifier"
      description: "string - Product name"
      category: "string - Product category"
      abc_class: "string - ABC classification (A, B, C)"
      total_picks: "integer - Total pick count (last 30 days)"
      last_pick_date: "date - Last movement date"

  movements:
    description: "All inventory movements"
    fields:
      id: "integer (PK) - Movement ID"
      movement_type: "enum - inbound, outbound, transfer, adjustment"
      sku: "string (FK) - Product reference"
      quantity: "integer - Movement quantity"
      from_zone: "string - Source zone"
      to_zone: "string - Target zone"
      operator_id: "string - Operator identifier"
      created_at: "timestamp - Movement timestamp"

  product_performance:
    description: "Derived product performance metrics"
    fields:
      sku: "string (PK)"
      total_picks: "integer - Total picks"
      avg_pick_quantity: "float - Average quantity per pick"
      pick_frequency_30d: "integer - Picks in last 30 days"
      abc_velocity_class: "string - ABC by velocity"

# AVAILABLE VIEWS
views:
  v_daily_movement_stats:
    description: "Daily movement statistics by type"
    returns: "date, movement_type, count, total_quantity"

  v_operator_performance:
    description: "Operator pick rates and accuracy"
    returns: "operator_id, total_picks, avg_rate, accuracy"
```

### Versioning Rule

```
MAJOR version: Breaking change (e.g., field removed)
MINOR version: New field added (backward compatible)
PATCH version: Bug/performance fix
```

**Examples**:
- `1.0.0` → `2.0.0`: Remove `category` field from `products`
- `1.0.0` → `1.1.0`: Add `storage_location` field to `products`

**Impact**: Analyses can specify `requires: ">=1.0.0,<2.0.0"`

---

## Layer 3: Analysis Engine

### Responsibilities

- ✅ Calculate KPIs
- ✅ Implement business logic
- ✅ Generate report datasets
- ✅ Be easily extensible

### Plugin Architecture

Each analysis is an **independent plugin**:

```
analyses/
├── core/
│   ├── __init__.py
│   └── base_analysis.py           # Abstract base class
├── product_performance/
│   ├── __init__.py
│   ├── analysis.py                # Implements BaseAnalysis
│   ├── config.yaml                # Analysis configuration
│   └── queries.sql                # SQL queries
├── picking_efficiency/
│   ├── __init__.py
│   ├── analysis.py
│   ├── config.yaml
│   └── queries.sql
└── abc_analysis/
    ├── __init__.py
    ├── analysis.py
    ├── config.yaml
    └── queries.sql
```

### Analysis Contract

**Base class `BaseAnalysis`**:
```python
class BaseAnalysis(ABC):
    # Metadata
    name: str
    version: str
    description: str
    author: str

    # Dependencies
    requires_datasets: List[str]      # ["products", "movements"]
    requires_catalog_version: str      # ">=1.0.0"

    # Configuration
    config_schema: dict                # Validation schema

    # Methods to implement
    @abstractmethod
    def validate_inputs(self, db_conn) -> bool:
        """Verify required data is available"""
        pass

    @abstractmethod
    def calculate(self, db_conn) -> pd.DataFrame:
        """Perform calculation and return DataFrame"""
        pass

    @abstractmethod
    def get_metadata(self) -> dict:
        """Return result metadata"""
        pass
```

### Implementation Example

**`analyses/product_performance/analysis.py`**:
```python
class ProductPerformanceAnalysis(BaseAnalysis):
    name = "product_performance"
    version = "1.0.0"
    description = "Calculate product performance metrics"
    author = "Wareflow Team"

    requires_datasets = ["products", "movements"]
    requires_catalog_version = ">=1.0.0"

    config_schema = {
        "lookback_days": {
            "type": "integer",
            "default": 30,
            "description": "Days to look back for analysis"
        }
    }

    def validate_inputs(self, db_conn):
        """Verify required tables/views exist"""
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='products'
        """)
        return len(cursor.fetchall()) > 0

    def calculate(self, db_conn):
        """Calculate product performance"""
        config = self.get_config()
        lookback = config.get('lookback_days', 30)

        query = f"""
        SELECT
            p.sku,
            p.description,
            p.category,
            COUNT(m.id) as total_movements,
            SUM(CASE WHEN m.movement_type = 'outbound' THEN m.quantity ELSE 0 END) as total_picks,
            AVG(CASE WHEN m.movement_type = 'outbound' THEN m.quantity ELSE 0 END) as avg_pick_qty,
            MAX(m.created_at) as last_movement_date
        FROM products p
        LEFT JOIN movements m ON p.sku = m.sku
            AND m.created_at >= DATE('now', '-{lookback} days')
        GROUP BY p.sku
        """
        return pd.read_sql_query(query, db_conn)

    def get_metadata(self):
        return {
            "columns": ["sku", "description", "category", "total_movements",
                       "total_picks", "avg_pick_qty", "last_movement_date"],
            "primary_key": "sku",
            "refresh_frequency": "daily"
        }
```

### Registry System

**`analyses/registry.py`**:
```python
class AnalysisRegistry:
    """Registry of all available analyses"""

    def __init__(self):
        self.analyses = {}
        self._discover_analyses()

    def _discover_analyses(self):
        """Automatically discover all analyses"""
        # Scan analyses/ folder
        # Load each analysis
        # Check dependencies
        # Register if valid

    def get_analysis(self, name: str) -> BaseAnalysis:
        """Return analysis instance"""
        return self.analyses[name]()

    def list_analyses(self) -> List[dict]:
        """List all available analyses"""
        return [
            {
                "name": analysis.name,
                "version": analysis.version,
                "description": analysis.description,
                "status": "ready" if self._check_dependencies(analysis) else "blocked"
            }
            for analysis in self.analyses.values()
        ]

    def run_analysis(self, name: str, db_conn, config: dict = None):
        """Execute analysis"""
        analysis = self.get_analysis(name)

        # Validation
        if not analysis.validate_inputs(db_conn):
            raise AnalysisError(f"Inputs validation failed for {name}")

        # Execution
        result_df = analysis.calculate(db_conn)

        # Metadata
        metadata = analysis.get_metadata()

        return {
            "data": result_df,
            "metadata": metadata
        }
```

### Adding New Analysis (Without Touching Existing)

**Step 1: Create folder**
```bash
mkdir analyses/slow_moving_inventory
cd analyses/slow_moving_inventory
```

**Step 2: Create `analysis.py`**
```python
class SlowMovingInventoryAnalysis(BaseAnalysis):
    name = "slow_moving_inventory"
    version = "1.0.0"
    # ... implementation
```

**Step 3: Create `config.yaml`**
```yaml
name: slow_moving_inventory
description: Identify products with no movement in X days
config:
  no_movement_days:
    type: integer
    default: 90
    description: Days without movement to consider "slow moving"
```

**Step 4: Create `queries.sql`** (optional)
```sql
# Reusable SQL queries
GET_SLOW_MOVERS: >
  SELECT p.sku, p.description, p.category
  FROM products p
  WHERE p.sku NOT IN (
    SELECT DISTINCT sku FROM movements
    WHERE created_at >= DATE('now', '-{days} days')
  )
```

**Step 5: Auto-discovery**
```python
# System automatically discovers new analysis
registry = AnalysisRegistry()
registry.run_analysis("slow_moving_inventory", db_conn)
```

**NO CHANGES** to existing code required!

---

## Layer 4: Export Layer

### Responsibilities

- ✅ Generate Excel files
- ✅ Format data
- ✅ Create charts
- ✅ Apply templates

### Template System

**Report = Template + Data**

```
templates/
├── daily_warehouse_report/
│   ├── template.yaml               # Report configuration
│   ├── sheets/
│   │   ├── summary.yaml            # "Summary" sheet
│   │   ├── products.yaml           # "Products" sheet
│   │   └── movements.yaml          # "Movements" sheet
│   └── styling/
│       └── formats.yaml            # Excel styles
├── abc_analysis_report/
│   ├── template.yaml
│   └── sheets/
│       └── ...
└── custom_reports/
    └── ...
```

### Template Example

**`templates/daily_warehouse_report/template.yaml`**:
```yaml
name: "Daily Warehouse Report"
version: "1.0.0"
description: "Daily warehouse performance report"

# Required analyses
analyses:
  - name: product_performance
    version: ">=1.0.0"
    output_sheet: "Products"
  - name: operator_performance
    version: ">=1.0.0"
    output_sheet: "Operators"

# Output configuration
output:
  filename: "warehouse_report_{date}.xlsx"
  format: "xlsx"
  sheets:
    - name: "Summary"
      type: "dashboard"
      source: "analyses_summary"
    - name: "Products"
      type: "data"
      source: "analysis:product_performance"
      formatting:
        freeze_header: true
        auto_width: true
        bold_header: true
    - name: "Operators"
      type: "data"
      source: "analysis:operator_performance"
```

### Adding New Report

**Step 1: Create template**
```bash
mkdir templates/monthly_inventory_review
```

**Step 2: Define `template.yaml`**
```yaml
name: "Monthly Inventory Review"
analyses:
  - name: slow_moving_inventory
    output_sheet: "Slow Movers"
  - name: dead_stock
    output_sheet: "Dead Stock"
```

**Step 3: Generate**
```bash
python scripts/generate_report.py --template monthly_inventory_review
```

**NO CHANGES** to analysis engine!

---

## Communication Between Layers

### Strict Contract-Based Communication

```
┌──────────────────────┐
│  Data Infrastructure │
└──────────┬───────────┘
           │
           │ CONTRACT: SQL Schema
           │ - Tables: products, movements, orders
           │ - Views: v_movements_for_analysis
           │ - Version: 1.0.0
           ↓
┌──────────────────────┐
│  Data Access Layer   │
└──────────┬───────────┘
           │
           │ CONTRACT: Data Catalog
           │ - Available datasets
           │ - Documented schemas
           │ - Stable version
           ↓
┌──────────────────────┐
│  Analysis Engine     │
│  - Plugin system     │
│  - Registry          │
│  - Versioning        │
└──────────┬───────────┘
           │
           │ CONTRACT: DataFrames
           │ - Standardized format
           │ - Included metadata
           │
           ↓
┌──────────────────────┐
│  Export Layer        │
│  - Templates         │
│  - Formatting        │
└──────────────────────┘
```

### Versioning and Backward Compatibility

**Scenario 1: Add field to `products`**

```sql
-- Version 1.0.0 → 1.1.0
ALTER TABLE products ADD COLUMN storage_location TEXT;
```

**Impact**:
- ✅ Existing analyses: Not affected (optional field)
- ✅ New analyses: Can use `storage_location`
- ✅ Data catalog: Version 1.1.0 (backward compatible)

**Scenario 2: Rename field**

```sql
-- Version 1.0.0 → 2.0.0 (BREAKING CHANGE)
ALTER TABLE products RENAME COLUMN category TO product_category;
```

**Impact**:
- ❌ Existing analyses: Must specify `requires_catalog: "<2.0.0"`
- ✅ New analyses: Can use version 2.0.0
- ✅ Data catalog: Both versions supported in parallel

### Dependency Management

**Each analysis specifies its dependencies**:

```python
class ProductPerformanceAnalysis(BaseAnalysis):
    requires_catalog_version = ">=1.0.0,<2.0.0"
    requires_datasets = ["products", "movements"]
```

**System verifies on load**:
```python
registry = AnalysisRegistry()
catalog_version = get_catalog_version()  # "1.1.0"

# Analysis is compatible
if "1.0.0" <= catalog_version < "2.0.0":
    registry.register(ProductPerformanceAnalysis)
```

---

## Benefits of This Architecture

### 1. Complete Isolation

- Change in ETL = No impact on analyses
- Add analysis = No impact on ETL
- Modify report = No impact on analyses

### 2. Risk-Free Extensibility

To add an analysis:
```
1. Create analyses/new_analysis folder
2. Implement BaseAnalysis
3. Done!
```

No risk of breaking existing code.

### 3. Independent Testing

- Test ETL without analyses
- Test analysis without ETL (mock data)
- Test report without analyses

### 4. Simplified Maintenance

- Bug in ETL? Fix in layer 1
- New KPI? Create new analysis
- New report format? Create new template

### 5. Independent Evolution

- ETL can be replaced by native excel-to-sql → Analyses unchanged
- Analyses can be rewritten in Rust → ETL unchanged
- Exports can move from Excel to PowerBI → Analyses unchanged

---

## Practical Implementation

### Project Structure

```
wareflow-analysis/
│
├── data/                          # Layer 1 (Infrastructure)
│   ├── products.xlsx
│   ├── movements.xlsx
│   └── orders.xlsx
│
├── database/
│   ├── schema/                    # SQL schema (contract)
│   │   ├── 001_create_tables.sql
│   │   ├── 002_create_views.sql
│   │   └── 003_create_indexes.sql
│   └── migrations/                # Schema migrations
│       ├── v1.0.0_to_v1.1.0.sql
│       └── v1.1.0_to_v2.0.0.sql
│
├── etl/                           # Layer 1 (ETL)
│   ├── import.py                  # Import excel-to-sql
│   ├── transform.py               # Data transformation
│   └── update.py                  # Incremental update
│
├── data_access/                   # Layer 2 (Data Access)
│   ├── catalog.yaml               # Data catalog
│   ├── views/                     # SQL views
│   │   ├── v_products_for_analysis.sql
│   │   └── v_movements_for_analysis.sql
│   └── materialized_views/        # Materialized views
│       ├── mv_product_performance.sql
│       └── mv_operator_performance.sql
│
├── analyses/                      # Layer 3 (Analysis Engine)
│   ├── __init__.py
│   ├── base_analysis.py           # Base class
│   ├── registry.py                # Analysis registry
│   ├── product_performance/       # Analysis plugin
│   ├── picking_efficiency/        # Analysis plugin
│   └── slow_moving_inventory/     # Analysis plugin
│
├── reports/                       # Layer 4 (Export)
│   ├── templates/                 # Report templates
│   │   ├── daily_warehouse_report/
│   │   └── monthly_inventory_review/
│   └── generators/                # Generators
│       ├── excel_generator.py
│       └── chart_builder.py
│
├── scripts/                       # Utility scripts
│   ├── run_etl.py                 # Run ETL
│   ├── run_analyses.py            # Run analyses
│   └── generate_reports.py        # Generate reports
│
└── config/
    ├── catalog_version.yaml       # Catalog version
    └── analyses_config.yaml       # Analyses configuration
```

### Daily Workflow

```bash
# 1. Import new data
python scripts/run_etl.py --update

# 2. Run ALL analyses
python scripts/run_analyses.py --all

# 3. Generate ALL reports
python scripts/generate_reports.py --all

# OR one-shot
python scripts/run_pipeline.py
```

### Add New Analysis

```bash
# 1. Create scaffold
python scripts/create_analysis.py --name inventory_turnover

# 2. Implement logic
# Edit analyses/inventory_turnover/analysis.py

# 3. Test
python scripts/test_analysis.py --name inventory_turnover

# 4. Deploy
# Analysis is automatically discovered and available!
```

---

## Strategy Summary

### 4-Layer Separation

1. **Data Infrastructure**: Import and transformation (stable)
2. **Data Access Layer**: API and catalog (stable contract)
3. **Analysis Engine**: Calculations and KPIs (extensible)
4. **Export Layer**: Reports and formatting (plugable)

### Contracts Between Layers

- **SQL Schema** between 1 and 2
- **Data Catalog** between 2 and 3
- **DataFrames** between 3 and 4

### Extensibility

- **Add analysis** = Create new plugin (no existing changes)
- **Modify analysis** = Touch only that plugin
- **Add report** = Create new template

### Evolution

- Each layer evolves independently
- Contracts ensure stability
- Versioning handles breaking changes

### Result

You can add **infinite** new analyses without:
- Modifying ETL
- Modifying existing analyses
- Modifying database structure
- Creating fragile dependencies

Each analysis is an **autonomous** and **isolated** module!

---

## Design Principles

### 1. Single Responsibility

Each layer has ONE job:
- Layer 1: Get data into database
- Layer 2: Provide stable access to data
- Layer 3: Calculate insights
- Layer 4: Present insights

### 2. Open/Closed Principle

- Open for extension (add analyses)
- Closed for modification (stable contracts)

### 3. Dependency Inversion

- High-level modules (analyses) don't depend on low-level (ETL)
- Both depend on abstractions (contracts)

### 4. Interface Segregation

- Each analysis uses ONLY what it needs
- No forced dependencies

### 5. Don't Repeat Yourself

- Common logic in base classes
- Reusable SQL in views
- Shared formatting in templates

---

## Migration Path

### From Monolith to Layered Architecture

**Phase 1: Identify Boundaries**
- Separate ETL logic
- Identify analysis logic
- Extract report formatting

**Phase 2: Define Contracts**
- Document SQL schema
- Create data catalog
- Define analysis interface

**Phase 3: Implement Layers**
- Build ETL layer
- Build data access layer
- Migrate analyses to plugins

**Phase 4: Verify Isolation**
- Test each layer independently
- Verify contracts work
- Check extensibility

---

## Best Practices

### For Layer 1 (Data Infrastructure)

- ✅ Use versioned schema migrations
- ✅ Never break contracts without major version bump
- ✅ Document all breaking changes
- ✅ Provide backward compatibility when possible

### For Layer 2 (Data Access)

- ✅ Version the data catalog
- ✅ Use views for abstraction
- ✅ Materialize expensive queries
- ✅ Document all datasets

### For Layer 3 (Analyses)

- ✅ Extend BaseAnalysis
- ✅ Declare all dependencies
- ✅ Validate inputs before calculation
- ✅ Return metadata with results
- ✅ Handle errors gracefully

### For Layer 4 (Export)

- ✅ Use templates for reports
- ✅ Separate data from presentation
- ✅ Support multiple output formats
- ✅ Make styling configurable

---

*Last Updated: 2025-01-20*
*Version: 1.0.0*
*Status: Architecture Design - Awaiting Implementation*
