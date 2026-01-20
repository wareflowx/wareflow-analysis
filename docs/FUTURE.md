# Wareflow Analysis - Future Architecture & Scalability

## Real-World Context

### The True Complexity

This is not a simple single-warehouse analysis project. The reality is:

```
Warehouse A (Paris)      Warehouse B (Lyon)      Warehouse C (Marseille)
       │                        │                        │
       ↓                        ↓                        ↓
   WMS Manhattan          WMS SAP EWM             WMS Blue Yonder
       │                        │                        │
       ↓                        ↓                        │
   Excel Files            CSV Files                API Calls
   (French codes)         (English codes)          (JSON format)
```

**Consequences**:
- Different data structures per warehouse
- Different code systems (French vs English)
- Different file formats (Excel vs CSV vs API)
- Different column names
- Different date formats
- Different business rules

### Business Requirements

1. **Reuse the same analysis system** across all warehouses
2. **Add new warehouses** without duplicating code
3. **Compare warehouses** (consolidated reporting)
4. **Handle new WMS systems** without rewriting everything
5. **Scale to 50+ warehouses** across multiple countries

---

## Why OSI-like Architecture is JUSTIFIED

### The Problem: Spaghetti Code Without Architecture

**Without proper layering**:
```python
# This becomes unmaintainable quickly
def load_paris_warehouse():
    df = pd.read_excel("paris_data.xlsx")
    df['type'] = df['Type Mouvement'].map({"ENTRÉE": "inbound"})
    # Paris-specific logic...
    return df

def load_lyon_warehouse():
    df = pd.read_csv("lyon_data.csv", sep=';')
    df['type'] = df['MOVEMENT_TYPE'].str.lower()
    # Lyon-specific logic...
    return df

def analyze_paris_products():
    # Paris-specific analysis...

def analyze_lyon_products():
    # Almost identical but with slight differences...
    # Code duplication!
```

**Result**: For 10 warehouses = 10x code duplication, unmaintainable, error-prone.

### The Solution: Layered Architecture

**With OSI-like layering**:
```
WMS A ────┐
WMS B ────┼──► ETL LAYER (Normalization) ──► STANDARD SCHEMA
WMS C ────┘                                      │
                                                   │
                                    ┌──────────────┴──────────────┐
                                    │  REUSABLE ANALYSIS ENGINE  │
                                    └─────────────────────────────┘
```

**Result**: Add 10 warehouses = add 10 config files, no code duplication.

---

## Complete Architecture: 4 Layers

### Layer Overview

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: ETL & NORMALIZATION                          │
│  - Multi-source adapters (Excel, CSV, API)             │
│  - Warehouse-specific mappers                          │
│  - Code standardization                                 │
│  - Quality validation                                   │
│  Output: Standardized data per warehouse                │
└─────────────────────────┬───────────────────────────────┘
                         │
                         ↓ Standard Schema Contract
                         │
┌─────────────────────────┴───────────────────────────────┐
│  LAYER 2: DATA INTEGRATION                             │
│  - Standard schema (ONE schema for ALL warehouses)      │
│  - Multi-warehouse tables (with warehouse_id)           │
│  - Cross-warehouse views                                │
│  - Global data catalog                                  │
│  Output: Unified database                                │
└─────────────────────────┬───────────────────────────────┘
                         │
                         ↓ SQL/DataFrame Contract
                         │
┌─────────────────────────┴───────────────────────────────┐
│  LAYER 3: ANALYSIS ENGINE (Reusable)                   │
│  - Warehouse-agnostic algorithms                        │
│  - Configurable per warehouse                           │
│  - Cross-warehouse comparison                           │
│  - Extensible plugin system                             │
│  Output: Analysis results                                │
└─────────────────────────┬───────────────────────────────┘
                         │
                         ↓ DataFrame Contract
                         │
┌─────────────────────────┴───────────────────────────────┐
│  LAYER 4: REPORTING & EXPORT                            │
│  - Per-warehouse reports                                 │
│  - Consolidated reports                                  │
│  - Multi-format outputs                                 │
│  - Template-based generation                             │
└───────────────────────────────────────────────────────────┘
```

---

## Layer 1: ETL & Normalization

### Purpose

Extract data from heterogeneous WMS systems and transform into a **standard format**.

### Architecture

```
etl/
├── adapters/                    # Source adapters
│   ├── base_adapter.py          # Abstract base class
│   ├── excel_adapter.py         # Excel files
│   ├── csv_adapter.py           # CSV files
│   └── api_adapter.py           # REST APIs
│
├── mappers/                     # Warehouse-specific mappers
│   ├── paris_manhattan.py       # Paris WMS → Standard
│   ├── lyon_sap.py              # Lyon WMS → Standard
│   └── marseille_blue_yonder.py # Marseille WMS → Standard
│
└── loader.py                    # Load to database
```

### Base Adapter Interface

```python
class BaseAdapter(ABC):
    """Base class for all data source adapters"""

    @abstractmethod
    def extract(self, source_path):
        """Extract raw data from source"""
        pass

    @abstractmethod
    def transform(self, raw_data):
        """Transform to standard schema"""
        pass

    @abstractmethod
    def validate(self, data):
        """Validate data quality"""
        pass

    @abstractmethod
    def load(self, data, warehouse_id):
        """Load into database"""
        pass
```

### Concrete Mapper Example

**Paris Warehouse (Manhattan WMS, Excel)**:
```python
# etl/mappers/paris_manhattan.py
from adapters.excel_adapter import ExcelAdapter
from utils.standard_mappings import FRENCH_MOVEMENT_TYPES

