# Analyze Command Implementation Plan

## Overview

This document provides a comprehensive analysis of implementing the `analyze` command for the Wareflow Analysis CLI. This command transforms raw imported data into actionable insights and KPIs.

## Current State

**Phase 1 (Completed)**: CLI infrastructure and `init` command ✅
**Phase 2 (In Progress)**: Data processing - `import` command 🔄
**Phase 3 (Next)**: Data analysis - `analyze` command ❌

The `analyze` command is the **intelligence layer** of the system:
- ❌ Cannot run without imported data
- ❌ Depends on `import` command completion
- ✅ Once implemented, enables insights and reporting

## Why the `analyze` Command After `import`?

According to the development flow:
```
init → import → analyze → export → run (full pipeline)
```

The `analyze` command must come after `import` because:
1. It requires data in the SQLite database
2. It reads from database (not Excel files)
3. It's the foundation for the `export` command
4. It provides the insights that make the system valuable

---

## Command Specifications

### Current Implementation

**File**: `src/wareflow_analysis/cli.py:42-44`

```python
@app.command()
def analyze() -> None:
    """Run all analyses."""
    typer.echo("Analyze command not implemented yet")
```

**Status**: Skeleton without implementation

### Command Responsibilities

The `analyze` command must:

#### 1. Database Connection
- **Check database exists**: Verify `warehouse.db` is present
- **Establish connection**: Connect to SQLite database
- **Verify data**: Ensure tables have data (not empty)

#### 2. Execute Analyses
- **Run SQL queries**: Execute analytical queries on imported data
- **Calculate KPIs**: Compute key performance indicators
- **Generate statistics**: Produce descriptive statistics

#### 3. Present Results
- **Display summary**: Show analysis results to user
- **Store results**: Optionally save results in database
- **Report performance**: Show execution time and metrics

---

## Strategic Decision: Simple First, Extensible Later

### Implementation Approach

We'll use a **progressive implementation strategy**:

| Phase | Approach | Complexity | Timeline |
|-------|----------|------------|----------|
| **MVP** | Simple SQL queries in code | Low | 2-3 days |
| **Enhanced** | Configurable queries, more analyses | Medium | 3-4 days |
| **Advanced** | Plugin system (future) | High | 1-2 weeks |

**Recommendation**: Start with MVP, enhance based on usage patterns, add plugins when needed.

---

## Technical Architecture to Implement

### Phase 1: MVP Architecture (Initial Implementation)

#### File Structure

```
src/wareflow_analysis/
├── cli.py                      # ✅ Exists (to modify)
├── init.py                     # ✅ Exists
├── import/                     # 🔄 New module (from import phase)
├── analyze/                    # 🆕 New module
│   ├── __init__.py
│   ├── analyzer.py             # Main analysis orchestration
│   ├── queries.py              # SQL query definitions
│   └── calculators.py          # KPI calculation functions
└── templates/                  # ✅ Exists
```

#### Module Descriptions

**A. Module `queries.py` - SQL Query Definitions**

All SQL queries centralized in one place:

```python
# queries.py

QUERIES = {
    "row_counts": """
        SELECT
            name as table_name,
            (SELECT COUNT(*) FROM pragma_table_info(name)) as column_count
        FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """,

    "table_statistics": """
        SELECT '{table}' as table_name, COUNT(*) as row_count
        FROM {table}
    """,

    "movement_type_summary": """
        SELECT
            type as movement_type,
            COUNT(*) as count,
            SUM(quantite) as total_quantity,
            MIN(date_heure) as first_movement,
            MAX(date_heure) as last_movement
        FROM mouvements
        GROUP BY type
        ORDER BY count DESC
    """,

    "product_movement_frequency": """
        SELECT
            m.no_produit,
            p.nom_produit,
            COUNT(*) as total_movements,
            SUM(CASE WHEN m.type = 'SORTIE' THEN 1 ELSE 0 END) as outbound_count,
            MAX(m.date_heure) as last_movement_date
        FROM mouvements m
        JOIN produits p ON m.no_produit = p.no_produit
        GROUP BY m.no_produit
        ORDER BY total_movements DESC
        LIMIT 20
    """,

    "order_statistics": """
        SELECT
            etat as status,
            COUNT(*) as count,
            COUNT(DISTINCT demandeur) as unique_requesters,
            AVG(lignes) as avg_lines,
            AVG(priorite) as avg_priority
        FROM commandes
        GROUP BY etat
        ORDER BY count DESC
    """
}
```

