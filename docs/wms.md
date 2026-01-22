# Warehouse Management System (WMS) - Conceptual Modeling

**For wareflow-analysis CLI tool**

---

## The General Vision

A warehouse is **a physical space** where we **store products** to **move them to destinations**. These are the three fundamental pillars.

**wareflow-analysis** is a **CLI analytics tool** that helps warehouse managers understand what happened in their warehouse, identify problems, and make better decisions.

---

## The 4 Central Questions

**1. WHERE are things?** (Location)
- Which warehouse?
- Which zone?
- At what precise address?

**2. WHAT do we have?** (Products)
- Which product?
- How much do we have?
- In what condition (quality, lot, expiration)?

**3. WHEN does it arrive/leave?** (Timeline)
- When did it arrive?
- When does it need to ship?
- How long does it sit in storage?

**4. WHO does what?** (Actors)
- Who received it?
- Who stocked it?
- Who picked the order?
- Who replenished it?

---

## The 5 Fundamental Flows

### **Flow 1: Receiving (Inbound)**
```
Supplier → Receiving (quality control) → Stock putaway
```
**Needs**: Know what arrived, when, from whom, in what quantity, what quality, where to store it

### **Flow 2: Storage (Static)**
```
Product → Storage location
```
**Needs**: Know where each product is, how much, how long it's been there, if it expires

### **Flow 3: Replenishment (Internal)**
```
Storage zone → Picking zone
```
**Needs**: Know when to replenish, how much, who does it, from where to where

### **Flow 4: Order Picking (Outbound)**
```
Customer order → Picking → Packing → Shipping
```
**Needs**: Know what to prepare, where to find it, who prepares it, how long it takes, if it's complete

### **Flow 5: Adjustment (Correction)**
```
Error → Stock correction
```
**Needs**: Know why we adjust, what, who validates, difference between theoretical and actual

---

## Conceptual Entities

### **Spaces (Places)**
```
Warehouse → Zone → Aisle → Bay → Level → Container
```
**Needs**:
- Know where each product is stored
- Optimize travel paths (picking efficiency)
- Manage capacity (what space remains available)
- Separate zones (receiving, storage, picking, shipping)

### **Products (Items)**
```
Product → Quantity → Condition → Location
```
**Needs**:
- Uniquely identify each product
- Know how much we have (stock level)
- Know their rotation speed (ABC classification)
- Manage lots and expiration (perishables)
- Identify dead products (slow-moving, dead stock)

### **Movements (Actions)**
```
Type → Product → Quantity → Origin → Destination → Who → When
```
**Needs**:
- Full traceability of every movement
- History for analytics (performance, trends)
- Calculate current stock levels
- Identify errors and losses

### **Orders (Demands)**
```
Order → Customer → Order Lines → Products → Quantities → Status
```
**Needs**:
- Know what to ship to whom
- Track each order's status
- Measure fulfillment rate
- Calculate lead times
- Identify late orders

### **Operators (Actors)**
```
Operator → Actions → Performance
```
**Needs**:
- Know who did what
- Measure each person's performance (picks/hour, accuracy)
- Identify training needs
- Optimize resource allocation

---

## Key Relationships

### **Product → Location** (Many-to-Many)
A single product can be stored in multiple locations
A location can contain multiple products (mixing)
**Need**: Know quantity per location

### **Order → Products** (Many-to-Many)
One order contains multiple products
One product can be in multiple orders
**Need**: Intermediate table (order lines) with quantities

### **Movement → Order** (Many-to-One)
Multiple movements for one order (one per product)
One movement belongs to a single order
**Need**: Direct link to know "this pick is for this order"

### **Movement → Operator** (Many-to-One)
One operator performs multiple movements
One movement is done by one operator (or several)
**Need**: Track responsibility and measure performance

### **Receiving → Product** (Many-to-One)
One receiving contains multiple products
One product can be received multiple times
**Need**: Supplier traceability, lot, expiration

---

## Critical States

### **Stock States**
- **Available**: Ready to be sold
- **Allocated**: Reserved for an order (not yet physically moved)
- **Being picked**: Currently being prepared
- **Being replenished**: In transfer to picking zone

