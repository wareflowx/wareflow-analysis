# Analyses Catalog

## Overview

This document provides a comprehensive catalog of all available analyses in the Wareflow SaaS platform. Analyses are organized by category and include data requirements, configuration options, and output formats.

## Analysis Categories

- **Flux Analyses**: Movement and operational flow analysis
- **Personnes Analyses**: User and team productivity analysis
- **Produits Analyses**: Product and inventory analysis
- **Commandes Analyses**: Order fulfillment analysis
- **Fournisseurs Analyses**: Supplier performance analysis
- **Custom Analyses**: User-defined extensions

---

## 1. Flux Analyses (Movement & Operations)

### 1.1 Temporal Flux Analysis

**ID**: `flux-temporal`
**Category**: `flux`
**Version**: `1.0.0`

**Description**: Analyze movement patterns over time to identify trends, seasonality, and operational patterns.

**Data Requirements**:
- Tables: `mouvements`
- Columns: `no_produit`, `type`, `quantite`, `date_heure`
- Min rows: 100
- Date range: 30+ days recommended

**Configuration**:
```typescript
{
  dateRange: {
    start: Date,      // Inclusive
    end: Date,        // Inclusive
    preset: 'last-30-days' | 'last-90-days' | 'this-year' | 'custom'
  },
  granularity: 'day' | 'week' | 'month' | 'quarter',
  groupBy: 'type' | 'zone' | 'usager' | null
}
```

**Output**:
- Movement volume over time
- Trend analysis (growth/decline)
- Seasonal patterns
- Day-of-week and hour-of-day heatmaps
- Comparison with previous period

**Visualization**:
- Line chart: Volume over time
- Heatmap: Activity by day/hour
- Bar chart: Comparison with previous period

---

### 1.2 Spatial Flux Analysis

**ID**: `flux-spatial`
**Category**: `flux`
**Version**: `1.0.0`

**Description**: Analyze movement patterns across warehouse locations to optimize space utilization.

**Data Requirements**:
- Tables: `mouvements`
- Columns: `zone_source`, `zone_cible`, `localisation_source`, `localisation_cible`, `quantite`
- Min rows: 500

**Configuration**:
```typescript
{
  level: 'site' | 'zone' | 'location',
  movementType: 'all' | 'inbound' | 'outbound' | 'transfer',
  topN: number  // Top N locations to show
}
```

**Output**:
- Heatmap of movements by zone
- Top source/destination locations
- Movement distance analysis
- Bottleneck identification
- Space utilization recommendations

**Visualization**:
- Heatmap: Color-coded zones by movement volume
- Network diagram: Source → destination flows
- Bar chart: Top locations

---

### 1.3 Operational Flux Analysis

**ID**: `flux-operational`
**Category**: `flux`
**Version**: `1.0.0`

**Description**: Analyze operational efficiency including throughput, cycle times, and resource utilization.

**Data Requirements**:
- Tables: `mouvements`, `commandes`
- Columns: `date_heure`, `usager`, `type`, `quantite`
- Min rows: 500

**Configuration**:
```typescript
{
  timeWindow: {
    start: Date,
    end: Date
  },
  metrics: [
    'throughput',      // Movements per hour
    'cycleTime',       // Time to complete operations
    'utilization',     // Resource utilization
    'errors'           // Error/rejection rate
  ]
}
```

**Output**:
- Average throughput (movements/hour)
- Peak and off-peak analysis
- Cycle time distribution
- Resource utilization
- Error rate by operation type

**Visualization**:
- Line chart: Throughput over time
- Histogram: Cycle time distribution
- Gauge: Resource utilization
- Pie chart: Error breakdown

---

## 2. Personnes Analyses (Users & Teams)

### 2.1 Productivity Analysis

**ID**: `personnes-productivity`
**Category**: `personnes`
**Version**: `1.0.0`

**Description**: Analyze individual and team productivity to identify top performers and training needs.

**Data Requirements**:
- Tables: `mouvements`
- Columns: `usager`, `date_heure`, `quantite`, `type`
- Min rows: 100

