# Wareflow Analysis Project

## Overview

Wareflow Analysis is a data analysis system designed to process and analyze warehouse data from any Warehouse Management System (WMS). The project follows a configuration-driven architecture that separates the core analysis engine from WMS-specific data structures.

## Philosophy

The core principle is **separation of concerns**:
- **Fixed Components**: Internal data models, SQLite database schema, analysis algorithms, and business logic
- **Configurable Components**: Mapping rules, data source definitions, and WMS-specific transformations

This approach allows the same analysis engine to work with different WMS systems by simply changing configuration files.

## Architecture

### System Flow

```
┌──────────────────┐
│ WMS DATA SOURCES │ (Movements, Picking Lines,
│   (Your Files)   │  Replenishment Reports,
│                  │  Product Catalog, Order History)
└────────┬─────────┘
         │
         ↓
┌─────────────────────────────────────────────────────┐
│  ETL LAYER (Extract, Transform, Load)               │
│  - Parse configuration file                         │
│  - Read source files (CSV, Excel, etc.)             │
│  - Validate data quality                            │
│  - Map columns → internal models                    │
│  - Transform and clean data                         │
│  - Load into SQLite database                        │
└─────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────┐
│  SQLITE DATABASE (Internal Architecture)            │
│  - Standardized schema                              │
│  - Optimized for analysis queries                   │
│  - Persistent storage                               │
│  - Single source of truth                           │
└─────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────┐
│  ANALYSIS ENGINE                                    │
│  - KPI calculations                                 │
│  - Statistical analysis                             │
│  - Performance metrics                              │
│  - Cross-referenced data queries                    │
└─────────────────────────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────┐
│  EXPORT LAYER                                       │
│  - Excel report generation                          │
│  - Multi-sheet workbooks                            │
│  - Formatted tables and charts                      │
│  - Configurable report templates                    │
└─────────────────────────────────────────────────────┘
```

### SQLite Database Schema (Internal Architecture)

The SQLite database serves as the **canonical internal data model** with the following structure:

**Core Tables:**
```sql
-- Product master data
CREATE TABLE products (
    sku TEXT PRIMARY KEY,
    description TEXT,
    category TEXT,
    family TEXT,
    dimensions_length REAL,
    dimensions_width REAL,
    dimensions_height REAL,
    weight REAL,
    abc_class TEXT,
    storage_requirements TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Order headers
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    order_date DATE,
    customer_id TEXT,
    status TEXT,
    priority TEXT,
    requested_ship_date DATE,
    actual_ship_date DATE,
    order_value REAL,
    total_weight REAL,
    total_volume REAL
);

-- Order lines
CREATE TABLE order_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT,
    sku TEXT,
    quantity INTEGER,
    price REAL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (sku) REFERENCES products(sku)
);

-- Picking operations
CREATE TABLE picking_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT,
    sku TEXT,
    requested_quantity INTEGER,
    picked_quantity INTEGER,
    zone TEXT,
    aisle TEXT,
    bay TEXT,
    level TEXT,
    operator_id TEXT,
    assigned_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT,
    equipment_used TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (sku) REFERENCES products(sku)
);

-- Replenishment operations
CREATE TABLE replenishments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT,
    quantity INTEGER,
    from_zone TEXT,
    from_aisle TEXT,
    from_bay TEXT,
    from_level TEXT,
    to_zone TEXT,
    to_aisle TEXT,
    to_bay TEXT,
    to_level TEXT,
    trigger_type TEXT,
    operator_id TEXT,
    requested_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT,
    stock_level_before INTEGER,
    stock_level_after INTEGER,
    FOREIGN KEY (sku) REFERENCES products(sku)
);

-- All inventory movements
CREATE TABLE movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movement_type TEXT, -- 'inbound', 'outbound', 'transfer', 'adjustment', 'return'
    sku TEXT,
    quantity INTEGER,
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
    FOREIGN KEY (sku) REFERENCES products(sku)
);

-- Derived/Calculated data (materialized views or tables)
CREATE TABLE product_performance (
    sku TEXT PRIMARY KEY,
    total_picks INTEGER,
    avg_pick_quantity REAL,
    last_pick_date DATE,
    pick_frequency_30d INTEGER,
    abc_velocity_class TEXT,
    FOREIGN KEY (sku) REFERENCES products(sku)
);

CREATE TABLE operator_performance (
    operator_id TEXT PRIMARY KEY,
    total_picks INTEGER,
    avg_pick_rate_per_hour REAL,
    total_replenishments INTEGER,
    avg_replenishment_time_minutes REAL,
    accuracy_rate REAL,
    last_activity_date DATE
);
```