class ParisManhattanMapper(ExcelAdapter):
    """Map Paris WMS (Manhattan) Excel to standard schema"""

    # Paris-specific configuration
    CONFIG = {
        'file_path': 'data/paris/produits.xlsx',
        'sheet_name': 'Products',
        'encoding': 'utf-8',
        'date_format': 'DD/MM/YYYY'
    }

    # Column mapping (French → Standard)
    COLUMN_MAPPING = {
        'REF_ARTICLE': 'sku',
        'DÉSIGNATION': 'description',
        'FAMILLE': 'category',
        'POIDS': 'weight',
        'DATE CRÉATION': 'created_at'
    }

    # Value mapping (WMS codes → Standard)
    VALUE_MAPPING = {
        'Type de mouvement': {
            'ENTRÉE': 'inbound',
            'SORTIE': 'outbound',
            'TRANSFERT': 'transfer',
            'AJUSTEMENT': 'adjustment'
        },
        'Statut': {
            'EN_COURS': 'pending',
            'TERMINÉ': 'completed',
            'ANNULÉ': 'cancelled',
            'EN_ATTENTE': 'pending'
        }
    }

    def transform(self, raw_data):
        """Transform Paris data to standard schema"""
        df = raw_data

        # 1. Rename columns
        df = df.rename(columns=self.COLUMN_MAPPING)

        # 2. Apply value mappings
        for col, mapping in self.VALUE_MAPPING.items():
            if col in df.columns:
                df[col.replace(mapping, inplace=True)

        # 3. Standardize types
        df['created_at'] = pd.to_datetime(
            df['created_at'],
            format=self.CONFIG['date_format']
        )

        return df

    def validate(self, data):
        """Validate data quality"""
        errors = []

        # Check for required columns
        required = ['sku', 'description', 'created_at']
        for col in required:
            if col not in data.columns:
                errors.append(f"Missing column: {col}")

        # Check for null SKUs
        if data['sku'].isnull().any():
            errors.append(f"Found {data['sku'].isnull().sum()} null SKUs")

        # Check for negative quantities
        if 'quantity' in data.columns:
            if (data['quantity'] < 0).any():
                errors.append("Found negative quantities")

        return errors
```

**Lyon Warehouse (SAP EWM, CSV)**:
```python
# etl/mappers/lyon_sap.py
from adapters.csv_adapter import CSVAdapter

class LyonSAPMapper(CSVAdapter):
    """Map Lyon WMS (SAP) CSV to standard schema"""

    CONFIG = {
        'file_path': 'data/lyon/products.csv',
        'delimiter': ';',
        'encoding': 'latin-1'
    }

    COLUMN_MAPPING = {
        'MATERIAL_NR': 'sku',
        'DESCRIPTION': 'description',
        'PRODUCT_FAMILY': 'category'
    }

    VALUE_MAPPING = {
        'MOVEMENT_TYPE': {
            'INBOUND': 'inbound',
            'OUTBOUND': 'outbound'
        }
    }

    # ... implementation similar to Paris
```

**Marseille Warehouse (Blue Yonder, API)**:
```python
# etl/mappers/marseille_blue_yonder.py
from adapters.api_adapter import APIAdapter

class MarseilleBlueYonderMapper(APIAdapter):
    """Map Marseille WMS (Blue Yonder API) to standard schema"""

    CONFIG = {
        'base_url': 'https://api.blueyonder.com/v1',
        'api_key': os.getenv('MARSEILLE_API_KEY'),
        'timeout': 30
    }

    ENDPOINT_MAPPING = {
        'products': '/products',
        'movements': '/inventory/movements'
    }

    RESPONSE_MAPPING = {
        'products': {
            'id': 'sku',
            'name': 'description',
            'category': 'category'
        },
        'movements': {
            'movementType': 'movement_type',
            'quantity': 'quantity'
        }
    }

    def extract(self, source_path):
        """Extract from API"""
        import requests

        products = requests.get(
            self.CONFIG['base_url'] + self.ENDPOINT_MAPPING['products'],
            headers={'Authorization': f"Bearer {self.CONFIG['api_key']}"}
        )

        return pd.DataFrame(products.json())

    # ... rest of implementation
```

### Usage

```python
# etl/load_warehouse.py
from mappers.paris_manhattan import ParisManhattanMapper
from mappers.lyon_sap import LyonSAPMapper
from mappers.marseille_blue_yonder import MarseilleBlueYonderMapper

def load_warehouse_data(warehouse_id):
    """Load data from specific warehouse"""

    # Get mapper for warehouse
    mappers = {
        'paris': ParisManhattanMapper,
        'lyon': LyonSAPMapper,
        'marseille': MarseilleBlueYonderMapper
    }

    mapper_class = mappers.get(warehouse_id)
    if not mapper_class:
        raise ValueError(f"Unknown warehouse: {warehouse_id}")

    # Process data
    mapper = mapper_class()
    raw_data = mapper.extract()
    standard_data = mapper.transform(raw_data)

    errors = mapper.validate(standard_data)
    if errors:
        raise ValueError(f"Validation errors: {errors}")

    # Load into database
    mapper.load(standard_data, warehouse_id)

    return {
        'warehouse': warehouse_id,
        'rows_loaded': len(standard_data),
        'status': 'success'
    }

# Usage
load_warehouse_data('paris')
load_warehouse_data('lyon')
load_warehouse_data('marseille')
```

---

## Layer 2: Data Integration

### Purpose

Provide a **unified database schema** that works for ALL warehouses.

### Standard Schema Design

**Key Principle**: All tables have `warehouse_id` column

```sql
-- Warehouse metadata
CREATE TABLE warehouses (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT,
    wms_type TEXT,
    timezone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products (with warehouse_id)
CREATE TABLE products (
    sku TEXT NOT NULL,
    warehouse_id TEXT NOT NULL,
    description TEXT,
    category TEXT,
    family TEXT,
    abc_class TEXT,
    storage_location TEXT,
    weight REAL,
    dimensions_length REAL,
    dimensions_width REAL,
    dimensions_height REAL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    PRIMARY KEY (sku, warehouse_id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
);

-- Movements (with warehouse_id)
CREATE TABLE movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse_id TEXT NOT NULL,
    movement_type TEXT NOT NULL,
    sku TEXT NOT NULL,
    quantity REAL NOT NULL,
    from_zone TEXT,
    from_aisle TEXT,
    from_bay TEXT,
    from_level TEXT,
    to_zone TEXT,
    to_aisle TEXT,
    to_bay TEXT,
    to_level TEXT,
    operator_id TEXT,
    reference_document TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (sku, warehouse_id) REFERENCES products(sku, warehouse_id)
);

-- Orders (with warehouse_id)
CREATE TABLE orders (
    order_id TEXT NOT NULL,
    warehouse_id TEXT NOT NULL,
    order_date DATE,
    customer_id TEXT,
    status TEXT,
    priority TEXT,
    requested_ship_date DATE,
    actual_ship_date DATE,
    total_value REAL,
    total_weight REAL,
    PRIMARY KEY (order_id, warehouse_id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
);

-- Order lines (with warehouse_id)
CREATE TABLE order_lines (
    line_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    warehouse_id TEXT NOT NULL,
    sku TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL,
    FOREIGN KEY (order_id, warehouse_id) REFERENCES orders(order_id, warehouse_id),
    FOREIGN KEY (sku, warehouse_id) REFERENCES products(sku, warehouse_id)
);
```

### Multi-Warehouse Views

```sql
-- All products across all warehouses
CREATE VIEW v_all_products AS
SELECT
    p.*,
    w.name as warehouse_name,
    w.location as warehouse_location,
    w.wms_type as wms_system
FROM products p
JOIN warehouses w ON p.warehouse_id = w.id;

-- Products for specific warehouse
CREATE VIEW v_paris_products AS
SELECT * FROM products WHERE warehouse_id = 'paris';

CREATE VIEW v_lyon_products AS
SELECT * FROM products WHERE warehouse_id = 'lyon';

-- Cross-warehouse comparison
CREATE VIEW v_cross_warehouse_products AS
SELECT
    sku,
    warehouse_id,
    category,
    abc_class,
    COUNT(*) as warehouse_count
FROM products
GROUP BY sku
HAVING COUNT(*) > 1;
```

### Materialized Views (Performance)

```sql
-- Product performance per warehouse
CREATE TABLE mv_product_performance AS
SELECT
    warehouse_id,
    sku,
    COUNT(*) as total_movements,
    SUM(CASE WHEN movement_type = 'outbound' THEN quantity ELSE 0 END) as total_picks,
    AVG(CASE WHEN movement_type = 'outbound' THEN quantity ELSE 0 END) as avg_pick_qty,
    MAX(created_at) as last_movement_date
FROM movements
GROUP BY warehouse_id, sku;

-- Refresh strategy
CREATE TRIGGER refresh_mv_product_performance
AFTER INSERT ON movements
BEGIN
    DELETE FROM mv_product_performance;
    INSERT INTO mv_product_performance
    SELECT
        warehouse_id,
        sku,
        COUNT(*) as total_movements,
        SUM(CASE WHEN movement_type = 'outbound' THEN quantity ELSE 0 END) as total_picks,
        AVG(CASE WHEN movement_type = 'outbound' THEN quantity ELSE 0 END) as avg_pick_qty,
        MAX(created_at) as last_movement_date
    FROM movements
    GROUP BY warehouse_id, sku;
END;
```

---

## Layer 3: Analysis Engine

### Purpose

**Reusable analysis algorithms** that work on ANY warehouse data.

### Core Principle: Warehouse-Agnostic

All analysis functions accept an optional `warehouse_id` parameter:
- `warehouse_id=None`: Analyze ALL warehouses (consolidated)
- `warehouse_id='paris'`: Analyze ONLY Paris warehouse

### Basic Analysis Example

```python
# analyses/product_performance.py
import pandas as pd
from utils.database import get_connection

def calculate_product_performance(warehouse_id=None, lookback_days=30):
    """
    Calculate product performance metrics.

    Args:
        warehouse_id: If None, calculate for ALL warehouses
                    If 'paris', calculate ONLY for Paris warehouse
        lookback_days: Lookback period in days

    Returns:
        DataFrame with product performance metrics
    """
    conn = get_connection()

    # Build WHERE clause
    where_conditions = []
    if warehouse_id:
        where_conditions.append(f"warehouse_id = '{warehouse_id}'")

    where_clause = ""
    if where_conditions:
        where_clause = "WHERE " + " AND ".join(where_conditions)

    query = f"""
    SELECT
        warehouse_id,
        sku,
        COUNT(*) as total_movements,
        SUM(CASE WHEN movement_type = 'outbound' THEN quantity ELSE 0 END) as total_picks,
        AVG(CASE WHEN movement_type = 'outbound' THEN quantity ELSE 0 END) as avg_pick_qty,
        MAX(created_at) as last_movement_date
    FROM movements
    {where_clause}
    GROUP BY warehouse_id, sku
    """

    return pd.read_sql(query, conn)

# Usage examples
paris_products = calculate_product_performance(warehouse_id='paris')
lyon_products = calculate_product_performance(warehouse_id='lyon')
all_products = calculate_product_performance()  # All warehouses
```

### Advanced Analysis: Cross-Warehouse Comparison

```python
# analyses/cross_warehouse_comparison.py

def compare_abc_classification():
    """Compare ABC classification across warehouses"""
    conn = get_connection()

    query = """
    WITH warehouse_abc AS (
        SELECT
            warehouse_id,
            sku,
            NTILE(100) OVER (
                PARTITION BY warehouse_id
                ORDER BY total_picks DESC
            ) as percentile_rank,
            CASE
                WHEN percentile_rank <= 20 THEN 'A'
                WHEN percentile_rank <= 50 THEN 'B'
                ELSE 'C'
            END as abc_class
        FROM (
            SELECT
                warehouse_id,
                sku,
                SUM(CASE WHEN movement_type = 'outbound' THEN quantity ELSE 0 END) as total_picks
            FROM movements
            GROUP BY warehouse_id, sku
        )
    )
    SELECT
        sku,
        SUM(CASE WHEN abc_class = 'A' THEN 1 ELSE 0 END) as count_a,
        SUM(CASE WHEN abc_class = 'B' THEN 1 ELSE 0 END) as count_b,
        SUM(CASE WHEN abc_class = 'C' THEN 1 ELSE 0 END) as count_c
    FROM warehouse_abc
    GROUP BY sku
    HAVING COUNT(*) > 1
    """

    return pd.read_sql(query, conn)

def benchmark_warehouse_performance():
    """Benchmark key metrics across warehouses"""
    conn = get_connection()

    query = """
    SELECT
        warehouse_id,
        COUNT(DISTINCT sku) as total_products,
        COUNT(*) as total_movements,
        SUM(CASE WHEN movement_type = 'outbound' THEN quantity ELSE 0 END) as total_picks,
        AVG(CASE WHEN movement_type = 'outbound' THEN quantity ELSE 0 END) as avg_pick_qty,
        COUNT(DISTINCT operator_id) as total_operators
    FROM movements
    GROUP BY warehouse_id
    """

    return pd.read_sql(query, conn)

def identify_slow_moving_products(warehouse_id=None, threshold_days=90):
    """Identify products with no movement in X days"""
    conn = get_connection()

    where_clause = f"WHERE warehouse_id = '{warehouse_id}'" if warehouse_id else ""

    query = f"""
    SELECT
        warehouse_id,
        p.sku,
        p.description,
        p.category,
        MAX(m.created_at) as last_movement_date,
        JULIANDAY('now') - JULIANDAY(MAX(m.created_at)) as days_since_movement
    FROM products p
    LEFT JOIN movements m ON p.sku = m.sku AND p.warehouse_id = m.warehouse_id
    {where_clause}
    GROUP BY warehouse_id, p.sku, p.description, p.category
    HAVING days_since_movement > {threshold_days}
    ORDER BY days_since_movement DESC
    """

    return pd.read_sql(query, conn)
```

### Analysis Registry (Auto-Discovery)

```python
# analyses/registry.py
import os
import importlib
from pathlib import Path

class AnalysisRegistry:
    """Registry of all available analyses"""

    def __init__(self):
        self.analyses = {}
        self._discover_analyses()

    def _discover_analyses(self):
        """Auto-discover all analysis modules"""
        analyses_dir = Path(__file__).parent

        for analysis_file in analyses_dir.glob('*.py'):
            if analysis_file.name.startswith('_'):
                continue

            module_name = analysis_file.stem

            try:
                module = importlib.import_module(f'analytics.{module_name}')

                # Find all analysis functions
                for name in dir(module):
                    obj = getattr(module, name)
                    if callable(obj) and name.startswith('calculate_'):
                        self.analyses[name] = {
                            'function': obj,
                            'module': module_name,
                            'name': name.replace('calculate_', '').replace('_', ' ').title()
                        }
            except ImportError:
                continue

    def list_analyses(self):
        """List all available analyses"""
        return [
            {
                'id': name,
                'name': info['name'],
                'module': info['module']
            }
            for name, info in self.analyses.items()
        ]

    def run_analysis(self, analysis_name, **kwargs):
        """Run specific analysis"""
        if analysis_name not in self.analyses:
            raise ValueError(f"Unknown analysis: {analysis_name}")

        return self.analyses[analysis_name]['function'](**kwargs)

    def run_all_analyses(self, warehouse_id=None):
        """Run all analyses for a warehouse"""
        results = {}

        for name, info in self.analyses.items():
            try:
                results[name] = info['function'](warehouse_id=warehouse_id)
            except Exception as e:
                results[name] = {'error': str(e)}

        return results

# Usage
registry = AnalysisRegistry()

# List all analyses
print(registry.list_analyses())
# [
#     {'id': 'calculate_product_performance', 'name': 'Product Performance', ...},
#     {'id': 'calculate_abc_classification', 'name': 'Abc Classification', ...},
#     ...
# ]

# Run specific analysis
result = registry.run_analysis('calculate_product_performance', warehouse_id='paris')

# Run all analyses for Paris
all_results = registry.run_all_analyses(warehouse_id='paris')
```

---

## Layer 4: Reporting & Export

### Purpose

Generate reports for specific warehouses OR consolidated reports across all warehouses.

### Template-Based Report Generation

```python
# reports/generate.py
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

class ReportGenerator:
    """Generate Excel reports"""

    def __init__(self, warehouse_id=None):
        self.warehouse_id = warehouse_id

    def generate_daily_report(self, output_path):
        """Generate daily warehouse report"""

        # Run analyses
        product_perf = calculate_product_performance(self.warehouse_id)
        operator_perf = calculate_operator_performance(self.warehouse_id)
        abc_analysis = calculate_abc_classification(self.warehouse_id)

        # Create Excel workbook
        wb = Workbook()

        # Summary sheet
        ws_summary = wb.active
        ws_summary.title = "Summary"
        self._create_summary_sheet(ws_summary, product_perf, operator_perf)

        # Products sheet
        ws_products = wb.create_sheet("Products")
        self._create_products_sheet(ws_products, product_perf)

        # Operators sheet
        ws_operators = wb.create_sheet("Operators")
        self._create_operators_sheet(ws_operators, operator_perf)

        # ABC Analysis sheet
        ws_abc = wb.create_sheet("ABC Analysis")
        self._create_abc_sheet(ws_abc, abc_analysis)

        # Save
        if self.warehouse_id:
            filename = f"daily_report_{self.warehouse_id}_{date.today()}.xlsx"
        else:
            filename = f"consolidated_report_{date.today()}.xlsx"

        wb.save(output_path / filename)
        return filename

    def generate_comparison_report(self, output_path):
        """Generate cross-warehouse comparison report"""

        # Run cross-warehouse analyses
        benchmark = benchmark_warehouse_performance()
        abc_comparison = compare_abc_classification()

        # Create workbook
        wb = Workbook()

        # Benchmark sheet
        ws = wb.active
        ws.title = "Warehouse Benchmark"

        # Add data
        for r_idx, row in enumerate(benchmark.itertuples(), 1):
            for c_idx, value in enumerate(row, 1):
                if c_idx == 1:
                    ws.cell(r_idx, c_idx, value)
                else:
                    ws.cell(r_idx, c_idx, value)

        # Add charts
        self._add_benchmark_chart(ws)

        # Save
        wb.save(output_path / f"comparison_report_{date.today()}.xlsx")

    def _create_summary_sheet(self, ws, product_perf, operator_perf):
        """Create summary sheet"""
        ws['A1'] = "Warehouse Summary"
        ws['A1'].font = Font(bold=True, size=16)

        ws['A3'] = "Total Products"
        ws['B3'] = len(product_perf)

        ws['A4'] = "Total Movements"
        ws['B4'] = product_perf['total_movements'].sum()

        ws['A5'] = "Total Picks"
        ws['B5'] = product_perf['total_picks'].sum()

        ws['A7'] = "Total Operators"
        ws['B7'] = len(operator_perf)

        # Format
        for row in ws.iter_rows(min_row=3, max_row=7, min_col=1, max_col=2):
            for cell in row:
                cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
```

### Report Configuration

**reports/templates/daily_report.yaml**:
```yaml
name: "Daily Warehouse Report"
type: "daily"
frequency: "daily"

sheets:
  - name: "Summary"
    type: "summary"
    analyses:
      - product_performance
      - operator_performance

  - name: "Products"
    type: "data"
    analysis: product_performance
    columns:
      - sku
      - description
      - category
      - total_movements
      - total_picks
      - avg_pick_qty
    formatting:
      freeze_header: true
      auto_width: true
      bold_header: true

  - name: "Operators"
    type: "data"
    analysis: operator_performance
    columns:
      - operator_id
      - total_picks
      - avg_pick_rate
      - accuracy
    formatting:
      freeze_header: true

output:
  per_warehouse: true
  consolidated: true
  filename_pattern: "{report_type}_{warehouse_id}_{date}.xlsx"
```

---

## Multi-Warehouse Configuration

### Centralized Configuration File

**config/warehouses.yaml**:
```yaml
# Warehouse Registry
warehouses:
  paris:
    name: "Paris Warehouse"
    location: "Paris, France"
    wms_type: "Manhattan"
    timezone: "Europe/Paris"
    language: "fr"

    # ETL Configuration
    etl:
      adapter: "ParisManhattanMapper"
      sources:
        products:
          type: "excel"
          path: "data/paris/produits.xlsx"
          sheet: "Products"
        movements:
          type: "excel"
          path: "data/paris/mouvements.xlsx"
          sheet: "Mouvements"
        orders:
          type: "excel"
          path: "data/paris/commandes.xlsx"
          sheet: "Commandes"

    # Column Mappings
    mappings:
      products:
        REF_ARTICLE: sku
        DÉSIGNATION: description
        FAMILLE: category
        POIDS (KG): weight
        DATE CRÉATION: created_at
      movements:
        No. du produit: sku
        Type de mouvement: movement_type
        Quantité: quantity
        Date et heure: created_at

    # Value Mappings (WMS codes → Standard)
    value_maps:
      movement_type:
        ENTRÉE: inbound
        SORTIE: outbound
        TRANSFERT: transfer
        AJUSTEMENT: adjustment
      status:
        EN_COURS: pending
        TERMINÉ: completed
        ANNULÉ: cancelled
        EN_ATTENTE: pending

    # Validation Rules
    validation:
      required_fields: [sku, created_at]
      positive_quantities: true
      date_format: "DD/MM/YYYY"

    # Business Rules
    business_rules:
      picking_zones: [A, B, C, D]
      low_stock_threshold: 10
      abc_thresholds:
        class_a: 20
        class_b: 50

  lyon:
    name: "Lyon Warehouse"
    location: "Lyon, France"
    wms_type: "SAP EWM"
    timezone: "Europe/Paris"
    language: "en"

    etl:
      adapter: "LyonSAPMapper"
      sources:
        products:
          type: "csv"
          path: "data/lyon/products.csv"
          delimiter: ";"
          encoding: "latin-1"
        movements:
          type: "csv"
          path: "data/lyon/movements.csv"
          delimiter: ","
          encoding: "utf-8"

    mappings:
      products:
        MATERIAL_NR: sku
        DESCRIPTION: description
        PRODUCT_FAMILY: category
      movements:
        MATERIAL: sku
        MOVEMENT_TYPE: movement_type
        QUANTITY: quantity

    value_maps:
      movement_type:
        INBOUND: inbound
        OUTBOUND: outbound
        TRANSFER: transfer

    validation:
      required_fields: [sku, movement_type, quantity]
      date_format: "YYYY-MM-DD"

  marseille:
    name: "Marseille Warehouse"
    location: "Marseille, France"
    wms_type: "Blue Yonder"
    timezone: "Europe/Paris"
    language: "en"

    etl:
      adapter: "MarseilleAPIMapper"
      sources:
        products:
          type: "api"
          base_url: "https://api.blueyonder.com/v1"
          endpoints:
            products: /products
            movements: /inventory/movements
        auth:
          type: "bearer"
          api_key_env: "MARSEILLE_API_KEY"

    mappings:
      products:
        id: sku
        name: description
        category: category
        productFamily: category
      movements:
        movementType: movement_type
        quantity: quantity
        createdDateTime: created_at

    value_maps:
      movement_type:
        RECEIPT: inbound
        SHIPMENT: outbound
        TRANSFER: transfer

    validation:
      required_fields: [sku, movement_type]
      date_format: "ISO8601"

# Global Configuration
global:
  database:
    path: "database/wareflow.db"
    backup_enabled: true
    backup_path: "backups/"

  analyses:
    output_path: "output/analyses/"
    refresh_interval: 86400  # 24 hours

  reports:
    output_path: "output/reports/"
    default_template: "daily_report"

  logging:
    level: "INFO"
    path: "logs/"
    rotation: "daily"
    retention_days: 30
```

### Configuration Loader

```python
# config/loader.py
import yaml
import os

class WarehouseConfig:
    """Load warehouse configuration"""

    def __init__(self, config_path='config/warehouses.yaml'):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def get_warehouse(self, warehouse_id):
        """Get specific warehouse configuration"""
        return self.config['warehouses'][warehouse_id]

    def get_all_warehouses(self):
        """Get all warehouse IDs"""
        return list(self.config['warehouses'].keys())

    def get_etl_adapter(self, warehouse_id):
        """Get ETL adapter class name"""
        return self.config['warehouses'][warehouse_id]['etl']['adapter']

    def get_mappings(self, warehouse_id, data_type):
        """Get column mappings for data type"""
        return self.config['warehouses'][warehouse_id]['mappings'][data_type]

    def get_value_maps(self, warehouse_id):
        """Get value mappings"""
        return self.config['warehouses'][warehouse_id]['value_maps']

# Usage
config = WarehouseConfig()

# Load Paris configuration
paris_config = config.get_warehouse('paris')
print(paris_config['name'])  # "Paris Warehouse"
print(paris_config['wms_type'])  # "Manhattan"

# Get Paris products mapping
products_mapping = config.get_mappings('paris', 'products')
print(products_mapping)  # {'REF_ARTICLE': 'sku', ...}

# Get all warehouses
all_warehouses = config.get_all_warehouses()
print(all_warehouses)  # ['paris', 'lyon', 'marseille']
```

---

## Complete Workflow

### Daily Automated Pipeline

```python
# scripts/daily_pipeline.py
from etl.load_warehouse import load_warehouse_data
from analyses.registry import AnalysisRegistry
from reports.generate import ReportGenerator
from config.loader import WarehouseConfig

def run_daily_pipeline(warehouse_id=None):
    """
    Run complete daily pipeline.

    Args:
        warehouse_id: If None, run for ALL warehouses
                   If 'paris', run ONLY for Paris
    """
    config = WarehouseConfig()

    if warehouse_id:
        warehouses = [warehouse_id]
    else:
        warehouses = config.get_all_warehouses()

    results = []

    for wh_id in warehouses:
        print(f"\n{'='*60}")
        print(f"Processing warehouse: {wh_id}")
        print(f"{'='*60}")

        # Phase 1: Load data
        print("Phase 1: Loading data...")
        load_result = load_warehouse_data(wh_id)
        print(f"  Loaded {load_result['rows_loaded']} rows")

        # Phase 2: Run analyses
        print("Phase 2: Running analyses...")
        registry = AnalysisRegistry()
        analysis_results = registry.run_all_analyses(warehouse_id=wh_id)

        for analysis_name, result in analysis_results.items():
            if 'error' in result:
                print(f"  ✗ {analysis_name}: {result['error']}")
            else:
                print(f"  ✓ {analysis_name}: {len(result)} rows")

        # Phase 3: Generate reports
        print("Phase 3: Generating reports...")
        generator = ReportGenerator(warehouse_id=wh_id)
        report_file = generator.generate_daily_report(output_path='output/reports/')
        print(f"  Generated: {report_file}")

        results.append({
            'warehouse': wh_id,
            'status': 'success',
            'rows_loaded': load_result['rows_loaded'],
            'report_file': report_file
        })

    # Generate consolidated report if processing all warehouses
    if not warehouse_id:
        print(f"\n{'='*60}")
        print("Generating consolidated report...")
        print(f"{'='*60}")

        generator = ReportGenerator(warehouse_id=None)
        consolidated_report = generator.generate_comparison_report(output_path='output/reports/')
        print(f"  Generated: {consolidated_report}")

    return results

# Usage
if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        warehouse_id = sys.argv[1]
    else:
        warehouse_id = None

    results = run_daily_pipeline(warehouse_id)

    print(f"\n{'='*60}")
    print("Pipeline complete!")
    print(f"{'='*60}")
```

### Command Line Usage

```bash
# Process all warehouses
python scripts/daily_pipeline.py

# Process specific warehouse
python scripts/daily_pipeline.py paris

# Schedule daily (cron)
0 2 * * * cd /path/to/wareflow-analysis && python scripts/daily_pipeline.py >> logs/pipeline.log 2>&1
```

---

## Adding a New Warehouse

### Step-by-Step Guide

**Scenario**: Add a new warehouse in Bordeaux with a different WMS

#### Step 1: Define Configuration

**config/warehouses.yaml** - Add new warehouse:
```yaml
  bordeaux:
    name: "Bordeaux Warehouse"
    location: "Bordeaux, France"
    wms_type: "Körber"
    timezone: "Europe/Paris"

    etl:
      adapter: "BordeauxKorberMapper"
      sources:
        products:
          type: "excel"
          path: "data/bordeaux/products.xlsx"
        movements:
          type: "excel"
          path: "data/bordeaux/movements.xlsx"

    mappings:
      products:
        SKU: sku
        PRODUCT_NAME: description
        CATEGORY: category
      movements:
        SKU: sku
        MOV_TYPE: movement_type
        QTY: quantity

    value_maps:
      movement_type:
        REC: inbound
        SHIP: outbound
        TRF: transfer
```

#### Step 2: Create Mapper

**etl/mappers/bordeaux_korber.py**:
```python
from adapters.excel_adapter import ExcelAdapter

class BordeauxKorberMapper(ExcelAdapter):
    """Map Bordeaux WMS (Körber) to standard schema"""

    CONFIG = {
        'file_path': 'data/bordeaux/products.xlsx',
        'sheet_name': 'Products'
    }

    COLUMN_MAPPING = {
        'SKU': 'sku',
        'PRODUCT_NAME': 'description',
        'CATEGORY': 'category'
    }

    VALUE_MAPPING = {
        'MOV_TYPE': {
            'REC': 'inbound',
            'SHIP': 'outbound',
            'TRF': 'transfer'
        }
    }

    def transform(self, raw_data):
        df = raw_data.rename(columns=self.COLUMN_MAPPING)
        # Apply transformations...
        return df
```

#### Step 3: Test the Import

```bash
# Test Bordeaux import
python scripts/test_import.py bordeaux

# Run pipeline for Bordeaux
python scripts/daily_pipeline.py bordeaux
```

#### Step 4: Verify Results

```python
# Check data in database
conn = sqlite3.connect('database/wareflow.db')
df = pd.read_sql("SELECT * FROM products WHERE warehouse_id='bordeaux'", conn)
print(df.head())
```

**Result**: All existing analyses now work for Bordeaux automatically!

---

## Benefits of This Architecture

### 1. True Scalability

Add 10, 50, 100 warehouses:
```
10 warehouses  = 10 mappers  (no analysis code changes)
50 warehouses  = 50 mappers  (no analysis code changes)
100 warehouses = 100 mappers (no analysis code changes)
```

### 2. Code Reusability

One analysis function works for ALL warehouses:
```python
# This ONE function works for Paris, Lyon, Marseille, Bordeaux...
def calculate_abc_classification(warehouse_id=None):
    # ... implementation

# Use it
paris_abc = calculate_abc_classification('paris')
lyon_abc = calculate_abc_classification('lyon')
bordeaux_abc = calculate_abc_classification('bordeaux')
all_abc = calculate_abc_classification()  # All warehouses
```

### 3. Maintainability

Each warehouse has its own mapper:
```
etl/mappers/
├── paris_manhattan.py       # Paris-specific logic
├── lyon_sap.py              # Lyon-specific logic
├── marseille_blue_yonder.py # Marseille-specific logic
└── bordeaux_korber.py       # Bordeaux-specific logic
```

Change Paris WMS → Update `paris_manhattan.py` only
No impact on Lyon, Marseille, Bordeaux, or analyses!

### 4. Isolation of Concerns

- **ETL Team**: Manages adapters/mappers
- **Analytics Team**: Develops analysis algorithms
- **Reporting Team**: Creates report templates

Each team works independently without stepping on each other.

### 5. Testing

```python
# Test each warehouse independently
def test_paris_import():
    mapper = ParisManhattanMapper()
    data = mapper.extract()
    result = mapper.transform(data)
    assert result['movement_type'].iloc[0] == 'inbound'  # Not "ENTRÉE"

def test_lyon_import():
    mapper = LyonSAPMapper()
    # ... test logic

# Test analyses work with any warehouse
def test_abc_analysis():
    result = calculate_abc_classification('test_warehouse')
    assert 'A' in result['abc_class'].values
```

### 6. Cross-Warehouse Analytics

```python
# Compare performance across all warehouses
benchmark = benchmark_warehouse_performance()
print(benchmark)

# Output:
#   warehouse_id  total_picks  avg_pick_qty
#   paris         15000        50
#   lyon          12000        45
#   marseille      18000        55
#   bordeaux       8000        40
```

### 7. Easy Onboarding

New warehouse:
```
1. Add to config/warehouses.yaml
2. Create etl/mappers/newwarehouse_mapper.py
3. Test import
4. Done! (All existing analyses work)
```

---

## Implementation Strategy

### Phase 1: Foundation (Weeks 1-2)

**Goals**: Core infrastructure

**Tasks**:
- [ ] Set up project structure
- [ ] Define standard database schema
- [ ] Create base adapter classes
- [ ] Implement Paris warehouse (proof of concept)
- [ ] Create basic analyses (product performance, ABC)

**Deliverable**: Working Paris warehouse pipeline

### Phase 2: Multi-Warehouse (Weeks 3-4)

**Goals**: Add 2 more warehouses

**Tasks**:
- [ ] Implement Lyon warehouse
- [ ] Implement Marseille warehouse
- [ ] Create cross-warehouse comparison
- [ ] Consolidated reporting
- [ ] Configuration system

**Deliverable**: 3 warehouses, cross-warehouse analytics

### Phase 3: Advanced Analytics (Weeks 5-6)

**Goals**: Comprehensive analyses

**Tasks**:
- [ ] Picking efficiency analysis
- [ ] Operator performance
- [ ] Replenishment analysis
- [ ] Product lifecycle
- [ ] Advanced cross-warehouse comparisons

**Deliverable**: Complete analysis suite

### Phase 4: Automation & Reporting (Weeks 7-8)

**Goals**: Production-ready system

**Tasks**:
- [ ] Automated daily pipeline
- [ ] Report scheduling
- [ ] Error handling and logging
- [ ] Performance optimization
- [ ] Documentation

**Deliverable**: Production system

---

## Key Principles

### 1. Contract-Based Communication

**Between layers**:
- Layer 1 → Layer 2: Standard SQL schema
- Layer 2 → Layer 3: Database queries
- Layer 3 → Layer 4: DataFrames

**Change contracts only when necessary**:
- Use MINOR version for additive changes
- Use MAJOR version for breaking changes
- Document all changes

### 2. Warehouse Isolation

Each warehouse is isolated:
- **Separate mapper**: `ParisManhattanMapper`, `LyonSAPMapper`
- **Separate config**: In `config/warehouses.yaml`
- **Separate data**: `warehouse_id` column in all tables

But all use the **same standard schema** and **same analyses**.

### 3. Configuration Over Code

Warehouse-specific logic in **YAML config**, not Python code:
```yaml
# Good
paris:
  mappings:
    REF_ARTICLE: sku

# Bad
# if warehouse == 'paris':
#     mapping['REF_ARTICLE'] = 'sku'
```

### 4. Fail Fast

Validate early:
```python
# Validate on load
mapper = get_mapper(warehouse_id)
errors = mapper.validate(raw_data)
if errors:
    raise ValidationError(f"Validation failed: {errors}")

# Don't let bad data reach database
```

### 5. Convention Over Configuration

Use sensible defaults:
```python
# Default: analyze all warehouses
def calculate_abc_classification(warehouse_id=None):
    # If warehouse_id is None, analyze ALL
```

But allow override when needed.

---

## Common Patterns

### Pattern 1: Warehouse-Specific → Standard

**Problem**: Paris uses French codes, Lyon uses English

**Solution**: Value mapping in Layer 1
```python
# Paris mapper
VALUE_MAPPING = {'ENTRÉE': 'inbound'}

# Lyon mapper
VALUE_MAPPING = {'INBOUND': 'inbound'}
```

Both produce same standard output.

### Pattern 2: Single Warehouse → All Warehouses

**Problem**: Want to analyze one warehouse OR all warehouses

**Solution**: Optional parameter
```python
def calculate_performance(warehouse_id=None):
    where = f"WHERE warehouse_id = '{warehouse_id}'" if warehouse_id else ""
    # ... query
```

### Pattern 3: Extend, Don't Modify

**Problem**: Need warehouse-specific analysis logic

**Solution**: Inheritance and configuration
```python
class BaseAnalysis:
    def calculate(self, warehouse_id):
        # Base implementation

class ParisAnalysis(BaseAnalysis):
    def calculate(self, warehouse_id):
        # Paris-specific logic
        if warehouse_id == 'paris':
            # Custom behavior
            pass
        return super().calculate(warehouse_id)
```

---

## Migration Path from Monolith

### Current State (Likely)

```python
# Single script with mixed concerns
def process_warehouse():
    # Load data
    df = pd.read_excel('paris.xlsx')

    # Clean data (Paris-specific)
    df = df.rename(columns={'REF': 'sku'})
    df['type'] = df['Type'].map({'ENTRÉE': 'inbound'})

    # Analyze
    result = df.groupby('sku').agg({'quantity': 'sum'})

    # Export
    result.to_excel('report.xlsx')
```

### Future State (Layered)

```
┌─────────────────────┐
│  Load Data          │
│  (Layer 1: ETL)     │
│  - ParisManhattan   │
│    Mapper           │
└──────────┬──────────┘
           │
           ↓ (Standard Schema)
┌─────────────────────┐
│  Database           │
│  (Layer 2: Data)     │
│  - Standard Tables  │
└──────────┬──────────┘
           │
           ↓ (SQL Queries)
┌─────────────────────┐
│  Calculate          │
│  (Layer 3: Analyze) │
│  - calculate_abc()  │
│  - calculate_perf() │
└──────────┬──────────┘
           │
           ↓ (DataFrames)
┌─────────────────────┐
│  Export             │
│  (Layer 4: Report)  │
│  - Excel Generator   │
└─────────────────────┘
```

---

## Technology Stack

### Database
- **SQLite**: Single file, portable, SQL support
- **Indexes**: On `warehouse_id`, `sku`, `created_at`
- **Foreign keys**: Enable for integrity
- **Triggers**: For materialized views

### Python Libraries
- **pandas**: Data manipulation
- **openpyxl**: Excel generation
- **SQLAlchemy**: Database ORM (optional)
- **pydantic**: Data validation
- **PyYAML**: Configuration
- **pytest**: Testing

### Development Tools
- **pytest**: Testing framework
- **black**: Code formatting
- **pylint**: Linting
- **mypy**: Type checking

---

## Performance Considerations

### Database Design

**Indexing strategy**:
```sql
-- Critical indexes
CREATE INDEX idx_movements_warehouse_sku ON movements(warehouse_id, sku);
CREATE INDEX idx_movements_date ON movements(created_at);
CREATE INDEX idx_products_warehouse_sku ON products(warehouse_id, sku);

-- Composite indexes for common queries
CREATE INDEX idx_movements_analysis ON movements(warehouse_id, movement_type, created_at);
```

**Partitioning** (if scaling needed):
```sql
-- For very large datasets, consider partitioning by warehouse_id
-- Or separate database per warehouse
```

### Query Optimization

```python
# Bad: N+1 queries
for sku in skus:
    df = pd.read_sql(f"SELECT * FROM movements WHERE sku = '{sku}'", conn)

# Good: Single query
skus_str = "', '".join(skus)
df = pd.read_sql(f"SELECT * FROM movements WHERE sku IN ('{skus_str}')", conn)
```

### Caching

```python
# Cache analysis results
from functools import lru_cache

@lru_cache(maxsize=128)
def calculate_abc_classification(warehouse_id, lookback_days):
    """Cached version - same inputs = cache hit"""
    # ... implementation
```

---

## Error Handling Strategy

### Layer 1: ETL Errors

```python
try:
    mapper = get_mapper(warehouse_id)
    data = mapper.extract()
except FileNotFoundError as e:
    logger.error(f"File not found for {warehouse_id}: {e}")
    raise
except ValidationError as e:
    logger.error(f"Validation failed for {warehouse_id}: {e}")
    raise
```

### Layer 2: Database Errors

```python
try:
    save_to_database(data, warehouse_id)
except sqlite3.IntegrityError as e:
    logger.error(f"Integrity error for {warehouse_id}: {e}")
    raise
```

### Layer 3: Analysis Errors

```python
try:
    result = calculate_performance(warehouse_id)
except pd.errors.DatabaseError as e:
    logger.error(f"Query failed for {warehouse_id}: {e}")
    return None  # Graceful degradation
```

---

## Monitoring & Observability

### Logging Strategy

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler()
    ]
)

# Use in pipeline
logger.info(f"Starting pipeline for warehouse: {warehouse_id}")
logger.info(f"Loaded {rows} rows")
logger.error(f"Analysis failed: {error}")
```

### Metrics Tracking

```python
# Simple metrics
import time

def time_analytics(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start

        logger.info(f"{func.__name__} completed in {duration:.2f}s")
        return result
    return wrapper

@time_analytics
def calculate_performance(warehouse_id):
    # ... implementation
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_mappers.py
def test_paris_mapper():
    mapper = ParisManhattanMapper()
    raw = load_test_data('paris_test.xlsx')
    result = mapper.transform(raw)

    assert result['movement_type'].iloc[0] == 'inbound'
    assert result['sku'].notnull().all()

def test_lyon_mapper():
    mapper = LyonSAPMapper()
    # ... similar tests
```

### Integration Tests

```python
# tests/test_pipeline.py
def test_full_pipeline_paris():
    result = run_daily_pipeline('paris')
    assert result['status'] == 'success'
    assert os.path.exists(result['report_file'])

def test_cross_warehouse_analysis():
    result = benchmark_warehouse_performance()
    assert len(result) >= 3  # At least 3 warehouses
```

### Test Data

```
tests/
├── fixtures/
│   ├── paris_test.xlsx
│   ├── lyon_test.csv
│   └── marseille_test.json
└── expected/
    ├── paris_products.csv
    └── lyon_products.csv
```

---

## Documentation

### Required Documentation

1. **Architecture** (this document)
2. **API Documentation**: Docstrings for all analysis functions
3. **Configuration Guide**: How to add new warehouse
4. **Troubleshooting Guide**: Common issues and solutions
5. **Onboarding Guide**: For new developers

### Code Documentation

```python
def calculate_product_performance(warehouse_id=None, lookback_days=30):
    """
    Calculate product performance metrics for a warehouse or all warehouses.

    This analysis provides key performance indicators for products including
    total movements, pick quantities, and velocity metrics. Used for ABC
    classification and inventory optimization.

    Args:
        warehouse_id (str, optional): Warehouse identifier. If None, analyzes
            all warehouses. Default: None.
        lookback_days (int): Number of days to look back for analysis.
            Default: 30.

    Returns:
        pandas.DataFrame: DataFrame with columns:
            - warehouse_id (str): Warehouse identifier
            - sku (str): Product SKU
            - total_movements (int): Total number of movements
            - total_picks (int): Total quantity picked
            - avg_pick_qty (float): Average pick quantity
            - last_movement_date (datetime): Date of last movement

    Raises:
        ValueError: If warehouse_id is invalid
        DatabaseError: If query fails

    Example:
        >>> # Analyze Paris warehouse
        >>> paris_perf = calculate_product_performance('paris')
        >>> # Analyze all warehouses
        >>> all_perf = calculate_product_performance()

    See Also:
        calculate_abc_classification: ABC analysis based on performance
        benchmark_warehouse_performance: Cross-warehouse comparison
    """
    pass
```

---

## Conclusion

### Why OSI-like Architecture is Essential

For a **multi-warehouse, multi-WMS system**, layered architecture is NOT over-engineering—it's **essential**:

1. **Scalability**: Add warehouses without duplicating code
2. **Maintainability**: Each warehouse's logic is isolated
3. **Reusability**: Same analysis code works for all warehouses
4. **Flexibility**: Change one warehouse without affecting others
5. **Testability**: Test each component independently
6. **Comparability**: Easy cross-warehouse analytics

### Key Takeaways

**Standard Schema is King**:
- All warehouses must use the same database schema
- `warehouse_id` column in all tables
- Standard column names, types, formats

**ETL Layer is Isolation**:
- Each warehouse has its own mapper
- Mapper handles all warehouse-specific logic
- Outputs standard schema

**Analysis Layer is Universal**:
- Works with any warehouse
- Optional `warehouse_id` parameter
- No warehouse-specific logic

**Configuration Drives Behavior**:
- Warehouse definitions in YAML
- Column mappings configurable
- Value mappings configurable

### The Result

```
Today: 3 warehouses (Paris, Lyon, Marseille)
Tomorrow: 10 warehouses
Next Month: 50 warehouses across Europe
Next Year: 200 warehouses worldwide

Code changes needed: 0 (just add config files)
```

---

## Next Steps

### Immediate Actions

1. **Review this architecture** with stakeholders
2. **Validate assumptions** with actual data samples
3. **Choose pilot warehouse** (recommend Paris)
4. **Define MVP analyses** (start with 3-5 key analyses)

### Implementation Priority

1. **Phase 1**: Build Layer 1 + Layer 2 for ONE warehouse (Paris)
2. **Phase 2**: Implement core analyses (3-5 analyses)
3. **Phase 3**: Add 2 more warehouses (Lyon, Marseille)
4. **Phase 4**: Cross-warehouse analytics
5. **Phase 5**: Add remaining warehouses as needed

### Success Criteria

- [ ] Can process Paris warehouse end-to-end
- [ ] Can add Lyon warehouse without analysis code changes
- [ ] Can compare performance across warehouses
- [ ] Can add new analysis without breaking existing code
- [ ] Can generate per-warehouse and consolidated reports
- [ ] System can scale to 50+ warehouses

---

*Last Updated: 2025-01-20*
*Version: 2.0 - Multi-Warehouse Architecture*
*Status: Architecture Design - Ready for Implementation*
