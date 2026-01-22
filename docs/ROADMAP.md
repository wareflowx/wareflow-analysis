# Wareflow Analysis - Roadmap & Strategic Planning

## Project Goal

**Objective**: Build an automated data analysis system that:
1. Ingests warehouse data from Excel files (products, movements, orders)
2. Transforms and standardizes data into a SQLite database
3. Performs automated analyses (KPIs, performance metrics, ABC analysis)
4. Exports results to formatted Excel reports

**Key Constraint**: The system must be **fire-and-forget** - updates to source files (new products, movements, orders) should be handled automatically without requiring manual script modifications (10+ minutes).

---

## Current Situation Analysis

### Source Data Structure

**Products (Produits)**
- No. du produit (SKU)
- Nom (description)
- Etat (status)

**Movements (Mouvements)**
- No. du produit, Nom du produit
- Type de mouvement (ENTRÉE, SORTIE, TRANSFERT, AJUSTEMENT)
- Source: Site, Zone, Localisation, Conteneur
- Target: Site, Zone, Localisation, Conteneur
- Quantité, Unité, Date et heure, Personne associée

**Orders (Commandes)**
- Identifiant, Type, Demandeur, Destination
- Niveau de priorité, Date requise
- Nom de lignes, Etat inférieur, Etat supérieur, Etat

### Data Challenges

1. **Non-standard codes**: French WMS codes (ENTRÉE, SORTIE, EN_COURS)
2. **Multi-level locations**: Site + Zone + Localisation + Conteneur
3. **Split status fields**: État supérieur + État inférieur + État
4. **Frequent updates**: New data added daily
5. **Missing fields**: No product dimensions, no order line details

---

## Target Architecture

### Ideal Flow

```
┌──────────────────────────────────────────────────────┐
│  EXCEL SOURCE FILES (updated daily)                  │
│  - produits.xlsx (new products)                      │
│  - mouvements.xlsx (new movements each day)          │
│  - commandes.xlsx (status updates)                   │
└──────────────────┬───────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────┐
│  AUTOMATED IMPORT (excel-to-sql)                     │
│  - Automatic change detection                        │
│  - Native UPSERT (no duplicates)                     │
│  - Mapping + transformation                          │
│  - Data validation                                   │
└──────────────────┬───────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────┐
│  WAREFLOW DATABASE (standardized schema)             │
│  - products, movements, orders                       │
│  - product_performance, operator_performance         │
│  - Always up-to-date, clean data                     │
└──────────────────┬───────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────┐
│  AUTOMATED ANALYSES (materialized views)             │
│  - KPIs calculated automatically                     │
│  - ABC analysis                                      │
│  - Product/operator performance                      │
└──────────────────┬───────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────┐
│  AUTOMATED EXPORT (excel-to-sql or Python)           │
│  - Multi-sheet reports                               │
│  - Charts and KPIs                                   │
│  - Ready for distribution                            │
└──────────────────────────────────────────────────────┘
```

---

## Excel-to-SQL Feature Dependencies

### Critical Features (Blocking) - Cannot automate without these

#### 1. Issue #001: Value Mapping

**Why blocking**: WMS codes must be standardized automatically

**Problem**:
- Source: ENTRÉE, SORTIE, TRANSFERT, EN_COURS, TERMINÉ
- Target: inbound, outbound, transfer, pending, completed

**Without #001**:
- Must write and maintain SQL UPDATE statements
- Fragile, breaks on code changes
- Manual intervention required

**With #001**:
- Configuration JSON once, works forever
- Automatic mapping on import
- Maintenace-free

#### 2. Issue #002: Calculated Columns

**Why blocking**: Combining split status fields automatically

**Problem**:
- Source: État supérieur + État inférieur + État (3 fields)
- Target: status (1 combined field)

**Business logic**: COALESCE(etat_sup, etat_inf, etat)

**Without #002**:
- Complex SQL/Python transformation logic
- Must maintain case statements
- Error-prone

**With #002**:
- Declarative calculation in config
- Automatic combination
- Testable and maintainable

#### 3. Issue #003: Custom Validators