**B. Module `calculators.py` - KPI Calculations**

Business logic for calculated metrics:

```python
# calculators.py

import pandas as pd
from datetime import datetime, timedelta

class KPICalculator:
    """Calculate KPIs from raw query results."""

    @staticmethod
    def calculate_movement_velocity(movement_df: pd.DataFrame) -> dict:
        """Calculate movement velocity metrics."""
        total_movements = movement_df['count'].sum()
        avg_per_type = movement_df['count'].mean()

        return {
            "total_movements": int(total_movements),
            "movement_types": len(movement_df),
            "avg_movements_per_type": float(avg_per_type),
            "most_common_type": movement_df.iloc[0]['movement_type']
        }

    @staticmethod
    def calculate_time_range(min_date: str, max_date: str) -> dict:
        """Calculate time range statistics."""
        if min_date is None or max_date is None:
            return {"days_span": 0}

        min_dt = pd.to_datetime(min_date)
        max_dt = pd.to_datetime(max_date)
        delta = max_dt - min_dt

        return {
            "days_span": delta.days,
            "first_movement": min_date,
            "last_movement": max_date
        }

    @staticmethod
    def calculate_product_metrics(product_df: pd.DataFrame) -> dict:
        """Calculate product-level metrics."""
        if len(product_df) == 0:
            return {"total_products": 0}

        return {
            "total_products_analyzed": len(product_df),
            "avg_movements_per_product": float(product_df['total_movements'].mean()),
            "max_movements": int(product_df['total_movements'].max()),
            "active_products": int(product_df['total_movements'].gt(0).sum())
        }
```

**C. Module `analyzer.py` - Main Orchestration**

```python
# analyzer.py

import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

from analyze.queries import QUERIES
from analyze.calculators import KPICalculator

class DatabaseAnalyzer:
    """Main analyzer orchestrator."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self.calculator = KPICalculator()
        self.results = {}

    def connect(self) -> Tuple[bool, str]:
        """Connect to database."""
        if not self.db_path.exists():
            return False, f"Database not found: {self.db_path}"

        try:
            self.conn = sqlite3.connect(self.db_path)
            return True, "Connected successfully"
        except Exception as e:
            return False, f"Connection failed: {e}"

    def verify_data(self) -> Tuple[bool, str]:
        """Verify database has data."""
        cursor = self.conn.cursor()

        # Check if tables exist and have data
        tables_to_check = ['produits', 'mouvements', 'commandes']
        empty_tables = []

        for table in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count == 0:
                empty_tables.append(table)

        if empty_tables:
            return False, f"Empty tables: {', '.join(empty_tables)}"

        return True, f"All tables verified ({len(tables_to_check)} tables)"

    def run_query(self, query_name: str) -> pd.DataFrame:
        """Run a named query."""
        query = QUERIES[query_name]
        return pd.read_sql_query(query, self.conn)

    def analyze_row_counts(self) -> Dict:
        """Analyze row counts per table."""
        df = self.run_query("row_counts")

        # Get actual row counts for each table
        table_stats = []
        for _, row in df.iterrows():
            table_name = row['table_name']
            query = QUERIES["table_statistics"].format(table=table_name)
            count_df = pd.read_sql_query(query, self.conn)
            table_stats.append({
                "table": table_name,
                "rows": int(count_df.iloc[0]['row_count'])
            })

        return {
            "summary": {
                "total_tables": len(table_stats),
                "total_rows": sum(t["rows"] for t in table_stats)
            },
            "tables": table_stats
        }

    def analyze_movements(self) -> Dict:
        """Analyze movement patterns."""
        df = self.run_query("movement_type_summary")

        velocity_kpis = self.calculator.calculate_movement_velocity(df)

        # Get time range
        first = df.iloc[0]['first_movement']
        last = df.iloc[0]['last_movement']
        time_kpis = self.calculator.calculate_time_range(first, last)

        return {
            "velocity": velocity_kpis,
            "time_range": time_kpis,
            "by_type": df.to_dict('records')
        }

    def analyze_products(self) -> Dict:
        """Analyze product movement frequency."""
        df = self.run_query("product_movement_frequency")

        return {
            "metrics": self.calculator.calculate_product_metrics(df),
            "top_products": df.head(10).to_dict('records')
        }

    def analyze_orders(self) -> Dict:
        """Analyze order statistics."""
        df = self.run_query("order_statistics")

        return {
            "by_status": df.to_dict('records'),
            "total_orders": int(df['count'].sum())
        }

    def run_all_analyses(self) -> Dict:
        """Run all predefined analyses."""
        results = {
            "row_counts": self.analyze_row_counts(),
            "movements": self.analyze_movements(),
            "products": self.analyze_products(),
            "orders": self.analyze_orders()
        }

        self.results = results
        return results

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
```