**Indexing Strategy:**
- Indexes on all foreign keys
- Composite indexes on frequently queried columns (e.g., operator_id + date)
- Indexes on timestamp fields for time-based queries
- Indexes on location fields (zone, aisle, bay, level)

## Core Components

### 1. Internal Models (Fixed)

**Core Entities:**
- **Article**: SKU, description, dimensions, weight, categories
- **Location**: Zone, aisle, bay, level, type (storage, picking)
- **Stock**: Quantity, entry date, expiration date, lot/batch
- **Movement**: Type (in/out/transfer), date, operator
- **Order**: Lines, status, priority, customer
- **Operator**: Performance metrics, productivity

**Analysis Methods:**
- ABC analysis
- Inventory turnover rates
- Stock coverage
- Storage density
- Operator productivity
- Order fulfillment metrics
- Picking performance analysis
- Replenishment metrics
- Returns processing analysis
- Product performance analytics

### 2. Analysis Categories

#### A. Picking Performance Analysis

**Global Metrics:**
- Overall pick rate (lines/hour, units/hour)
- Order cycle time (average, median, percentiles)
- Picking accuracy rate
- On-time fulfillment rate
- Travel distance optimization
- Picks per hour per zone
- Peak capacity analysis
- Bottleneck identification

**Individual Metrics (Operator Level):**
- Individual pick rates by operator
- Operator accuracy rates
- Productivity trends over time
- Operator efficiency ranking
- Training needs assessment
- Exception handling performance
- Comparison to team averages
- Personal performance evolution

**Advanced Analytics:**
- Zone-wise picking performance
- Product category pick difficulty
- Optimal picking path analysis
- Congestion hotspots
- Equipment utilization (p carts, forklifts)
- Wave picking vs batch picking efficiency

#### B. Replenishment Performance Analysis

**Global Metrics:**
- Replenishment frequency (daily/weekly/monthly)
- Average time to replenish
- Stockout frequency and duration
- Replenishment accuracy
- Trigger point effectiveness
- Bulk-to-picker transfer efficiency
- Replenishment labor cost

**Individual Metrics:**
- Operator replenishment speed
- Individual accuracy rates
- Task completion time by operator
- Proactive vs reactive replenishment ratio
- Operator zone coverage efficiency

**Advanced Analytics:**
- Replenishment optimization opportunities
- Seasonal patterns in replenishment needs
- ABC classification replenishment patterns
- Space utilization after replenishment
- Predictive replenishment triggers

#### C. Returns Processing Analysis

**Global Metrics:**
- Return rate (by volume, value, % of orders)
- Return processing time
- Return categorization (damaged, wrong item, customer preference)
- Restocking success rate
- Return disposition (restock, scrap, return to vendor)
- Cost of returns processing
- Return reason analysis

**Individual Metrics:**
- Processing time by operator
- Accuracy of return categorization
- Restocking efficiency per operator
- Quality control accuracy

**Advanced Analytics:**
- Product return correlation
- Customer return patterns
- Seasonal return trends
- Return impact on inventory
- Root cause analysis (product quality, description accuracy, etc.)
- Vendor performance (returns by supplier)

#### D. Product Performance Analytics

**Inventory Performance:**
- ABC classification (by sales velocity, value, picks)
- Product turnover rates
- Dead stock identification
- Slow-moving inventory analysis
- Fast movers concentration
- Product lifespan analysis
- Seasonality patterns per product