**Why blocking**: Automatic data quality validation

**Risks**:
- Negative quantities
- Invalid dates
- Unknown SKUs in movements
- Missing required fields

**Without #003**:
- Invalid data enters database
- Analyses produce incorrect results
- Manual data cleaning required

**With #003**:
- Automatic rejection/validation
- Clear error reporting
- Data quality enforced at import

#### 4. Issue #004: Reference Validation

**Why blocking**: Referential integrity enforcement

**Problem**:
- Movement references SKU that doesn't exist in products
- Order line references non-existent order

**Without #004**:
- Orphaned records in database
- Analyses miss data
- Silent failures

**With #004**:
- Immediate error on import
- Clear violation reporting
- Data integrity guaranteed

#### 5. Issue #008: Incremental Import

**Why blocking**: Efficient daily updates

**Reality**:
- 100,000 historical movements
- 5,000 new movements per day
- Full import: 5 minutes
- Incremental import: 10 seconds

**Without #008**:
- Long import times discourage updates
- Must reprocess all data every time
- Impractical for daily use

**With #008**:
- Only process new/changed rows
- Fast daily updates
- Practical automation

### Important Features (Significant Simplification)

#### 6. Issue #006: Multi-Sheet Import

**Use case**: Import orders + order lines together with FK validation

#### 7. Issue #011: Python SDK

**Use case**: Seamless integration in analysis scripts

---

## Strategic Options

### Option A: Wait for Critical Features ⚠️ DEPRECATED

**Status**: Superseded by excel-to-sql 0.3.0 Auto-Pilot Mode

This option is no longer recommended as excel-to-sql 0.3.0 now includes all critical features.

### Option B: Active Contribution ⚠️ DEPRECATED

**Status**: No longer necessary

excel-to-sql 0.3.0 already implements all required features including value mapping, calculated columns, and validation.

### Option C: Custom ETL Solution ⚠️ DEPRECATED

**Status**: Not recommended

With Auto-Pilot Mode, building custom ETL code is unnecessary overhead. The Auto-Pilot approach provides the same flexibility with 80% less development effort.

---

## ✨ NEW RECOMMENDED APPROACH: Option D - Auto-Pilot Assisted

### Overview

excel-to-sql 0.3.0 introduces **Auto-Pilot Mode** - a zero-configuration intelligent import system that automatically detects patterns, scores data quality, and guides you through setup. This creates a new, superior option for wareflow-analysis.

### Strategy

**Hybrid intelligent approach**:
1. Use Auto-Pilot to automatically generate initial configuration
2. Manually refine detected mappings and patterns
3. Use programmatic SDK approach for integration
4. Maintain full control over business logic

### Benefits

| Aspect | Benefit |
|--------|---------|
| ⚡ **Speed** | Configuration in 5 minutes vs 2-3 months |
| 🎯 **Zero Config** | No manual column mapping required |
| 🇫🇷 **French Code Detection** | Automatic ENTRÉE→inbound mapping |
| 🔍 **Data Quality** | Built-in quality scoring (0-100) |
| 🚀 **Accelerated Dev** | Import test data immediately |
| 🎛️ **Full Control** | Adjust what Auto-Pilot detects |

### Timeline Comparison

| Option | Time to MVP | Development Effort | Maintenance |
|--------|-------------|-------------------|-------------|
| **Option A** (Wait) | 6-12 months | Low | Very low |
| **Option B** (Contribute) | 2-3 months | Medium | Low |
| **Option C** (Custom ETL) | 2 months | High | Medium |
| **Option D** (Auto-Pilot) | **2-3 weeks** | **Low** | **Low** |

**Recommendation**: **Option D** is now the official recommended approach.

### Technical Approach

#### Phase 1: Auto-Pilot Configuration (Day 1)

```bash
# Analyze Excel files with Auto-Pilot
excel-to-sql magic --data ./data --dry-run

# Review detected patterns, quality score, recommendations
# Interactive mode if needed
excel-to-sql magic --data ./data --interactive
```