---

## Complete Execution Flow

### `analyze` Command Algorithm

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
│ 3. Run Analyses                    │
│    ┌─────────────────────────────┐  │
│    │ a. Row counts               │  │
│    │ b. Movement statistics      │  │
│    │ c. Product frequency        │  │
│    │ d. Order statistics         │  │
│    └─────────────────────────────┘  │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 4. Calculate KPIs                  │
│    - Movement velocity             │
│    - Time ranges                   │
│    - Product metrics               │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 5. Display Report                  │
│    - Summary statistics            │
│    - Key insights                  │
│    - Execution time                │
└─────────────────────────────────────┘
```

---

## Initial Analysis Set (MVP)

### 1. Database Overview Analysis

**Purpose**: Provide a quick overview of database contents

**Queries**:
- Count tables
- Count rows per table
- Identify empty tables

**Output Example**:
```
📊 Database Overview
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tables: 4
  produits:   1,234 rows
  mouvements: 45,678 rows
  commandes:    789 rows
  receptions:   234 rows

Total: 47,935 rows across 4 tables
```

### 2. Movement Analysis

**Purpose**: Understand movement patterns and types

**Queries**:
- Group by movement type (inbound/outbound/transfer)
- Calculate totals per type
- Time range of movements

**Output Example**:
```
📈 Movement Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

By Type:
  SORTIE:     28,901 movements (63.3%)
  ENTRÉE:     12,345 movements (27.0%)
  TRANSFERT:   4,432 movements (9.7%)

Time Range:
  First: 2024-01-01 08:00:00
  Last:  2025-01-21 17:30:00
  Span:  386 days

Velocity:
  Average per day: 118 movements
  Peak day: 2024-12-15 (1,234 movements)
```

### 3. Product Performance Analysis

**Purpose**: Identify top-moving products

**Queries**:
- Count movements per product
- Identify products with most activity
- Calculate outbound vs inbound ratio

**Output Example**:
```
🏆 Top Products by Activity
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. Product A (no_produit: 1001) - 1,234 movements
  2. Product B (no_produit: 1045) - 987 movements
  3. Product C (no_produit: 1123) - 876 movements
  ...

Product Metrics:
  Total active products: 1,234
  Average movements/product: 37.0
  Zero movements: 156 products
```

### 4. Order Status Analysis

**Purpose**: Understand order distribution and status

**Queries**:
- Group by order status
- Calculate average lines per order
- Identify priority distribution

**Output Example**:
```
📋 Order Status Distribution
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status Breakdown:
  EN_COURS:     234 orders (29.7%)
  TERMINÉ:      456 orders (57.8%)
  EN_ATTENTE:    89 orders (11.3%)
  ANNULÉ:        10 orders (1.3%)

Order Metrics:
  Total orders: 789
  Avg lines/order: 12.3
  Avg priority: 2.4
```

---

## Error Handling Strategy

### Validation Errors

| Error Type | Check | Action |
|------------|-------|--------|
| Database not found | File exists check | Exit with error message |
| Empty database | Row count = 0 | Suggest running import |
| Missing table | Table exists check | Report missing tables |
| SQL error | Query execution | Log query and error |

### Error Messages

```python
ERROR_MESSAGES = {
    "no_database": """
❌ Error: Database not found

  File: warehouse.db

💡 Solution:
  Run 'wareflow import' to create and populate the database.
""",

    "empty_database": """
❌ Error: Database is empty

  All tables are empty or missing.

💡 Solution:
  1. Check that Excel files are in data/ directory
  2. Run 'wareflow import' to load data
  3. Verify import completed successfully
""",

    "missing_tables": """
⚠️  Warning: Some tables are missing or empty

  Missing: {missing_tables}

💡 Solution:
  Verify your Excel files contain all required sheets.
""",

    "sql_error": """
❌ Error: Analysis query failed

  Query: {query_name}
  Error: {error}

💡 Solution:
  1. Check database integrity: wareflow status
  2. Try re-importing: wareflow import --force
  3. Report issue if problem persists
"""
}
```

---

## User Experience Design

### Scenario 1: First Analysis After Import

**Context**: User just completed `wareflow import`

```bash
$ wareflow analyze
```

**Output**:
```
✓ Starting analysis process...