### **Order States**
- **Pending**: Not yet started
- **In progress**: Picking in progress
- **Ready**: Ready to ship
- **Shipped**: Has left
- **Cancelled**: Cancelled

### **Movement States**
- **Planned**: Scheduled but not executed
- **In progress**: Being executed
- **Completed**: Successfully finished
- **Cancelled**: Cancelled
- **Error**: Problem occurred

---

## Common Friction Points

### **Ghost Stock**
In system: 10 units
In reality: 8 units (2 lost, damaged, or stolen)
**Need**: Regular physical inventories + adjustments

### **Stock Fragmentation**
Same product stored in 3 different locations
**Need**: Consolidated view by product

### **Inefficient Picking**
A-class product stored at the back of the warehouse
**Need**: ABC placement + path optimization

### **Stockout**
We think we have 50 units, actually only 5
**Need**: Accurate calculation of available stock (theoretical - allocated)

### **Forgotten Expiration**
Expired product discovered when customer complains
**Need**: Expiration alerts + FEFO management (First Expired First Out)

---

# wareflow-analysis Features

## CLI Scope and Constraints

**This is a CLI tool, not a web application.**

**What it does:**
- Batch analysis of warehouse data
- Generate reports (Excel, CSV, JSON)
- Provide insights through terminal output
- Export data for external visualization