Auto-Pilot automatically detects:
- ✅ Primary keys
- ✅ Foreign keys
- ✅ Value mappings (11 French code mappings)
- ✅ Split fields to combine (COALESCE)
- ✅ Data types
- ✅ Quality issues with scoring

#### Phase 2: Refinement (Day 2)

```python
# src/wareflow_analysis/import/autopilot.py
from excel_to_sql.auto_pilot import PatternDetector

def generate_config(data_dir: Path) -> dict:
    """Generate config with Auto-Pilot, refine for wareflow"""
    detector = PatternDetector(data_dir)
    config = detector.detect_patterns()

    # Add wareflow-specific mappings
    config = refine_for_wareflow(config)

    return config
```

#### Phase 3: SDK Integration (Day 3-4)

```python
# src/wareflow_analysis/import/importer.py
from excel_to_sql import ExcelToSqlite

def run_import(project_dir: Path):
    """Import using excel-to-sql SDK"""
    config = load_config("config.yaml")

    sdk = ExcelToSqlite(db_path="warehouse.db")
    result = sdk.import_excel(
        file_path=config['source'],
        mapping_name=config['name'],
        mapping_config=config
    )
    return result
```

### Migration from Previous Options

Users who previously considered Options A, B, or C should migrate to Option D:

**From Option A**: No need to wait - features are ready now
**From Option B**: No need to contribute - use existing Auto-Pilot
**From Option C**: Replace custom ETL code with Auto-Pilot + SDK approach

---

## Updated Implementation Timeline

### Phase 1: Auto-Pilot Integration (Week 1)

**Goals**:
- Test Auto-Pilot on real WMS data
- Generate initial configuration
- Integrate SDK into wareflow-analysis
- Implement `import` command

**Deliverables**:
- [x] excel-to-sql 0.3.0 installed
- [ ] Auto-Pilot configuration generated
- [ ] `import/autopilot.py` module
- [ ] `import/importer.py` SDK wrapper
- [ ] CLI integration
- [ ] Initial tests with real data

### Phase 2: Core Analyses (Week 2)

**Goals**:
- Implement basic SQL analyses
- Create KPI calculators
- Generate first reports

**Deliverables**:
- [ ] `analyze/` module with queries
- [ ] `analyze/` module with calculators
- [ ] 4 core analyses (overview, movements, products, orders)
- [ ] CLI integration

### Phase 3: Export & Orchestration (Week 3)

**Goals**:
- Excel report generation
- Full pipeline orchestration
- End-to-end testing

**Deliverables**:
- [ ] `export/` module with Excel builder
- [ ] `run/` orchestration module
- [ ] Complete E2E testing
- [ ] Documentation

### Total Timeline: **2-3 weeks** for MVP (vs 6-8 weeks previously)

---

## Migration Path from Auto-Pilot

### Phase 1: Use Auto-Pilot Generated Config (Immediate)

- Deploy with configuration generated by Auto-Pilot
- Validate analyses work correctly
- Identify edge cases and specific needs

### Phase 2: Adopt Enhanced Features (As Needed)

Auto-Pilot continues evolving:
- New detection capabilities can be adopted
- Enhanced quality analysis
- Improved recommendations

### Phase 3: Full Customization (Optional)

- Customize configuration based on usage patterns
- Add wareflow-specific business rules
- Optimize based on real-world feedback

---

## Decision Matrix - Updated

| Factor | Option A | Option B | Option C | **Option D** |
|--------|----------|----------|----------|-------------|
| Time to working | 6-12 mo | 2-3 mo | 2 mo | **2-3 weeks** ✨ |
| Development effort | Low | Medium | High | **Low** ✨ |
| Maintenance | Very low | Low | Medium | **Low** ✨ |
| Flexibility | Low | Medium | High | **High** ✨ |
| Migration needed | No | No | Yes | **No** ✨ |
| Control over timeline | None | High | High | **High** ✨ |
| Community benefit | None | High | None | **Medium** |
| **Overall Winner** | ❌ | ⚠️ | ⚠️ | **✅ RECOMMENDED** |

**Official Recommendation**: **Option D - Auto-Pilot Assisted**

---

## Critical Success Factors

### 1. Data Quality First