**Picking Efficiency by Product:**
- Pick frequency by product
- Average pick quantity per product
- Product placement efficiency (fast movers access)
- Product size/weight vs picking performance
- Bulk vs split pick analysis
- Product grouping optimization

**Storage & Space:**
- Storage density by product category
- Space utilization efficiency
- Cubic utilization rate
- Product footprint analysis
- Vertical space optimization
- Product-to-location matching efficiency

**Product Lifecycle:**
- New product introduction performance
- Obsolescence detection
- Product phase-out analysis
- Promotional item performance
- Bundle/break-bulk efficiency

#### E. Cross-Category Analytics

**Operator Comprehensive Scorecard:**
- Overall productivity index (picking + replenishment + returns)
- Versatility score (cross-training effectiveness)
- Error-prone product/operator combinations
- Peak vs off-peak performance variance

**Product Operational Scorecard:**
- Total handling cost per product
- Labor cost per unit handled
- Storage + handling efficiency index
- High-maintenance product identification

### 3. Configuration System

The configuration file defines:
- Data source locations (file paths, database connections, APIs)
- Column mapping from source files to internal models
- Data transformation rules
- Business rules specific to each warehouse/client

Example Configuration Structure:
```yaml
# Data sources
sources:
  stock_file: "path/to/stock.csv"
  movements_file: "path/to/movements.xlsx"
  articles_file: "path/to/articles.csv"

# Column mapping: source → internal models
mapping:
  articles:
    sku_code: "REF_ARTICLE"
    description: "DESCRIPTION"
    weight_kg: "WEIGHT"
    category: "FAMILY"

  stock:
    location: "LOC_ID"
    quantity: "QTY"
    entry_date: "IN_DATE"

# Transformation rules
transformations:
  date_format: "DD/MM/YYYY"
  encoding: "UTF-8"
  delimiter: ";"

# Business rules
business_rules:
  picking_zones: ["A", "B", "C"]
  low_stock_threshold: 10
  abc_thresholds:
    class_a: 0.80
    class_b: 0.15
```

### 4. Available Data Sources

The system has access to the following data sources from the WMS:

#### A. Movement Records (Mouvements)
**Purpose:** Track all inventory movements in the warehouse

**Contains:**
- Movement ID, type (inbound/outbound/transfer/adjustment)
- Timestamps (creation, completion)
- Product SKU, quantity
- From/to locations (zones, aisles, bays, levels)
- Operator ID (if applicable)
- Reference documents (order number, receipt number, etc.)

**Enables:**
- Global throughput analysis
- Transfer efficiency metrics
- Movement patterns by zone
- Operator velocity analysis
- Peak activity identification

#### B. Picking Lines (Lignes de Picking)
**Purpose:** Detailed picking operations data

**Contains:**
- Pick line ID, order reference
- Product SKU, requested quantity, picked quantity
- Source location (zone, aisle, bay, level)
- Timestamps (assignment, start, completion)
- Operator ID
- Pick status (completed, cancelled, short pick)
- Equipment used (if available)

**Enables:**
- Picking performance analysis (global & individual)
- Order cycle time calculation
- Accuracy rate metrics
- Product pick frequency analysis
- Zone performance comparison
- Operator productivity tracking

#### C. Replenishment Reports (Rapports de Réapprovisionnement)
**Purpose:** Replenishment operations tracking

**Contains:**
- Replenishment ID, trigger type (manual/auto/min-stock)
- Product SKU, quantity moved
- From/to locations (bulk → picking)
- Timestamps (request, start, completion)
- Operator ID
- Status (pending, completed, cancelled)
- Stock level before/after

**Enables:**
- Replenishment frequency analysis
- Replenishment time metrics
- Stockout prevention analysis
- Operator efficiency (replenishment)
- Trigger effectiveness evaluation

#### D. Product Catalog (Catalogue des Produits)
**Purpose:** Master data for all products

**Contains:**
- Product SKU, description, barcode/EAN
- Dimensions (length, width, height)
- Weight (gross/net)
- Category, family, sub-family
- ABC classification
- Storage requirements (temperature, hazardous, etc.)
- Special handling requirements
- Supplier/vendor information