**What it doesn't do:**
- Real-time monitoring (use cron/scheduler instead)
- Interactive dashboards (use Grafana/Tableau instead)
- Live notifications (use email/Slack integrations instead)
- Direct warehouse operations (it's read-only analytics)

---

## Phase 1: Foundation Features (MVP - 3 months)

### **1. Data Import and Validation**

#### **a. Excel Import with excel-to-sql**
```
wareflow import [files...]

Features:
- Import multiple Excel files (products, orders, movements, receptions)
- Use excel-to-sql SDK for ETL
- Value mapping (French WMS codes → standard values)
- Calculated columns (derived fields)
- Data validation (type checks, required fields)
- Incremental import (only new/changed data)
- Progress indication (with rich CLI)

Data required:
- produits.xlsx
- commandes.xlsx
- mouvements.xlsx
- receptions.xlsx
```

#### **b. Data Validation Suite**
```
wareflow validate

Checks performed:
✓ All required files present
✓ All required columns exist
✓ Data types are correct
✓ No null values in required fields
✓ Referential integrity (FKs valid)
✓ No negative quantities
✓ Dates are valid
✓ No duplicate primary keys

Output:
- Validation summary (errors, warnings, info)
- Detailed error report per file
- Exit code 0 if valid, 1 if errors

Example output:
  ✓ produits.xlsx: 1,250 rows validated
  ✗ commandes.xlsx: 12 errors
    - Row 45: date_commande is null
    - Row 78: no_commande duplicate
    - Row 102: client_id references non-existent client
  ⚠ mouvements.xlsx: 5 warnings
    - 3 rows have empty usager field
```

#### **c. Configuration Management**
```
wareflow config init
wareflow config set dead_stock_days 90
wareflow config set abc_top_percentage 20
wareflow config get dead_stock_days

Configuration file: wareflow.yaml
```

```yaml
# wareflow.yaml
dead_stock:
  threshold_days: 90

abc:
  top_percentage: 20
  medium_percentage: 50

export:
  default_format: excel
  include_charts: true

import:
  files:
    - data/produits.xlsx
    - data/commandes.xlsx
    - data/mouvements.xlsx
    - data/receptions.xlsx
```

---

### **2. Data Inspection and Exploration**

#### **a. Database Status**
```
wareflow status

Output:
Database: wareflow.db (245 MB)
Last import: 2024-01-15 14:30

Tables:
  ✓ produits        1,250 rows
  ✓ commandes       3,420 rows
  ✓ mouvements     45,230 rows
  ✓ receptions      2,100 rows

Data quality: 98.5% (based on validation)

Time range:
  From: 2023-01-01
  To:   2024-01-15
```

#### **b. Data Inspection Commands**
```
wareflow inspect products
wareflow inspect product --sku="PROD-001"
wareflow inspect orders
wareflow inspect order --id=12345
wareflow inspect movements --after="2024-01-01"
wareflow inspect receptions --supplier="ACME Corp"

Features:
- View sample data (first 10 rows)
- Filter by any field
- Sort by any field
- Export inspection results
```

#### **c. Search and Query**
```
wareflow find product "PROD-001"
wareflow find movements --product="PROD-001" --type="sortie"
wareflow find orders --status="late"
wareflow find products --category="Electronics"

Features:
- Quick search by ID or name
- Filter by multiple criteria
- Show matching results in table format
- Export search results
```

---

### **3. Core Analytics (Descriptive)**

#### **a. Global Overview**
```
wareflow analyze overview

Output:
╔════════════════════════════════════════════════════════╗
║              WAREHOUSE ANALYSIS OVERVIEW               ║
╠════════════════════════════════════════════════════════╣
║ Period: 2023-01-01 to 2024-01-15 (380 days)           ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║ PRODUCTS                              ║
║   Total products:           1,250     ║
║   Active products:          1,180     ║
║   Products with stock:        980     ║
║   Dead stock (>90 days):       45     ║
║                                                        ║
║ ORDERS                                 ║
║   Total orders:             3,420     ║
║   Completed orders:         3,180     ║
║   Pending orders:             180     ║
║   Late orders:                45     ║
║   Fulfillment rate:          93.0%    ║
║                                                        ║
║ MOVEMENTS                              ║
║   Total movements:          45,230     ║
║   Inbound (receiving):       8,420     ║
║   Outbound (shipping):      28,150     ║
║   Transfers:                 5,340     ║
║   Adjustments:               3,320     ║
║                                                        ║
║ PERFORMANCE                            ║
║   Avg orders/day:              9.0     ║
║   Avg lead time:              2.3 days ║
║   Avg pick rate:            45 items/h ║
╚════════════════════════════════════════════════════════╝
```

#### **b. Dead Stock Analysis**
```
wareflow analyze dead-stock

Output:
╔════════════════════════════════════════════════════════╗
║                    DEAD STOCK ANALYSIS                  ║
╠════════════════════════════════════════════════════════╣
║ Threshold: 90 days without movement                    ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║ Summary:                                               ║
║   Dead stock products:              45                ║
║   Total quantity:                  3,420 units        ║
║   Estimated value:              $45,230               ║
║   Storage cost/year:           $4,520               ║
║                                                        ║
║ Top 10 Dead Stock Products:                           ║
║ ┌──────────┬──────────┬────────┬─────────┬──────────┐┐
║ │ SKU      │ Last Mov.│ Qty    │ Value   │ Action   ││
║ ├──────────┼──────────┼────────┼─────────┼──────────┤│
║ │PROD-001  │ 245 days │  150   │ $4,500  │ LIQUIDATE││
║ │PROD-002  │ 312 days │   75   │ $2,250  │ DESTROY  ││
║ │PROD-003  │ 198 days │  200   │ $3,800  │ DONATE   ││
║ │PROD-004  │ 175 days │   50   │   $750  │ PROMOTE  ││
║ └──────────┴──────────┴────────┴─────────┴──────────┘│
║                                                        ║
║ Recommendations:                                       ║
║   1. Liquidate 15 products (potential: $12,000)       ║
║   2. Destroy 8 expired products                       ║
║   3. Donate 10 products (tax deduction)               ║
║   4. Promote 12 products (clearance sale)             ║
║                                                        ║
║ Potential savings: $45,230 + $4,520/year = $49,750   ║
╚════════════════════════════════════════════════════════╝

Export to: dead-stock-report-2024-01-15.xlsx
```

#### **c. ABC Classification**
```
wareflow analyze abc

Output:
╔════════════════════════════════════════════════════════╗
║                  ABC CLASSIFICATION                    ║
╠════════════════════════════════════════════════════════╣
║ Method: Pareto (80/20 rule) on last 90 days           ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║ Classification:                                        ║
║   ┌─────────┬──────────┬────────────┬──────────────┐│
║   │ Class   │ Products │ Movements  │   % Moves    ││
║   ├─────────┼──────────┼────────────┼──────────────┤│
║   │ A       │     250  │    36,184  │     80.0%    ││
║   │ B       │     375  │     6,785  │     15.0%    ││
║   │ C       │     625  │     2,261  │      5.0%    ││
║   └─────────┴──────────┴────────────┴──────────────┘│
║                                                        ║
║ Class A (High priority):                              ║
║   Store in: Prime picking locations (easy access)     ║
║   Strategy: Keep well-stocked, monitor daily          ║
║                                                        ║
║ Class B (Medium priority):                            ║
║   Store in: Secondary locations                       ║
║   Strategy: Regular replenishment                     ║
║                                                        ║
║ Class C (Low priority):                               ║
   Store in: Remote areas                                ║
║   Strategy: Order on demand, minimize stock           ║
║                                                        ║
║ Top 20 Class A Products:                              ║
║   ┌──────────┬─────────────┬──────────┐              ║
║   │ SKU      │ Picks (90d) │   % Total│              ║
║   ├──────────┼─────────────┼──────────┤              ║
║   │ PROD-A01 │      2,450  │    5.4%  │              ║
║   │ PROD-A02 │      1,890  │    4.2%  │              ║
║   │ PROD-A03 │      1,650  │    3.6%  │              ║
║   └──────────┴─────────────┴──────────┘              ║
╚════════════════════════════════════════════════════════╝
```

#### **d. Order Fulfillment Analysis**
```
wareflow analyze orders

Output:
╔════════════════════════════════════════════════════════╗
║              ORDER FULFILLMENT ANALYSIS                ║
╠════════════════════════════════════════════════════════╣
║ Period: Last 30 days                                   ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║ Fulfillment Metrics:                                   ║
║   Total orders:                    450                ║
║   Completed:                       418  (92.9%)      ║
║   Partial:                          25  ( 5.6%)      ║
║   Backordered:                       7  ( 1.5%)      ║
║                                                        ║
║ First Pick Fulfillment:                                ║
║   Fulfilled on first pick:           85.3%            ║
║   Required second pick:              12.1%            ║
║   Required 3+ picks:                  2.6%            ║
║                                                        ║
║ Lead Time:                                             ║
║   Average:                         2.3 days           ║
║   Median:                          1.8 days           ║
║   P95:                              5.2 days           ║
║   P99:                              8.1 days           ║
║                                                        ║
║ Late Orders:                                           ║
║   Total late orders:                45                ║
║   Late rate:                        10.0%             ║
║   Avg delay:                        1.8 days          ║
║                                                        ║
║ Problems by Product:                                   ║
║   ┌──────────┬──────────┬─────────────┐              ║
║   │ Product  │ Backorders│   Reason    │              ║
║   ├──────────┼──────────┼─────────────┤              ║
║   │ PROD-X01 │        8  │ Out of stock│              ║
║   │ PROD-X02 │        5  │ Low stock   │              ║
║   │ PROD-X03 │        3  │ Damaged     │              ║
║   └──────────┴──────────┴─────────────┘              ║
╚════════════════════════════════════════════════════════╝
```

---

### **4. Export and Reporting**

#### **a. Excel Report Generation**
```
wareflow export report --output=warehouse-report.xlsx

Features:
- Multi-sheet workbook
- Professional formatting
- Charts and graphs
- Executive summary
- Detailed data sheets

Sheets:
1. Summary (KPIs dashboard)
2. Products (ABC, dead stock)
3. Orders (fulfillment, lead times)
4. Movements (by type, by zone)
5. Operators (performance rankings)
6. Recommendations (action items)
```

#### **b. Multiple Export Formats**
```
wareflow export dead-stock --format=excel --output=dead-stock.xlsx
wareflow export dead-stock --format=csv --output=dead-stock.csv
wareflow export dead-stock --format=json --output=dead-stock.json
wareflow export dead-stock --format=markdown --output=dead-stock.md
wareflow export dead-stock --format=pdf --output=dead-stock.pdf
```

#### **c. Custom Reports**
```
wareflow export custom --sections="overview,deadstock,abc" --period=30d

Features:
- Choose which sections to include
- Define time periods
- Filter by category, zone, etc.
- Add custom title/subtitle
- Include/exclude charts
```

---

## Phase 2: Enhanced Analytics (3-6 months)

### **5. Period-over-Period Comparison**

#### **a. Time Comparison**
```
wareflow compare --period1="2023-12" --period2="2024-01"

Output:
╔════════════════════════════════════════════════════════╗
║            PERIOD-OVER-PERIOD COMPARISON               ║
╠════════════════════════════════════════════════════════╣
║ Comparing: December 2023 vs January 2024               ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║ Orders:                                                ║
║   Dec 2023:                    420              │
║   Jan 2024:                    450              │
║   Change:        +30  (+7.1%)  ████               ║
║                                                        ║
║ Fulfillment Rate:                                     ║
║   Dec 2023:                    91.2%            ║
║   Jan 2024:                    92.9%            ║
║   Change:        +1.7%        ████               ║
║                                                        ║
║ Dead Stock:                                           ║
║   Dec 2023:                     42              │
║   Jan 2024:                     45              │
║   Change:         +3  (+7.1%)  ████               ║
║                                                        ║
║ Avg Lead Time:                                        ║
║   Dec 2023:                    2.5 days         ║
║   Jan 2024:                    2.3 days         ║
║   Change:        -0.2         ████               ║
╚════════════════════════════════════════════════════════╝
```

---

### **6. Advanced Product Analytics**

#### **a. Product Performance Details**
```
wareflow analyze products --sku="PROD-001"

Output:
╔════════════════════════════════════════════════════════╗
║              PRODUCT PERFORMANCE REPORT                 ║
╠════════════════════════════════════════════════════════╣
║ Product: PROD-001 - Widget A                          ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║ Classification:                                        ║
║   ABC Class:                       A                  ║
║   Velocity:                       High               ║
║   Category:                       Electronics         ║
║                                                        ║
║ Stock Status:                                          ║
║   Current stock:                   150 units          ║
║   Avg monthly consumption:          45 units          ║
║   Months of supply:                 3.3               ║
║   Last movement:                    2 days ago        ║
║                                                        ║
║ Movement History (90 days):                            ║
║   Total picks:                     420                ║
║   Avg picks/day:                    4.7               ║
║   Total quantity:                  1,890 units        ║
║   Avg quantity/pick:                4.5 units         ║
║                                                        ║
║ Storage:                                               ║
║   Primary location:               Zone A-12-03        ║
║   Secondary locations:            Zone B-05-01        ║
║   Placement:                       Optimal ✓         ║
║                                                        ║
║ Recommendations:                                       ║
║   ✓ Stock level appropriate                           ║
║   ✓ Product in optimal location                       ║
║   ✓ No action needed                                  ║
╚════════════════════════════════════════════════════════╝
```

#### **b. Slow-Moving Inventory**
```
wareflow analyze slow-moving --threshold=90

Output:
Products with no movement in 90+ days, sorted by value
```

---

### **7. Basic Operator Performance**

#### **a. Operator Rankings**
```
wareflow analyze operators

Output:
╔════════════════════════════════════════════════════════╗
║              OPERATOR PERFORMANCE RANKINGS              ║
╠════════════════════════════════════════════════════════╣
║ Period: Last 30 days                                   ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║ Top Performers:                                        ║
║   ┌────────────┬──────────┬──────────┬────────────┐   ║
║   │ Operator   │  Picks   │  Rate    │  Accuracy  │   ║
║   ├────────────┼──────────┼──────────┼────────────┤   ║
║   │ John Doe   │    2,450 │ 52/hour  │    99.2%   │   ║
║   │ Jane Smith │    2,180 │ 48/hour  │    98.7%   │   ║
║   │ Bob Wilson │    1,920 │ 43/hour  │    97.5%   │   ║
║   └────────────┴──────────┴──────────┴────────────┘   ║
║                                                        ║
║ Performance Distribution:                              ║
║   Above target (≥40 picks/hour):      8 operators     ║
║   At target (30-40 picks/hour):        12 operators   ║
║   Below target (<30 picks/hour):        3 operators   ║
║                                                        ║
║ Needs Training:                                        ║
║   - Operator #3: Low accuracy (94.2%)                 ║
║   - Operator #7: Low speed (25 picks/hour)            ║
╚════════════════════════════════════════════════════════╝

Note: Based on TEXT field in mouvements table.
Requires consistent operator naming for accurate results.
```

---

### **8. Inventory Analytics**

#### **a. Expiration Tracking**
```
wareflow analyze expiration

Output:
Products expiring within 90 days, sorted by urgency
```

#### **b. Lot Tracking**
```
wareflow analyze lots

Output:
Lot rotation analysis, FEFO compliance
```

---

## Phase 3: Planning and Optimization (6-12 months)

### **9. Capacity Planning**

#### **a. Storage Capacity Analysis**
```
wareflow analyze capacity

Output:
╔════════════════════════════════════════════════════════╗
║              STORAGE CAPACITY ANALYSIS                  ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║ Current Utilization:                                   ║
║   Zone A (Picking):      85% full  ████████████░░     ║
║   Zone B (Storage):      72% full  ████████░░░░░░     ║
║   Zone C (Bulk):         45% full  █████░░░░░░░░░     ║
║   Overall:               67% full  ███████░░░░░░░     ║
║                                                        ║
║ Projections:                                           ║
║   Current growth rate:         +5%/month              ║
║   Estimated full capacity:     8 months               ║
║   Recommended action:          Plan expansion         ║
║                                                        ║
║ Optimization Opportunities:                           ║
║   1. Move 45 C-class items to Zone C (save 15%)      ║
║   2. Consolidate fragmented stock (save 10%)         ║
║   3. Remove dead stock (save 5%)                      ║
║   Potential space savings: 30%                        ║
╚════════════════════════════════════════════════════════╝
```

---

### **10. Simple Forecasting**

#### **a. Demand Forecasting (Simple)**
```
wareflow forecast demand --sku="PROD-001" --days=30

Output:
╔════════════════════════════════════════════════════════╗
║                 DEMAND FORECAST (30 days)               ║
╠════════════════════════════════════════════════════════╣
║ Product: PROD-001                                      ║
║ Method: 30-day moving average                          ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║ Historical Average (last 30 days):                     ║
║   Daily demand:                    4.7 units/day      ║
║   Monthly demand:                 141 units/month     ║
║                                                        ║
║ Forecast (next 30 days):                               ║
║   Expected demand:                141 units           ║
║   Min (historical):                98 units           ║
║   Max (historical):                184 units          ║
║                                                        ║
║ Stock Recommendation:                                  ║
║   Current stock:                   150 units          ║
║   Forecasted consumption:          141 units          ║
║   Remaining after 30 days:          9 units           ║
║   Status:                          ⚠ LOW STOCK        ║
║   Action:          Reorder now (min 200 units)        ║
╚════════════════════════════════════════════════════════╝
```

---

### **11. Scheduled Reports**

#### **a. Automated Reporting (Cron)**
```
# Cron job example
0 8 * * 1 wareflow export report --output=weekly-report-$(date +%Y%m%d).xlsx --email=manager@company.com

Features:
- Daily/weekly/monthly automated reports
- Email output
- Slack integration (webhook)
- Custom schedule
```

---

## Phase 4: Advanced Features (12+ months)

### **12. Multi-Warehouse Support**

#### **a. Warehouse Comparison**
```
wareflow analyze warehouses --compare

Output:
Compare KPIs across multiple warehouses
```

---

### **13. Advanced Analytics**

#### **a. Rule-Based Optimization**
```
wareflow optimize placement

Output:
Product placement recommendations based on ABC analysis
```

#### **b. Statistical Anomaly Detection**
```
wareflow detect anomalies

Output:
Identify outliers using z-score analysis (not ML)
```

---

## Not Included (Out of Scope)

### **Real-time Features**
- ❌ Real-time alerts (use scheduled reports instead)
- ❌ Live dashboards (use external tools)
- ❌ Streaming data (CLI is batch-oriented)

### **Interactive UI**
- ❌ Ad-hoc query builder (use SQL directly)
- ❌ Interactive dashboards (use Grafana/Tableau)
- ❌ Drag-and-drop report builder

### **Machine Learning**
- ❌ Anomaly detection ML (use rule-based instead)
- ❌ Demand forecasting ML (use moving averages instead)
- ❌ Intelligent optimization (use heuristics instead)

### **Operational Features**
- ❌ Direct warehouse operations (this is analytics only)
- ❌ Real-time stock updates (read-only)
- ❌ Task assignment to operators

---

## Data Prerequisites

### **Critical Data Requirements**

For each feature, specific data is required:

```
✓ Dead Stock Analysis:
  - Last movement date per product
  - Current stock quantity
  - Product value (optional but recommended)

✓ ABC Classification:
  - Movement history (last 90 days minimum)
  - Quantity per movement
  - Product IDs

✓ Order Fulfillment:
  - Order status
  - Order dates (creation, completion)
  - Order lines (products per order)

⚠ Operator Performance (Limited):
  - Operator name/ID in movements table
  - Movement dates
  - Note: TEXT field limits accuracy

⚠ Picking Route Analysis (Limited):
  - Movement zones
  - Order ID (currently missing in schema)

❌ Lead Time Decomposition (Not available):
  - Timestamps per stage (receiving, putaway, etc.)
  - Only global lead time available

❌ Warehouse Comparison (Not available):
  - Requires warehouse_id in all tables
  - Single warehouse only in current schema
```

### **Current Schema Limitations**

```
Missing critical fields:
  - No order_id in mouvements (can't link picks to orders)
  - No order_lines table (can't see products per order)
  - No warehouse_id (single warehouse only)
  - No stocks table (can't track warehouse-specific stock)
  - No operators table (only TEXT field in mouvements)

Impact:
  - 30% of planned features are partially limited
  - 20% of planned features are blocked
  - Recommendations: Phase schema updates
```

---

## Technical Complexity Indicators

Each feature is marked with complexity level:

**🟢 Simple** (SQL queries, basic aggregations)
- Dead Stock Analysis
- ABC Classification
- Overview Statistics

**🟡 Medium** (Multiple joins, window functions)
- Order Fulfillment Analytics
- Period-over-Period Comparison
- Operator Performance

**🟠 Complex** (Statistical calculations, forecasting)
- Demand Forecasting
- Capacity Planning
- Anomaly Detection

**🔴 Advanced** (Machine Learning, optimization)
- Intelligent Product Placement
- Dynamic Reordering
- (Phase 4 features)

---

## Implementation Priority Matrix

```
High Impact, Low Complexity (DO FIRST):
  ✓ Data Validation
  ✓ Dead Stock Analysis
  ✓ ABC Classification
  ✓ Overview Statistics
  ✓ Excel Export

High Impact, High Complexity (DO SECOND):
  ✓ Order Fulfillment Analytics
  ✓ Period-over-Period Comparison
  ✓ Capacity Planning
  ✓ Simple Forecasting

Low Impact, Low Complexity (DO WHEN NEEDED):
  ○ Data Inspection Commands
  ○ Search/Query Features
  ○ Configuration Management

Low Impact, High Complexity (DEFER):
  ◌ ML Anomaly Detection
  ◌ Advanced Optimization
  ◌ Intelligent Product Placement
```

---

## Summary

**wareflow-analysis** is a **pragmatic CLI analytics tool** focused on:

1. **Descriptive analytics first** (what happened)
2. **Diagnostic analytics second** (why did it happen)
3. **Predictive analytics later** (what will happen - simple methods only)
4. **Prescriptive analytics last** (what should we do - recommendations only)

**Not a replacement for:**
- Full WMS (operational system)
- Real-time monitoring tools
- Machine learning platforms
- Interactive dashboards

**Designed for:**
- Batch analysis of warehouse data
- Generating actionable insights
- Exporting reports for stakeholders
- Supporting data-driven decisions

**Realistic scope for first year:**
- Phase 1: Foundation (3 months)
- Phase 2: Enhanced analytics (3 months)
- Phase 3: Planning and optimization (6 months)

This is a complete, practical, and achievable analytics tool for warehouse management.