Auto-Pilot's quality scoring (0-100) provides immediate feedback:
- **Grade A (90-100)**: Excellent - proceed with confidence
- **Grade B (70-89)**: Good - minor issues to address
- **Grade C (50-69)**: Acceptable - significant issues
- **Grade D (<50)**: Poor - major data quality problems

### 2. Iterative Refinement

Don't expect perfection on first run:
1. Run Auto-Pilot → Get baseline config
2. Test import → Identify gaps
3. Refine config → Add specific mappings
4. Repeat until satisfied

### 3. Leverage Automation

Auto-Pilot eliminates 80-90% of manual work:
- Focus time on business logic, not ETL plumbing
- Let Auto-Pilot handle routine mappings
- Manual effort only for wareflow-specific needs

---

## Next Steps - Immediate Actions

### This Week

1. **Install excel-to-sql 0.3.0**
   ```bash
   pip install excel-to-sql==0.3.0
   ```

2. **Test Auto-Pilot on sample data**
   ```bash
   excel-to-sql magic --data ./data --dry-run
   ```

3. **Document findings**
   - Create `docs/autopilot-analysis.md`
   - Record detected patterns
   - Note manual adjustments needed

### Following Weeks

4. **Implement import command** (3-4 days)
5. **Implement analyze command** (2-3 days)
6. **Implement export command** (3-4 days)
7. **Implement run command** (1-2 days)
8. **Complete testing & documentation** (2-3 days)

---

## Updated Architecture

```
wareflow-analysis/
├── config/
│   └── wareflow_config.yaml          # Single configuration file
├── data/
│   ├── produits.xlsx                  # Source files
│   ├── mouvements.xlsx
│   └── commandes.xlsx
├── scripts/
│   ├── etl.py                        # Import + Transform (automatic)
│   ├── analyses.py                   # All Wareflow analyses
│   └── export.py                     # Excel multi-sheet export
├── output/
│   └── rapports/                     # Generated reports
└── warehouse.db                      # SQLite (Wareflow schema)
```

### Daily Workflow

**Option 1: Step by step**
```bash
python scripts/etl.py --update          # Import and transform automatically
python scripts/analyses.py --run        # Calculate all analyses
python scripts/export.py --all          # Generate Excel reports
```

**Option 2: One pipeline**
```bash
python scripts/run_pipeline.py          # All 3 steps automatically
```

**Option 3: Scheduled**
```bash
# Windows Task Scheduler or cron
0 2 * * * cd /path/to/wareflow-analysis && python scripts/run_pipeline.py
```

### Key Success Factors

1. **No manual modification** when data changes
2. **Automatic detection** of new files/rows
3. **Automatic validation** before transformation
4. **Centralized configuration** (no code to edit)
5. **Idempotent** - can run multiple times safely
6. **Incremental** - only processes new data
7. **Error handling** - clear reporting on failures

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Goals**:
- Set up project structure
- Define Wareflow database schema
- Create basic ETL pipeline

**Deliverables**:
- [ ] Project structure created
- [ ] Wareflow database schema defined
- [ ] Basic import (products, movements, orders)
- [ ] Basic transformation scripts

### Phase 2: Core Analyses (Week 3-4)

**Goals**:
- Implement key Wareflow analyses
- Create materialized views
- Generate basic reports

**Deliverables**:
- [ ] Product performance analysis
- [ ] Movement statistics
- [ ] Order fulfillment metrics
- [ ] Basic Excel export

### Phase 3: Advanced Features (Week 5-6)

**Goals**:
- Add advanced analytics
- Implement incremental updates
- Create comprehensive reports

**Deliverables**:
- [ ] ABC analysis
- [ ] Operator performance
- [ ] Picking efficiency
- [ ] Multi-sheet reports with charts

### Phase 4: Automation & Polish (Week 7-8)

**Goals**:
- Full automation
- Error handling
- Documentation

**Deliverables**:
- [ ] Scheduled pipeline
- [ ] Error logging and alerts
- [ ] User documentation
- [ ] Maintenance guide

---

## Migration Path to Native Excel-to-SQL

### Phase 1: Use Temporary Solution