**Enables:**
- Product performance profiling
- ABC analysis
- Storage optimization recommendations
- Picking difficulty assessment
- Product grouping strategies

#### E. Order History (Historique des Commandes)
**Purpose:** Complete order records

**Contains:**
- Order ID, order date, order type
- Customer ID, shipping information
- Order lines (product SKU, quantity, price)
- Order status (created, picked, packed, shipped)
- Priority level, requested ship date
- Actual ship date, delivery date
- Order value, weight, volume

**Enables:**
- Order fulfillment analysis
- Customer demand patterns
- Seasonality analysis
- On-time delivery metrics
- Product velocity calculation
- Returns analysis (when combined with returns data)

---

**Data Derivation Strategy:**
*Some metrics are derived by combining these data sources:*
- **Stock levels** = Calculated from Movement Records (in - out)
- **Returns processing** = Cross-reference Order History with return-type Movements
- **Operator profiles** = Aggregate performance from Picking Lines + Replenishment Reports + Movements
- **Product lifecycle** = Analyze Product Catalog + Order History + Movement Records

## Data Processing Flow

### ETL Process (Extract, Transform, Load)

**Phase 1: EXTRACT**
1. Load configuration file (YAML/JSON)
2. Read source files based on configuration:
   - Movement records (CSV/Excel)
   - Picking lines (CSV/Excel)
   - Replenishment reports (CSV/Excel)
   - Product catalog (CSV/Excel)
   - Order history (CSV/Excel)

**Phase 2: TRANSFORM**
3. Data Validation:
   - Check file format and structure
   - Validate required columns
   - Verify data types
   - Detect missing or corrupted data

4. Data Mapping:
   - Apply column mapping from configuration
   - Transform column names to internal schema
   - Convert data types (strings to dates, numbers, etc.)
   - Apply business rules and transformations

5. Data Cleaning:
   - Handle missing values
   - Remove duplicates
   - Standardize formats (dates, text case, etc.)
   - Validate referential integrity

**Phase 3: LOAD**
6. Database Creation/Update:
   - Create SQLite database with standard schema (if not exists)
   - Clear existing data (optional, based on configuration)
   - Insert transformed data into SQLite tables
   - Create/update indexes for performance
   - Update derived/calculated tables

7. Data Verification:
   - Verify record counts match source
   - Check foreign key constraints
   - Validate data integrity
   - Generate loading statistics

### Analysis Process

8. **Run Analyses**:
   - Execute SQL queries against SQLite database
   - Calculate KPIs and metrics
   - Perform statistical analysis
   - Generate aggregations and groupings
   - Compute performance scores

### Export Process

9. **Excel Export**:
   - Create Excel workbook with multiple sheets
   - Format data with headers, styles, and number formats
   - Add charts and visualizations
   - Apply conditional formatting for insights
   - Generate summary sheets and detailed data sheets

### Report Structure (Excel Export)

**Typical Workbook Structure:**
```
Workbook: Wareflow_Analysis_YYYYMMDD.xlsx
├── Sheet 1: Summary Dashboard
│   - Key KPIs overview
│   - Performance indicators
│   - Charts and visualizations
├── Sheet 2: Picking Performance
│   - Global metrics
│   - Individual operator performance
│   - Zone-wise analysis
├── Sheet 3: Replenishment Analysis
│   - Frequency and timing metrics
│   - Trigger effectiveness
│   - Operator performance
├── Sheet 4: Product Performance
│   - ABC analysis
│   - Fast/slow movers
│   - Pick frequency by product
├── Sheet 5: Order Analysis
│   - Order fulfillment metrics
│   - Cycle time analysis
│   - On-time delivery rates
└── Sheet 6: Data Quality & Metadata
    - Record counts
    - Data freshness indicators
    - Processing timestamps
```

## Benefits

### Architecture Benefits
- **Flexibility**: Adapt to any WMS without code changes through configuration
- **Maintainability**: Bugs and features managed in code, not configuration
- **Reusability**: Same engine processes different warehouses/clients
- **Testability**: Stable SQLite schema enables reliable testing
- **Extensibility**: New analyses added as SQL queries and export templates