**Configuration**:
```typescript
{
  dateRange: {
    start: Date,
    end: Date
  },
  metrics: {
    movements: boolean,    // Total movements
    quantity: boolean,     // Total quantity moved
    speed: boolean,        // Movements per hour
    accuracy: boolean      // Error rate
  },
  groupBy: 'individual' | 'team' | 'none'
}
```

**Output**:
- Movements per user
- Total quantity handled per user
- Movements per hour (speed)
- Error rate per user
- Comparison with team average
- Performance ranking

**Visualization**:
- Bar chart: Movements by user
- Scatter plot: Speed vs accuracy
- Leaderboard: Top performers
- Box plot: Distribution comparison

---

### 2.2 Team Analysis

**ID**: `personnes-teams`
**Category**: `personnes`
**Version**: `1.0.0`

**Description**: Analyze team dynamics, workload distribution, and collaboration patterns.

**Data Requirements**:
- Tables: `mouvements`, `commandes`
- Columns: `usager`, `demandeur`, `date_heure`
- Min rows: 200

**Configuration**:
```typescript
{
  teamDefinition: {
    teams: {
      [teamName]: string[]  // team -> user IDs
    }
  },
  dateRange: {
    start: Date,
    end: Date
  }
}
```

**Output**:
- Workload distribution across teams
- Team productivity comparison
- Collaboration patterns (who works on same orders)
- Team size optimization recommendations
- Cross-training opportunities

**Visualization**:
- Stacked bar chart: Workload by team
- Network diagram: Collaboration network
- Radar chart: Team comparison
- Heatmap: Team activity over time

---

### 2.3 Performance Analysis

**ID**: `personnes-performance`
**Category**: `personnes`
**Version**: `1.0.0`

**Description**: Deep dive into individual performance trends, improvement patterns, and training needs.

**Data Requirements**:
- Tables: `mouvements`
- Columns: `usager`, `date_heure`, `quantite`, `type`
- Min rows: 500 per user (recommended)

**Configuration**:
```typescript
{
  userId: string,
  dateRange: {
    start: Date,
    end: Date
  },
  compareWith: 'team' | 'all' | 'top-performer',
  metrics: ['trend', 'consistency', 'improvement', 'ranking']
}
```

**Output**:
- Performance trend over time
- Consistency metrics (variance)
- Improvement rate
- Ranking within team
- Strengths and weaknesses
- Training recommendations

**Visualization**:
- Line chart: Performance over time
- Box plot: Distribution comparison
- Radar chart: Skill breakdown
- Table: Ranking and metrics

---

## 3. Produits Analyses (Products & Inventory)

### 3.1 ABC Classification

**ID**: `abc-classification`
**Category**: `produits`
**Version**: `1.0.0`

**Description**: Classify products by importance using Pareto principle (80/20 rule) for inventory optimization.

**Data Requirements**:
- Tables: `produits`, `mouvements`
- Columns: `no_produit`, `nom_produit`, `type`, `quantite`, `date_heure`
- Min rows: 100

**Configuration**:
```typescript
{
  lookbackDays: number,           // Analysis period (default: 90)
  classBoundaries: [number, number],  // A/B and B/C thresholds (default: [20, 50])
  includeInactive: boolean,       // Include products without movements
  metric: 'movements' | 'quantity' | 'value'  // What to measure
}
```

**Output**:
- Product classification (A/B/C)
- Movement/value contribution per class
- Top products per class
- Class summary statistics
- Storage recommendations

**Visualization**:
- Bar chart: Cumulative distribution
- Pie chart: Class breakdown
- Table: Product classification with color-coding

---

### 3.2 Product Lifecycle Analysis

**ID**: `produits-lifecycle`
**Category**: `produits`
**Version**: `1.0.0`

**Description**: Analyze product lifecycle from introduction to decline to identify obsolete products and trends.

**Data Requirements**:
- Tables: `produits`, `mouvements`
- Columns: `no_produit`, `date_heure`, `quantite`
- Min rows: 500
- Time span: 6+ months recommended