- Deploy Option C (custom ETL)
- Validate analyses work correctly
- Identify edge cases

### Phase 2: Adopt Features as Available

**When #001 ready**: Replace custom value mapping
**When #002 ready**: Replace calculated columns
**When #003 ready**: Add validators
**When #004 ready**: Add reference validation
**When #008 ready**: Switch to incremental import

### Phase 3: Full Migration

- Migrate all configuration to excel-to-sql
- Remove custom ETL code
- Use excel-to-sql natively
- Maintain only analysis queries

---

## Success Criteria

### Functional Requirements

- [ ] Automatically imports new data without script changes
- [ ] Validates data quality before processing
- [ ] Standardizes WMS codes to internal schema
- [ ] Calculates all Wareflow KPIs automatically
- [ ] Generates formatted Excel reports
- [ ] Handles daily updates in < 1 minute
- [ ] Clear error reporting when data issues occur

### Non-Functional Requirements

- [ ] Idempotent (can run multiple times safely)
- [ ] Incremental (only processes new data)
- [ ] Resilient (handles missing fields, bad data)
- [ ] Maintainable (configuration > code)
- [ ] Documented (user guide, maintenance guide)
- [ ] Testable (sample data, test cases)

---

## Timeline Estimate

### Option A: Wait for excel-to-sql features
- **Timeline**: 6-12 months
- **Effort**: Low (configuration only)
- **Maintenance**: Very low

### Option B: Contribute actively
- **Timeline**: 2-3 months
- **Effort**: Medium (contributions to excel-to-sql)
- **Maintenance**: Low

### Option C: Temporary solution
- **Timeline**: 2 months
- **Effort**: Medium-High (custom ETL)
- **Maintenance**: Medium (until migration)

---

## Decision Matrix

| Factor | Option A | Option B | Option C |
|--------|----------|----------|----------|
| Time to working | 6-12 mo | 2-3 mo | 2 mo |
| Development effort | Low | Medium | High |
| Maintenance | Very low | Low | Medium |
| Flexibility | Low | Medium | High |
| Migration needed | No | No | Yes |
| Control over timeline | None | High | High |
| Community benefit | None | High | None |

**Recommendation**: Start with Option C for immediate results, migrate to Option B features as they become available.

---

## Next Steps

### Immediate Actions

1. **Review this roadmap** with stakeholders
2. **Choose strategic option** (A, B, or C)
3. **Define sample data** for testing
4. **Prioritize features** based on timeline needs

### If Choosing Option C (Recommended)

1. Create project structure
2. Define Wareflow database schema
3. Build basic ETL pipeline
4. Implement core analyses
5. Set up automation

### If Choosing Option B (Contribute)

1. Fork excel-to-sql repository
2. Start with Issue #001 (Value Mapping)
3. Use Wareflow data as test case
4. Submit PRs for review
5. Iterate based on feedback

---

## Questions to Resolve

1. **Timeline**: How soon do you need a working system?
2. **Resources**: Available development time per week?
3. **Data access**: Can we use real/anonymized data for testing?
4. **Analyses priority**: Which Wareflow analyses are most critical?
5. **Update frequency**: Daily, weekly, ad-hoc?
6. **Report consumers**: Who receives reports and in what format?

---

## Appendix: Technical Considerations

### Database Schema

**Core tables** (from PROJECT.md):
- products
- movements
- orders
- order_lines
- picking_lines
- replenishments
- product_performance (derived)
- operator_performance (derived)

### Key Transformations

**Location mapping**:
- Site → zone
- Zone → aisle
- Localisation → bay
- Conteneur → level

**Code mappings**:
- Movement types: ENTRÉE→inbound, SORTIE→outbound
- Status: EN_COURS→pending, TERMINÉ→completed

**Status combination**:
- COALESCE(etat_sup, etat_inf, etat)

### Performance Considerations

- Indexes on all foreign keys
- Indexes on timestamp fields
- Materialized views for complex analytics
- Incremental imports for daily updates

---

*Last Updated: 2025-01-20*
*Status: Planning Phase - Awaiting Decision on Strategic Approach*