### SQLite Database Benefits
- **Portability**: Single file database, easy to backup and transfer
- **Performance**: Optimized for analytical queries with proper indexing
- **Zero Configuration**: No database server setup required
- **Cross-Platform**: Works on Windows, Linux, Mac
- **SQL Support**: Full power of SQL for complex analysis
- **ACID Compliant**: Data integrity guarantees
- **Scalability**: Handles millions of records efficiently

### Excel Export Benefits
- **User-Friendly**: Familiar interface for business users
- **Rich Visualization**: Charts, pivot tables, conditional formatting
- **Distribution**: Easy to share via email or cloud storage
- **Further Analysis**: Users can perform additional analysis in Excel
- **Presentation Ready**: Professional formatting for reports
- **No Software Installation**: Recipients don't need specialized software

### Workflow Benefits
- **Batch Processing**: Process large data volumes offline
- **Reproducibility**: Same analysis can be run multiple times
- **Audit Trail**: SQLite database maintains data history
- **Incremental Updates**: Can update database with new data
- **Multiple Analyses**: Run different analyses on same database
- **Performance**: Fast queries compared to spreadsheet-based analysis

## Use Cases

### Operational Excellence
- **Performance Monitoring**: Track picking, replenishment, and returns performance in real-time
- **Operator Evaluation**: Individual performance tracking for training and incentives
- **Bottleneck Identification**: Locate and resolve operational constraints
- **Continuous Improvement**: Data-driven optimization of warehouse processes

### Strategic Decision Making
- **Resource Allocation**: Optimize labor deployment based on demand patterns
- **Warehouse Layout Optimization**: Improve product placement based on pick frequency
- **Equipment Investment**: Decide on equipment needs based on utilization metrics
- **Capacity Planning**: Forecast space and labor requirements

### Product & Inventory Management
- **Dead Stock Elimination**: Identify and address non-moving inventory
- **ABC Classification**: Optimize storage and handling based on product velocity
- **Seasonality Planning**: Anticipate and prepare for seasonal variations
- **Product Lifecycle Management**: Monitor product introduction to obsolescence

### Multi-Environment Support
- **Multi-Warehouse**: Analyze multiple warehouses with different WMS
- **Multi-Client**: Serve different clients with specific data formats
- **Migration Support**: Compare old vs new WMS implementations
- **Benchmarking**: Compare performance across warehouses or time periods

## Project Status

Currently in design phase. The architecture is being defined to ensure maximum flexibility and maintainability.

## Next Steps

### Phase 1: Foundation
1. **Finalize SQLite Schema**: Define complete database structure with all tables, indexes, and constraints
2. **Design Configuration File**: Specify YAML/JSON format for data sources and column mapping
3. **Choose Technology Stack**: Select programming language and libraries (Python recommended: pandas, sqlite3, openpyxl)

### Phase 2: ETL Implementation
4. **Implement ETL Layer**:
   - Configuration file parser
   - File readers (CSV, Excel)
   - Data validation and cleaning
   - Data mapping and transformation
   - SQLite database loader

### Phase 3: Analysis Engine
5. **Implement Analysis Module**:
   - SQL query library for KPIs
   - Statistical analysis functions
   - Performance scoring algorithms
   - ABC analysis implementation
   - Trend analysis functions

### Phase 4: Excel Export
6. **Implement Export Layer**:
   - Excel workbook generator
   - Multi-sheet creation
   - Formatting and styling
   - Chart generation
   - Conditional formatting
   - Template system for customization

### Phase 5: Testing & Documentation
7. **Testing**:
   - Unit tests for ETL processes
   - Integration tests for analysis
   - Sample data sets for validation
8. **Documentation**:
   - User guide for configuration
   - API documentation
   - Sample reports
   - Troubleshooting guide

### Phase 6: Deployment
9. **Packaging**:
   - Executable or script for easy deployment
   - Configuration file templates
   - Sample data and examples
10. **Delivery**:
    - Installation guide
    - Training materials
    - Support documentation