🔗 Database: warehouse.db
📊 Verifying data...

Running 4 analyses:
  1/4 Database overview
  2/4 Movement analysis
  3/4 Product performance
  4/4 Order statistics

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ Database overview completed       [0.2s]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ Movement analysis completed       [0.8s]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ Product performance completed     [0.5s]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ Order statistics completed        [0.3s]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ All analyses completed successfully!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 DATABASE OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tables: 4
Total Rows: 47,935

  produits:     1,234 rows (2.6%)
  mouvements:  45,678 rows (95.3%)
  commandes:      789 rows (1.6%)
  receptions:     234 rows (0.5%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 MOVEMENT ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Movement Types:
  ENTRÉE:     12,345 movements (27.0%) ↗
  SORTIE:     28,901 movements (63.3%) ↘
  TRANSFERT:   4,432 movements (9.7%)  ↔

Time Range:
  Period: 2024-01-01 → 2025-01-21
  Span: 386 days
  Average: 118 movements/day

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 PRODUCT PERFORMANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Top 5 Products:
  1. [1001] Product Alpha    1,234 movements
  2. [1045] Product Beta       987 movements
  3. [1123] Product Gamma      876 movements
  4. [1089] Product Delta      765 movements
  5. [1012] Product Epsilon    654 movements

Metrics:
  Active products: 1,234
  Zero movements: 156 (12.6%)
  Avg movements/product: 37.0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 ORDER STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status Distribution:
  TERMINÉ:      456 orders (57.8%) ✅
  EN_COURS:     234 orders (29.7%) 🔄
  EN_ATTENTE:    89 orders (11.3%) ⏳
  ANNULÉ:        10 orders (1.3%) ❌

Order Metrics:
  Total orders: 789
  Avg lines: 12.3
  Avg priority: 2.4

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Next steps:
  wareflow export    # Generate Excel reports
  wareflow status    # Detailed database status

⏱️  Total time: 1.8 seconds
```

---

### Scenario 2: Analysis Without Import

**Context**: User tries to analyze before importing data

```bash
$ wareflow analyze
```

**Output**:
```
❌ Error: Database not found

  File: warehouse.db does not exist in current directory

💡 Solution:
  Run 'wareflow import' to create and populate the database

📖 Documentation: https://github.com/wareflowx/wareflow-analysis
```

---

### Scenario 3: Verbose Mode (--verbose)

**Context**: User wants detailed technical information

```bash
$ wareflow analyze --verbose
```

**Output**:
```
✓ Starting analysis process...

[DEBUG] Connecting to database: warehouse.db
[DEBUG] Connection established
[DEBUG] Verifying data integrity...
[INFO] Database verified: 4 tables, 47,935 rows

Running 4 analyses in verbose mode...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Database overview
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[DEBUG] Executing query: row_counts
[DEBUG] Query returned 4 rows in 0.01s
[DEBUG] Executing query: table_statistics (4 tables)
[INFO] Statistics collected for 4 tables

Tables: 4
Total Rows: 47,935

[... verbose output for each analysis ...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Performance Metrics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Query Execution Times:
  Database overview:     0.21s
  Movement analysis:     0.78s
  Product performance:   0.54s
  Order statistics:      0.31s

Total: 1.84s
Database size: 8.2 MB
Memory usage: 45.2 MB

[DEBUG] Analysis completed successfully
[INFO] Results stored in memory (not persisted)
```

---

### Scenario 4: Specific Analysis (--name)

**Context**: User wants to run only one analysis

```bash
$ wareflow analyze --name movements
```

**Output**:
```
✓ Running analysis: movements

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 MOVEMENT ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Movement Types:
  ENTRÉE:     12,345 movements (27.0%)
  SORTIE:     28,901 movements (63.3%)
  TRANSFERT:   4,432 movements (9.7%)

Time Range:
  First: 2024-01-01 08:00:00
  Last:  2025-01-21 17:30:00
  Span:  386 days

Velocity:
  Average per day: 118 movements
  Busiest day: 2024-12-15 (1,234 movements)

✅ Analysis completed in 0.8s
```

---

### Scenario 5: List Available Analyses (--list)

**Context**: User wants to see what analyses are available

```bash
$ wareflow analyze --list
```

**Output**:
```
📊 Available Analyses
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Core Analyses:
  overview     Database overview and table statistics
  movements    Movement type analysis and patterns
  products     Product performance and frequency
  orders       Order status and metrics

Usage:
  wareflow analyze                  # Run all analyses
  wareflow analyze --name movements  # Run specific analysis
  wareflow analyze --verbose         # Show detailed output
```

---

## Command Options

| Option | Purpose | When to Use |
|--------|---------|-------------|
| `--name NAME` | Run specific analysis | Focus on one analysis type |
| `--list` | List available analyses | Discover what's available |
| `--verbose` | Show detailed info | Debugging or detailed insights |
| `--save` | Save results to database | Persist analysis results |
| `--format FORMAT` | Output format (text/json) | Integration with other tools |

---

## Performance Considerations

### Optimization Strategies

1. **Query Optimization**
   - Use indexes defined in schema
   - Avoid SELECT *
   - Use LIMIT for preview queries

2. **Caching**
   - Cache row counts
   - Reuse DataFrames when possible
   - Lazy load expensive queries

3. **Incremental Analysis**
   - Track last analysis timestamp
   - Only analyze new data
   - Support incremental updates

### Performance Targets

| Operation | Target Time |
|-----------|-------------|
| Database overview | < 1 second |
| Movement analysis | < 2 seconds |
| Product analysis | < 1 second |
| Order analysis | < 1 second |
| All analyses | < 5 seconds |

---

## Tests to Implement

### Unit Tests

```python
# tests/test_analyze_queries.py
def test_row_counts_query()
def test_movement_summary_query()
def test_product_frequency_query()
def test_order_statistics_query()

# tests/test_analyze_calculators.py
def test_calculate_movement_velocity()
def test_calculate_time_range()
def test_calculate_product_metrics()

# tests/test_analyze_analyzer.py
def test_database_connection()
def test_verify_data_with_empty_db()
def test_verify_data_with_valid_data()
def test_run_all_analyses()
def test_run_specific_analysis()
```

### Integration Tests

```python
# tests/test_analyze_integration.py
def test_full_analyze_flow()
def test_analyze_after_import()
def test_analyze_without_import()
def test_analyze_with_corrupted_db()
def test_save_results_to_db()
```

---

## Success Metrics

### Functional Objectives

- ✅ Successfully execute all 4 core analyses
- ✅ Handle empty or missing databases gracefully
- ✅ Display clear, formatted results
- ✅ Complete all analyses in < 5 seconds

### Technical Objectives

- ✅ Zero SQL injection vulnerabilities
- ✅ Proper connection management
- ✅ Memory efficient (< 100MB)
- ✅ Thread-safe (if adding parallel analysis)

### Quality Objectives

- ✅ Test coverage > 80%
- ✅ Clear error messages
- ✅ Consistent output formatting
- ✅ Complete documentation

---

## Future Enhancement: Plugin System

### Current Limitations

The MVP implementation has these constraints:
- **Fixed analyses**: Hard-coded SQL queries
- **Limited extensibility**: Adding analysis requires code changes
- **No configuration**: Analysis parameters are fixed
- **Tight coupling**: Analyses share common logic

### Vision: Plugin Architecture

A future enhancement would introduce a **plugin system** enabling:

#### 1. Plugin Structure

```
analyses/
├── core/
│   ├── base_analysis.py      # Abstract base class
│   └── registry.py            # Plugin discovery and loading
├── product_performance/       # Plugin: Product KPIs
│   ├── analysis.py            # Implements BaseAnalysis
│   ├── config.yaml            # Plugin configuration
│   └── queries.sql            # Reusable SQL queries
├── picking_efficiency/        # Plugin: Picking metrics
│   ├── analysis.py
│   ├── config.yaml
│   └── queries.sql
└── slow_moving_inventory/     # Plugin: Slow movers
    ├── analysis.py
    ├── config.yaml
    └── queries.sql
```

#### 2. Base Analysis Interface

```python
class BaseAnalysis(ABC):
    """Abstract base for all analysis plugins."""

    # Metadata
    name: str
    version: str
    description: str
    author: str

    # Dependencies
    requires_tables: List[str]
    requires_catalog_version: str

    @abstractmethod
    def validate_inputs(self, conn) -> bool:
        """Verify required data exists."""
        pass

    @abstractmethod
    def calculate(self, conn) -> pd.DataFrame:
        """Perform analysis and return results."""
        pass

    @abstractmethod
    def get_metadata(self) -> Dict:
        """Return analysis metadata."""
        pass
```

#### 3. Auto-Discovery Registry

```python
class AnalysisRegistry:
    """Auto-discovers and manages analysis plugins."""

    def __init__(self):
        self.analyses = {}
        self._discover_analyses()

    def _discover_analyses(self):
        """Scan analyses/ folder and load all plugins."""
        # Automatically discover all plugins
        # Validate dependencies
        # Register valid plugins

    def run_analysis(self, name: str, conn):
        """Execute a specific analysis plugin."""
        # Validation
        # Execution
        # Return results
```

#### 4. Benefits of Plugin System

| Aspect | Current MVP | Future Plugin System |
|--------|-------------|---------------------|
| **Adding analysis** | Modify code | Create new folder |
| **Configuration** | Hard-coded | Per-plugin YAML |
| **Testing** | Monolithic | Independent per plugin |
| **Extensibility** | Limited | Infinite |
| **Maintenance** | Risk of breaking changes | Isolated plugins |

#### 5. Migration Path

When the plugin system is implemented:

1. **Keep MVP analyses** as core plugins
2. **Add new analyses** as separate plugins
3. **Maintain backward compatibility** with existing CLI
4. **Gradual migration** of advanced users to plugins

#### 6. Timeline Recommendation

| Phase | Focus | Duration |
|-------|-------|----------|
| **Now** | Implement MVP | 2-3 days |
| **Next** | Gather usage feedback | 1-2 weeks |
| **Then** | Design plugin system | 3-5 days |
| **Finally** | Implement plugins | 1-2 weeks |

**Key Insight**: Start simple, add complexity based on real usage patterns. The MVP provides value immediately while the plugin system can wait until justified by demand.

---

## Dependencies with Other Commands

### Impact on `import`

**Prerequisite**: `import` must complete successfully

**Data requirements**:
- Minimum 1 row in `produits`
- Minimum 100 rows in `mouvements` (for meaningful stats)
- Orders table populated (optional but recommended)

### Impact on `export`

**`export` depends on `analyze` results**:

Two approaches:

**Option A**: Export uses database directly
```bash
wareflow import   # Load data to SQLite
wareflow analyze  # Calculate KPIs (optional)
wareflow export   # Export from SQLite
```

**Option B**: Export uses analyze results
```bash
wareflow import   # Load data to SQLite
wareflow analyze  # Calculate and STORE KPIs
wareflow export   # Export KPIs + raw data
```

**Recommendation**: Start with Option A, evolve to Option B when plugin system is implemented.

### Impact on `run`

**Full pipeline**:
```bash
wareflow run  # → import → analyze → export
```

The `run` command orchestrates all three commands in sequence.

---

## Expected Deliverables

### Code
- 3 Python modules in `src/wareflow_analysis/analyze/`
- Modified `cli.py` with analyze command
- 4+ SQL query templates

### Tests
- 12+ unit tests
- 4+ integration tests
- Test database fixtures

### Documentation
- Complete docstrings
- User guide for analyze command
- Analysis descriptions

### Artifacts
- Sample analysis outputs
- Performance benchmarks
- Query optimization notes

---

## Implementation Phases

### Phase 1: Core MVP (Day 1-2)
1. Create `analyze/` module structure
2. Implement basic queries (row counts, summaries)
3. Create KPI calculator
4. CLI integration

### Phase 2: Enhanced Analyses (Day 3-4)
5. Add movement pattern analysis
6. Add product frequency analysis
7. Add order statistics
8. Output formatting

### Phase 3: Polish & Testing (Day 5)
9. Error handling
10. Performance optimization
11. Complete test coverage
12. Documentation

---

## Conclusion

The `analyze` command is the **intelligence layer** that transforms raw data into actionable insights. Starting with a simple MVP enables immediate value while establishing a foundation for future enhancements.

**Implementation Philosophy**:
1. **Start simple**: Fixed SQL queries in code
2. **Get feedback**: Real usage patterns
3. **Evolve wisely**: Add complexity when justified
4. **Future-proof**: Design for eventual plugin system

**Next Steps After Analyze**:
1. Implement `export` command with Excel generation
2. Implement `run` command for full pipeline
3. Gather user feedback on analyses
4. Design plugin system based on needs

---

*Document created: 2025-01-21*
*Status: Implementation Plan - Ready for Development*
*Priority: HIGH - Core intelligence layer*