**Configuration**:
```typescript
{
  dateRange: {
    start: Date,
    end: Date
  },
  lifecycleStages: {
    introduction: number,   // Days since first movement
    growth: number,         // Growth threshold %
    maturity: number,       // Stable period threshold %
    decline: number         // Decline threshold %
  }
}
```

**Output**:
- Product lifecycle stage (introduction, growth, maturity, decline)
- Movement trends per product
- Obsolete product identification
- New product performance
- Seasonal pattern detection

**Visualization**:
- Line chart: Product movement trends
- Bubble chart: Products by lifecycle stage
- Table: Products by lifecycle stage

---

### 3.3 Stock Analysis

**ID**: `produits-stock`
**Category**: `produits`
**Version**: `1.0.0`

**Description**: Analyze stock levels, turnover, and coverage to optimize inventory management.

**Data Requirements**:
- Tables: `produits`, `mouvements`
- Columns: `no_produit`, `quantite`, `date_heure`, `type`
- Min rows: 500

**Configuration**:
```typescript
{
  analysisDate: Date,
  lookbackDays: number,      // For turnover calculation
  thresholds: {
    lowStock: number,        // Days of stock
    overstock: number,       // Days of stock
    obsolete: number         // Days without movement
  }
}
```

**Output**:
- Current stock levels (if available in movements)
- Turnover rate per product
- Stock coverage (days of supply)
- Understock identification
- Overstock identification
- Dead stock (no movement in X days)
- Obsolete product recommendations

**Visualization**:
- Scatter plot: Turnover vs stock value
- Heatmap: Stock coverage by product
- Table: Stock status with color coding

---

### 3.4 Inventory Overview

**ID**: `inventory-overview`
**Category**: `produits`
**Version**: `1.0.0`

**Description**: High-level overview of product catalog statistics and data quality.

**Data Requirements**:
- Tables: `produits`
- Columns: All columns
- Min rows: 1

**Configuration**:
```typescript
{
  includeDataQuality: boolean,
  groupByCategory: boolean,
  groupByStatus: boolean
}
```

**Output**:
- Total product count
- Distribution by category (up to 3 levels)
- Distribution by status
- Data quality issues:
  - Products without EAN
  - Products without description
  - Products with incomplete data

**Visualization**:
- Summary cards: Key metrics
- Bar chart: Category distribution
- Pie chart: Status distribution
- Table: Data quality issues

---

## 4. Commandes Analyses (Orders)

### 4.1 Order Fulfillment Analysis

**ID**: `commandes-fulfillment`
**Category**: `commandes`
**Version**: `1.0.0`

**Description**: Analyze order fulfillment rates, cycle times, and completion patterns.

**Data Requirements**:
- Tables: `commandes`, `mouvements`
- Columns: `commande`, `date_requise`, `etat`, `date_heure`
- Min rows: 50

**Configuration**:
```typescript
{
  dateRange: {
    start: Date,
    end: Date
  },
  metrics: [
    'fulfillment-rate',     // % orders completed
    'on-time-rate',         // % on-time deliveries
    'cycle-time',           // Time from request to delivery
    'backlog'               // Orders pending
  ]
}
```

**Output**:
- Order fulfillment rate
- On-time delivery rate
- Average cycle time
- Backlog size and age
- Top demandeurs
- Order status distribution

**Visualization**:
- Donut chart: Order status
- Line chart: Fulfillment rate over time
- Bar chart: Top demandeurs
- Table: Order details

---

### 4.2 Lead Time Analysis

**ID**: `commandes-lead-time`
**Category**: `commandes`
**Version**: `1.0.0`

**Description**: Analyze lead times, identify delays, and optimize order processing.

**Data Requirements**:
- Tables: `commandes`, `mouvements`
- Columns: `commande`, `date_requise`, `date_heure`
- Min rows: 100

**Configuration**:
```typescript
{
  dateRange: {
    start: Date,
    end: Date
  },
  groupBy: 'demandeur' | 'type' | 'priorite' | null
}
```

