# Wareflow Analysis - Requirements & Answers

## User Requirements Documentation

All requirements and answers provided by the user for the Wareflow Analysis project.

---

## Product & Inventory Structure

### Product Data (Global Catalog)
- **SKU**: Globally unique product identifier across entire business
- **Scope**: Products are global (same product can exist in multiple warehouses)
- **Available fields**:
  - No. du produit (SKU) - Global product identifier
  - Nom - Product name/description
  - État - State (active/inactive)
  - Category - Product category
  - No dimensions, weight, or additional attributes available

### Stock Data (Per Warehouse)
- **Scope**: Individual per warehouse
- **Relationship**: One global product can have different stock levels in different warehouses
- **Implication**:
  - Need separate `stocks` table (not just products table)
  - Stock is warehouse-specific, product is global

**Architecture implication**:
```sql
-- Products table (global catalog)
CREATE TABLE products (
    sku TEXT PRIMARY KEY,
    description TEXT,
    category TEXT,
    state TEXT
);

-- Stocks table (per warehouse)
CREATE TABLE stocks (
    warehouse_id TEXT,
    sku TEXT,
    quantity REAL,
    location TEXT,
    PRIMARY KEY (warehouse_id, sku),
    FOREIGN KEY (sku) REFERENCES products(sku)
);
```

---

## Movement Data

### Movement Types
- **Picking** (préparateurs)
- **Replenishment** (réapprovisionnements)
- **Returns** (retours)
- Other movement types may exist

### Location Hierarchy
- **4 levels**: Site, Zone, Localisation, Conteneur
- **NULL handling**: Location levels can be NULL (not always present)

### Referential Integrity
- Products: Movements always reference known products in global catalog
- No orphan movements (no references to non-existent products)

### User/Operator Data
- **Multiple users**: Can be preparers, pickers, or multiple people per movement
- **Not single-person**: Single movement can involve multiple operators
- **User types**: Préparateurs, Caristes (pickers), potentially others

### Movement Volume
- **Volume**: 150,000 - 200,000 movement lines per MONTH
- **Daily average**: ~5,000 - 6,500 movements per day
- **Annual estimate**: ~1.8 - 2.4 million movements

---

## Order Data

### Order Lines
- **Field**: "Nombre de lignes" (Number of lines)
- **Meaning**: COUNT of lines, NOT "Nom de lignes"
- **Line details**: Available but require complex WMS extraction

---

## Analysis Requirements

### KPIs Required

#### 1. Task Performance Analysis
- **Metric**: Average performance per task type per unit of time
- **Task types**:
  - Picking (préparateurs)
  - Replenishment (réapprovisionnements)
  - Returns (retours)
- **Measurement method**: Time-tracking between tasks
- **Calculation**:
  - If time between tasks < 15 minutes → Start a "block"
  - Average time per block = Total block duration / Number of tasks in block

#### 2. Global Performance Metrics
- **Time periods**: Daily, weekly, monthly, yearly
- **Aggregate performance indicators

#### 3. Product Performance
- Individual product metrics
- Performance tracking over time

#### 4. ABC Placement Analysis
- Products classified as A, B, C
- Placement optimization

#### 5. Product Grouping/Clustering
- Group similar products
- Clustering analysis

---

## Data File Characteristics

### Movement Files
- **Size**: Large (150k-200k lines/month)
- **Other files**: Reasonable size

### Unknown Structure Details

Still need to clarify:
- Actual Excel file structure (column names, example rows)
- User identifier format
- Order file structure
- Stock data format
- Movement time tracking format

---

## Critical Architecture Implications

### Global Products + Warehouse-Specific Stocks

This structure has significant implications:

1. **Schema Design**:
   - One `products` table (global catalog)
   - One `stocks` table (warehouse-specific inventory)
   - Movements track warehouse-specific stock movements

2. **Analysis Approach**:
   - Product performance can be analyzed globally (across warehouses)
   - Stock levels are warehouse-specific
   - Movement analysis must include warehouse context

3. **Multi-Warehouse Comparison**:
   - Same product performance can be compared across warehouses
   - Stock levels differ by warehouse for same product
   - Movement patterns differ by location

### Performance Tracking Challenge

**Critical question**: Time tracking methodology not yet fully specified

**Potential approaches**:
- Movement timestamps exist but need to group into "blocks"
- Separate time tracking system (not in files mentioned yet)
- Need to understand how to identify task types from movement data

---

## Next Steps

### Phase 1: Critical Clarifications (REQUIRED)

Must clarify before POC:

1. **Stock data structure**: What fields exist in stock data? How is warehouse identified?

2. **Time tracking details**: How do we identify:
   - When a task block starts/ends?
   - Which task type each block represents?
   - Who worked on each block?

3. **File examples**: Need actual Excel file examples (3-5 rows) showing:
   - Products file
   - Movements file (with time tracking if possible)
   - Orders file
   - Stock file (if separate)

### Phase 2: POC Planning

Once critical clarifications received:

1. Design database schema (products + stocks + movements)
2. Configure excel-to-sql mappings
3. Implement core analyses (picking performance, product performance)
4. Generate first reports

---

*Document created: 2025-01-20*
*Last updated: 2025-01-20*
*Status: Partially defined - Critical unknowns remain*
