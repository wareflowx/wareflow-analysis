# Wareflow Analysis - Complete Database Schema

## Current System Schema

All tables and relationships from the current Wareflow system.

---

## Table: produits (Global Product Catalog)

### Structure
```sql
CREATE TABLE produits (
    no_produit INTEGER PRIMARY KEY,    -- INTEGER (not TEXT!)
    nom_produit TEXT,
    description TEXT,
    classe_produit TEXT,
    categorie_1 TEXT,
    categorie_2 TEXT,
    categorie_3 TEXT,
    etat TEXT,                         -- Active/Inactive state
    configuration TEXT,
    ean_alternatif TEXT
);
```

### Key Characteristics
- **Global catalog**: Products are global (not warehouse-specific)
- **Primary Key**: INTEGER `no_produit` (not TEXT SKU)
- **Categories**: 3-level categorization (categorie_1, categorie_2, categorie_3)
- **No warehouse_id**: Products are global, not tied to warehouses

---

## Table: commandes (Orders)

### Structure
```sql
CREATE TABLE commandes (
    commande TEXT PRIMARY KEY,          -- TEXT identifier (not integer)
    type_commande TEXT,
    demandeur TEXT,
    destinataire TEXT,
    no_destinataire INTEGER,
    priorite INTEGER,
    vague TEXT,
    date_requise DATETIME,
    lignes INTEGER,                   -- Number of lines (COUNT)
    chargement TEXT,
    transporteur TEXT,
    etat_inferieur TEXT,              -- Lower status
    etat_superieur TEXT,              -- Higher status
    etat TEXT,
    statut_prepositionnement_max TEXT,
    statut_prepositionnement_actuel TEXT
);
```

### Key Characteristics
- **Primary Key**: TEXT `commande` (command ID)
- **Status fields**: 4 different status fields!
  - `etat_inferieur` (lower level)
  - ``etat_superieur`` (higher level)
  - `etat` (current status)
  - `statut_prepositionnement_max`
  - `statut_prepositionnement_actuel`
- **Has `destinataire`: References another entity (warehouse/customers?)

---

## Table: receptions (Receiving)

### Structure
```sql
CREATE TABLE receptions (
    no_reference INTEGER PRIMARY KEY,
    reception INTEGER,
    quantite_recue INTEGER,
    produit INTEGER,                   -- FK to produits.no_produit
    fournisseur TEXT,
    site TEXT,
    localisation_reception TEXT,
    date_reception DATETIME,
    utilisateur TEXT,
    etat TEXT,
    numero_lot REAL,
    date_expiration REAL,

    FOREIGN KEY (produit) REFERENCES produits(no_produit)
);
```

### Key Characteristics
- **Purpose**: Receiving operations (supplier deliveries)
- **Links**: References products table
- **Tracks**: Lots, expiration dates

---

## Table: mouvements (Movements)

### Structure
```sql
CREATE TABLE mouvements (
    oid INTEGER PRIMARY KEY,
    no_produit INTEGER,                -- FK to produits.no_produit
    nom_produit TEXT,
    type TEXT,                        -- Movement type
    site_source TEXT,
    zone_source TEXT,
    localisation_source TEXT,
    conteneur_source TEXT,
    site_cible TEXT,
    zone_cible TEXT,
    localisation_cible TEXT,
    conteneur_cible TEXT,
    quantite_uoi TEXT,                -- TEXT (not INTEGER)
    quantite INTEGER,                 -- Actual integer quantity
    unite TEXT,
    date_heure DATETIME,
    usager TEXT,                      -- Operator/user
    raison REAL,
    lot_expiration REAL,
    date_expiration REAL,
    date_heure_2 TEXT,

    FOREIGN KEY (no_produit) REFERENCES produits(no_produit)
);
```

### Key Characteristics
- **Product reference**: `no_produit` INTEGER (FK to produits)
- **Quantity handling**: TWO fields:
  - `quantite_uoi` TEXT (description of quantity?)
  - `quantity` INTEGER (actual numeric value)
- **Location hierarchy**: 4 levels + NULL handling
- **Multiple operators**: `usager` TEXT (can handle multiple people)
- **Time tracking**: `date_heure` DATETIME
- **Type field**: Movement type (picking, replenishment, return, etc.)

---

## Table Indexes

### Movement Indexes
- `idx_mouvements_produit` on `no_produit`
- `idx_mouvements_date` on `date_heure`
- `idx_mouvements_usager` on `usager`
- `idx_migrations_type` on `type`
- Location indexes on source and target

---

## Key Insights & Questions

### ✅ What's Now Clear

1. **Product structure is clear**:
   - Global catalog with INTEGER primary key
   - 3-level categorization
   - No warehouse_id in products

2. **Movement structure is clear**:
   - Hierarchical locations (4 levels)
   - Multiple operators supported
   - Time tracking via `date_heure`
   - Multiple quantity fields (TEXT description + INTEGER value)

3. **Reception data exists**:
   - Separate table for supplier deliveries
   - Links to products via `no_produit`

4. **Order status complexity**:
   - 4 different status fields
   - Status tracking at multiple levels

### ❓ Still Critical Questions

#### About Warehouses

**R1. Warehouse identification**: Where is warehouse information stored?
   - Is there a `warehouses` table somewhere?
   - Is warehouse info embedded in locations (site/zone)?
   - How do we distinguish Paris products from Lyon products?

#### About Stock Data

**R2. Stock data location**: Where is the stock data (inventories)?
   - Not in the schema provided
   - Is there a separate `stocks` table not shown here?
   - Or is stock calculated from movements?

#### About Performance Tracking

**R3. Time block identification**: How do you identify blocks of 15 minutes?
   - Movement timestamps exist in `date_heure`
   - But where is the "start/end" of task blocks?
   - Separate table? Logic applied to timestamps?

**R4. Task type per movement**: How do you know if a movement is picking vs replenishment?
   - Based on `type` field?
   - Derived from locations?
   - Based on separate data?

**R5. Multi-operator movements**: Multiple people on one movement:
   - How is this stored? Multiple rows?
   - Or just comma-separated names in `usager`?

**R6. Order detail**: Where are order line items stored?
   - Separate table?
   - Extracted from WMS differently?
   - Not needed for POC?

---

## Schema Analysis

### Relationships
```
products (global catalog)
    ↓
    ├── receptions (receiving operations)
    ├── mouvements (stock movements)
    └── order_lines (?) (not shown in schema)
```

### Data Flows Detected
1. **Products → Receptions**: Supplier deliveries
2. **Products → Movements: Stock movements
3. **Orders → Movements**: Order fulfillment (likely)

### Key Challenge: Missing Warehouse Context

The schema has NO explicit `warehouse_id` or `entrepot` field:
- Products are global (no warehouse)
- Movements have sites/zones but no warehouse identifier
- Orders have `destinataire` but not clear if it's a warehouse

**This is CRITICAL for multi-warehouse analysis!**

---

*Document created: 2025-01-20*
*Last updated: 2025-01-20*
*Status: Schema received - Critical questions remain*