**Output**:
- Average lead time
- Lead time distribution
- Lead time by group
- Orders with excessive delays
- Lead time trends over time

**Visualization**:
- Histogram: Lead time distribution
- Box plot: Lead time by group
- Line chart: Lead time trend
- Table: Delayed orders

---

## 5. Fournisseurs Analyses (Suppliers)

### 5.1 Supplier Performance Analysis

**ID**: `fournisseurs-performance`
**Category**: `fournisseurs`
**Version**: `1.0.0`

**Description**: Analyze supplier performance based on delivery timeliness, quantity accuracy, and quality.

**Data Requirements**:
- Tables: `receptions`, `produits`
- Columns: `fournisseur`, `quantite_recue`, `date_reception`
- Min rows: 50

**Configuration**:
```typescript
{
  dateRange: {
    start: Date,
    end: Date
  },
  metrics: [
    'delivery-timeliness',
    'quantity-accuracy',
    'quality',
    'frequency'
  ]
}
```

**Output**:
- Supplier ranking
- Delivery timeliness per supplier
- Quantity received vs expected
- Reception frequency
- Top suppliers by volume

**Visualization**:
- Bar chart: Supplier ranking
- Scatter plot: Timeliness vs volume
- Table: Supplier details

---

### 5.2 Lot & Expiration Analysis

**ID**: `lot-expiration`
**Category**: `fournisseurs`
**Version**: `1.0.0`

**Description**: Track lots, expiration dates, and identify products at risk of expiration.

**Data Requirements**:
- Tables: `receptions`
- Columns: `numero_lot`, `date_expiration`, `quantite_recue`, `produit`
- Min rows: 50

**Configuration**:
```typescript
{
  asOfDate: Date,
  alertThresholds: {
    critical: number,  // Days until expiration (red)
    warning: number    // Days until expiration (yellow)
  }
}
```

**Output**:
- Products approaching expiration
- Expired products
- Lot tracking
- FEFO (First Expired First Out) compliance
- Risk assessment by product

**Visualization**:
- Timeline: Lot expiration schedule
- Heatmap: Risk by product
- Table: Lots with color coding

---

## 6. Custom Analyses

### Creating Custom Analyses

Users can create custom analyses using the plugin API:

```typescript
// Example: Custom analysis
const customAnalysis: AnalysisDefinition = {
  id: 'my-custom-analysis',
  name: 'My Custom Analysis',
  category: 'custom',

  requirements: {
    tables: ['mouvements'],
    columns: { mouvements: ['no_produit', 'quantite', 'date_heure'] }
  },

  configSchema: z.object({
    threshold: z.number()
  }),

  execute: async (context) => {
    // Custom analysis logic
  },

  outputTemplate: myExportTemplate
}

// Register the analysis
engine.register(customAnalysis)
```

---

## Analysis Comparison Matrix

| Analysis | Data Req | Complexity | Execution Time | Use Case |
|----------|----------|------------|----------------|----------|
| **ABC Classification** | Low | Low | Fast | Inventory prioritization |
| **Temporal Flux** | Medium | Medium | Fast | Trend analysis |
| **Spatial Flux** | High | High | Medium | Layout optimization |
| **Productivity** | Low | Low | Fast | Performance review |
| **Lifecycle** | High | Medium | Medium | Product portfolio |
| **Order Fulfillment** | Medium | Low | Fast | Operations review |
| **Supplier Performance** | Medium | Low | Fast | Vendor management |

---

## Analysis Dependencies

Some analyses depend on others:

```
Basic Analyses (Foundation):
├── ABC Classification
├── Inventory Overview
└── Temporal Flux

Intermediate Analyses:
├── Spatial Flux (requires Temporal Flux)
├── Productivity (requires Inventory Overview)
└── Order Fulfillment

Advanced Analyses:
├── Lifecycle (requires ABC + Temporal Flux)
├── Team Analysis (requires Productivity)
└── Lead Time (requires Order Fulfillment)
```

---

**Version**: 1.0.0
**Last Updated**: 2025-01-26
**Status**: Draft
