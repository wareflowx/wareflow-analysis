# Import Command Implementation Plan

## Overview

This document provides a comprehensive analysis of implementing the `import` command for the Wareflow Analysis CLI using excel-to-sql 0.3.0 **Auto-Pilot Mode**.

## Current State

**Phase 1 (Completed)**: CLI infrastructure and `init` command ✅
**Phase 2 (Next)**: Data processing - `import` command ❌

The `import` command is the **critical entry point** for the data pipeline using Auto-Pilot Mode.

## ✨ Important Update: Auto-Pilot Approach

**As of January 2025**, excel-to-sql 0.3.0 introduces **Auto-Pilot Mode** - a zero-configuration intelligent import system. This supersedes the previous manual ETL approach (Option C) and is now the **official recommended approach (Option D)**.

### Why Auto-Pilot?

| Aspect | Manual ETL (Option C) | Auto-Pilot (Option D) |
|--------|----------------------|----------------------|
| Development time | 10 days | 2 days |
| Lines of code | ~2000 lines | ~200 lines |
| Configuration | Manual | Automatic |
| Quality insight | None | Comprehensive scoring |
| Time to MVP | 6-8 weeks | 2-3 weeks |

**Recommendation**: Use Auto-Pilot Mode for all new implementations.

---

## Command Specifications

### Current Implementation

**File**: `src/wareflow_analysis/cli.py:36-38`

```python
@app.command()
def import_data() -> None:
    """Import data from Excel files to SQLite."""
    typer.echo("Import command not implemented yet")
```

**Status**: Skeleton without implementation

### Command Responsibilities

According to IMPLEMENTATION.md and the template `templates/import.py`, the command must:

#### 1. Environment Validation
- **Check we're in a wareflow project**
  - Presence of `config.yaml` in current directory
  - Presence of `warehouse.db`
  - Clear error message if not in a project

- **Read configuration**
  - Parse `config.yaml`
  - Extract import definitions (sources, tables, primary keys)

#### 2. Excel File Processing

The original template planned to call `excel-to-sql`:

```python
result = subprocess.run(
    ["excel-to-sql", "import", "--config", "config.yaml"],
    capture_output=True,
    text=True,
)
```

**CRITICAL ISSUE**: `excel-to-sql` doesn't exist or isn't installed!

### Strategic Decision: Auto-Pilot Architecture

**IMPORTANT UPDATE (January 2025)**: excel-to-sql 0.3.0 introduces **Auto-Pilot Mode** which supersedes all previous strategic options.

**Previous Options (Now Deprecated)**:

| Option | Description | Status |
|--------|-------------|--------|
| **A** | Wait for `excel-to-sql` features | ⚠️ DEPRECATED - Features now available |
| **B** | Contribute to `excel-to-sql` | ⚠️ DEPRECATED - Not necessary |
| **C** | Custom ETL solution | ⚠️ DEPRECATED - Auto-Pilot is superior |

**NEW Official Recommendation: Option D - Auto-Pilot Assisted**

| Aspect | Benefit |
|--------|---------|
| ⚡ Speed | Configuration in 5 minutes vs 10 days of coding |
| 🎯 Zero Config | No manual column mapping required |
| 🇫🇷 French Codes | Auto-detects 11 common French WMS mappings |
| 🔍 Quality | Built-in scoring (0-100) with detailed reports |
| 🚀 Accelerated | Import test data immediately |

---

## Technical Architecture to Implement

### File Structure to Create

```
src/wareflow_analysis/
├── cli.py                      # ✅ Exists (modify for import command)
├── init.py                     # ✅ Exists
├── import/                     # 🆕 New module (simplified vs Option C)
│   ├── __init__.py
│   ├── autopilot.py            # Auto-Pilot config generator
│   ├── config_refiner.py        # Wareflow-specific refinements
│   └── importer.py              # excel-to-sql SDK wrapper
└── templates/                  # ✅ Exists
    └── config_autopilot.yaml   # Auto-Pilot generated config
```

**Comparison with Option C (Manual ETL)**:

| Component | Option C (Manual) | Option D (Auto-Pilot) | Reduction |
|-----------|-----------------|---------------------|-----------|
| Total lines | ~1100 lines | ~450 lines | **-60%** |
| Complexity | High | Low-Medium | **Significant** |
| Maintenance | High | Low | **80% less** |
| Time to implement | 10 days | 2-3 days | **70% faster** |

### Technical Dependencies

**Already configured in pyproject.toml**:
- ✅ `pandas>=2.0` - Data manipulation
- ✅ `openpyxl>=3.0` - Excel read/write
- ✅ `typer>=0.21` - CLI framework

**To add** (required):
- ❌ `pyyaml` - Parsing config.yaml (MISSING from pyproject.toml!)

---

## Detailed Functional Specifications

### A. Module `config.py` - Configuration Parsing

**Input**: File `config.yaml`

```yaml
database:
  path: warehouse.db

imports:
  produits:
    source: data/produits.xlsx
    table: produits
    primary_key: no_produit

  mouvements:
    source: data/mouvements.xlsx
    table: mouvements
    primary_key: oid

  commandes:
    source: data/commandes.xlsx
    table: commandes
    primary_key: commande
```

**Responsibilities**:
1. Load and validate YAML
2. Verify source files exist
3. Extract configuration structure
4. Validate consistency (defined tables match schema)

**Functions to implement**:
```python
def load_config(config_path: Path) -> dict
def validate_config(config: dict) -> tuple[bool, str]
def get_import_jobs(config: dict) -> list[ImportJob]
```

### B. Module `excel_reader.py` - Excel File Reading

**Responsibilities**:
1. Read Excel files with pandas
2. Validate expected columns
3. Handle multiple sheets (if applicable)
4. Handle data types
5. Clean data (missing values, incorrect types)

#### Challenges Identified in ROADMAP.md

**Challenge 1: Non-standard WMS Codes**
- **Source**: `ENTRÉE`, `SORTIE`, `TRANSFERT`, `AJUSTEMENT`
- **Target**: `inbound`, `outbound`, `transfer`, `adjustment`
- **Solution**: Value mapping in configuration

**Challenge 2: Split Status Fields**
- **Source**: `etat_superieur`, `etat_inferieur`, `etat` (3 fields)
- **Target**: Combined status
- **Solution**: COALESCE logic or business rule

**Challenge 3: Inconsistent Data Types**
- **Dates**: Variable formats (DD/MM/YYYY, YYYY-MM-DD, timestamps)
- **Numbers**: Some TEXT fields contain REAL values
- **Solution**: Explicit conversion with error handling

**Functions to implement**:
```python
def read_excel_file(file_path: Path, sheet_name: str = None) -> pd.DataFrame
def validate_columns(df: pd.DataFrame, expected_columns: list) -> tuple[bool, list[str]]
def clean_dataframe(df: pd.DataFrame, table_name: str) -> pd.DataFrame
def map_values(df: pd.DataFrame, mappings: dict) -> pd.DataFrame
```

### C. Module `db_writer.py` - SQLite Writing

**Responsibilities**:
1. Connect to existing SQLite database
2. Insert or update data (UPSERT)
3. Handle transactions (commit/rollback)
4. Report statistics (rows inserted, errors)

#### Technical Challenges

**Challenge 1: UPSERT in SQLite**
- SQLite supports `INSERT OR REPLACE` but requires a primary key
- Schema defines primary keys: `no_produit`, `oid`, `commande`
- **Solution**: Use `INSERT OR REPLACE` with defined PKs

**Challenge 2: Foreign Key Management**
- Table `mouvements` has FK to `produits(no_produit)`
- Table `receptions` has FK to `produits(no_produit)`
- **Risk**: Movement with `no_produit` that doesn't exist
- **Solutions**:
  - Option 1: Import in dependency order (products before movements)
  - Option 2: Disable FK constraints during import
  - Option 3: Validate and reject orphaned rows

**Functions to implement**:
```python
def connect_to_database(db_path: Path) -> sqlite3.Connection
def insert_or_replace_data(conn: Connection, table: str, df: pd.DataFrame) -> dict
def table_exists(conn: Connection, table_name: str) -> bool
def get_row_count(conn: Connection, table_name: str) -> int
```

### D. Module `importer.py` - Orchestration

**Responsibilities**:
1. Coordinate previous modules
2. Handle global errors
3. Display progress to user
4. Generate import report

**Functions to implement**:
```python
def run_import(project_dir: Path = None) -> tuple[bool, str]
def import_single_file(job: ImportJob, conn: Connection) -> ImportResult
def generate_import_report(results: list[ImportResult]) -> str
```

---

## Complete Execution Flow

### `import` Command Algorithm

```
┌─────────────────────────────────────┐
│ 1. Check Environment               │
│    - config.yaml exists?            │
│    - warehouse.db exists?           │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 2. Load Configuration              │
│    - Parse config.yaml              │
│    - Validate structure             │
│    - Verify source files            │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 3. For Each Import Job             │
│    ┌─────────────────────────────┐  │
│    │ a. Read Excel file          │  │
│    │ b. Validate columns         │  │
│    │ c. Clean data               │  │
│    │ d. Transform types          │  │
│    │ e. Insert into SQLite       │  │
│    │ f. Capture statistics       │  │
│    └─────────────────────────────┘  │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 4. Generate Report                 │
│    - Rows imported per table       │
│    - Errors encountered            │
│    - Execution time                │
└──────────┬──────────────────────────┘
           ↓
┌─────────────────────────────────────┐
│ 5. Return Status                   │
│    - Success if all OK             │
│    - Error message otherwise       │
└─────────────────────────────────────┘
```

---

## Watch Points and Risks

### 1. Missing Dependency: PyYAML

**Observation**: `pyproject.toml` does NOT contain `pyyaml`

**Impact**: Cannot read `config.yaml`

**Required Action**: Add dependency
```toml
dependencies = [
    "typer>=0.21",
    "pandas>=2.0",
    "openpyxl>=3.0",
    "pyyaml>=6.0",  # ← To add
]
```

### 2. Import Order Dependent on Foreign Keys

**Current Schema**:
```sql
CREATE TABLE mouvements (
    ...
    FOREIGN KEY (no_produit) REFERENCES produits(no_produit)
);
```

**Problem**: If importing `mouvements` before `produits`, FK error

**Solutions**:
- **Option A**: Automatically sort jobs by dependencies
- **Option B**: Always import `produits` first
- **Option C**: Temporarily disable FK constraints

**Recommendation**: Option B (simple and reliable)

### 3. Large Data Handling

**Scenario**: 100,000 historical movements + 5,000 new/day

**Risks**:
- Memory: Loading all in RAM may saturate
- Performance: Row-by-row INSERT is slow

**Solutions**:
- **Chunking**: Read and insert in 1000-row batches
- **Batch INSERT**: Use SQLite's `executemany()`
- **Progress**: Display progress bar

### 4. Data Validation

**Risks Identified in ROADMAP.md**:
- Negative quantities
- Invalid dates (31/02/2025)
- Unknown SKUs in movements
- Incorrect types (text instead of number)

**Strategy**:
1. **Strict validation**: Reject invalid rows
2. **Logging**: Record errors in file
3. **Reporting**: Display count of rejected rows

---

## Tests to Implement

### Unit Tests

```python
# tests/test_import_config.py
def test_load_valid_config()
def test_load_missing_config()
def test_load_invalid_yaml()
def test_validate_config_with_missing_files()
def test_get_import_jobs()

# tests/test_excel_reader.py
def test_read_excel_file_exists()
def test_read_excel_file_not_exists()
def test_validate_columns_success()
def test_validate_columns_missing()
def test_clean_dataframe_with_nulls()

# tests/test_db_writer.py
def test_connect_to_database()
def test_table_exists()
def test_insert_or_replace_data()
def test_insert_with_foreign_key_violation()

# tests/test_importer.py
def test_run_import_success()
def test_run_import_missing_config()
def test_import_single_file()
def test_generate_import_report()
```

### Integration Tests

```python
# tests/test_cli_integration.py
def test_import_command_creates_data()
def test_import_command_with_real_excel()
def test_import_command_handles_errors()
def test_full_init_import_flow()
```

### Test Datasets

**Need**: Excel test files with:
- Valid data
- Invalid data (incorrect types)
- Missing values
- Large datasets (performance test)

---

## Success Metrics

### Functional Objectives

- ✅ Successfully import 4 tables (produits, mouvements, commandes, receptions)
- ✅ Handle errors gracefully
- ✅ Display clear progress
- ✅ Generate import report

### Technical Objectives

- ✅ Process 10,000-row file in < 30 seconds
- ✅ Memory usage < 500MB
- ✅ Zero data loss (validation before insertion)
- ✅ ACID transactions (all or nothing)

### Quality Objectives

- ✅ Test coverage > 80%
- ✅ No duplicated code
- ✅ Clear, actionable error messages
- ✅ Complete documentation (docstrings)

---

## Phased Implementation Plan

### Phase 1: Auto-Pilot Setup & Configuration (Days 1-2)

**Objectives**:
- Install and test excel-to-sql 0.3.0
- Generate initial configuration with Auto-Pilot
- Create basic module structure

**Deliverables**:
- [ ] excel-to-sql 0.3.0 installed in pyproject.toml
- [ ] Test Auto-Pilot on sample data
- [ ] `import/autopilot.py` - Config generator
- [ ] `import/config_refiner.py` - Refinements
- [ ] Generated `excel-to-sql-config.yaml`

**Testing**:
```bash
# Test Auto-Pilot dry-run
excel-to-sql magic --data ./data --dry-run

# Test quality scoring
excel-to-sql magic --data ./data --interactive
```

### Phase 2: SDK Integration (Days 3-4)

**Objectives**:
- Wrap excel-to-sql SDK for programmatic import
- Implement CLI integration
- Handle progress reporting

**Deliverables**:
- [ ] `import/importer.py` - SDK wrapper
- [ ] CLI command modifications
- [ ] Progress and error reporting
- [ ] Basic import functionality

**Testing**:
```bash
# Test import
wareflow import

# Verify data loaded
sqlite3 warehouse.db "SELECT COUNT(*) FROM produits;"
```

### Phase 3: Validation & Polish (Days 5-7)

**Objectives**:
- Comprehensive error handling
- Data quality validation
- User documentation

**Deliverables**:
- [ ] Pre-import validation
- [ ] Error messages and recovery
- [ ] Unit tests (>80% coverage)
- [ ] User documentation

**Testing**:
- Unit tests for all modules
- Integration tests with real Excel files
- Error scenario testing

**Total Timeline**: 1 week for basic functionality, 2 weeks with comprehensive testing

**vs Previous Timeline (Option C)**: 10 days for basic, 14+ days total

**Speed Improvement**: ~40% faster

---

## Key Differences from Manual ETL (Option C)

### What Auto-Pilot Eliminates

| Complex Task | Before (Manual) | After (Auto-Pilot) |
|--------------|----------------|-----------------|
| **Column Detection** | Manual specification | Automatic |
| **Type Inference** | Manual per column | Automatic from data |
| **PK Detection** | Manual specification | Automatic (uniqueness analysis) |
| **FK Detection** | Manual specification | Automatic (relationship detection) |
| **French Mappings** | Manual mapping file | Auto-detected 11 common codes |
| **Quality Analysis** | None (post-import) | Built-in scoring (0-100) |
| **Split Field Detection** | Manual SQL COALESCE | Automatic suggestion |

### What Remains Manual

**Business Logic Only** (~10-20% of work):
- Wareflow-specific business rules
- Custom validation thresholds
- Domain-specific calculations
- Special edge case handling

### Code Comparison

**Manual ETL (Option C)** - NOT RECOMMENDED:
```python
# ~500 lines of excel_reader.py
def read_excel_file(file_path):
    df = pd.read_excel(file_path)
    # Manual column validation
    # Manual type detection
    # Manual data cleaning
    # Manual value mapping
    return df

# ~400 lines of db_writer.py
def insert_or_replace_data(conn, table, df):
    # Manual UPSERT logic
    # Manual transaction handling
    # Manual error handling
    pass

# ~200 lines of config.py
def load_config(config_path):
    # Manual YAML parsing
    # Manual validation
    pass
```

**Auto-Pilot (Option D)** - RECOMMENDED:
```python
# ~150 lines of autopilot.py
def generate_autopilot_config(data_dir):
    detector = PatternDetector(data_dir)  # Auto-Pilot SDK
    config = detector.detect_patterns()
    return refine_for_wareflow(config)  # Only business logic

# ~100 lines of importer.py
def run_import(project_dir):
    sdk = ExcelToSqlite("warehouse.db")  # excel-to-sql SDK
    result = sdk.import_excel(
        file_path=config['source'],
        mapping_name=config['name'],
        mapping_config=config
    )
    return result
```

**Reduction**: ~80% less code, focus on business logic not ETL plumbing.

---

## Dependencies with Other Commands

### Impact on `analyze`

**Prerequisite**: `import` must work to test `analyze`

**Data required** for first analyses:
- Table `produits` with data
- Table `mouvements` with data
- Minimum 100 movements to calculate statistics

**Analyses to implement next**:
- Count rows per table
- Calculate totals by movement type
- Identify most moved products

### Impact on `export`

**Prerequisite**: `import` + `analyze` must work

**Minimum export**:
- Extract all tables
- Generate Excel file with one sheet per table
- Format headers

### Impact on `run`

**Prerequisite**: All previous commands

**Full pipeline**:
```bash
wareflow run  # → import → analyze → export
```

---

## Expected Deliverables

### Code
- 4 Python modules in `src/wareflow_analysis/import/`
- Modified `cli.py`
- Added `pyyaml` in `pyproject.toml`

### Tests
- 15+ unit tests
- 4+ integration tests
- Test datasets

### Documentation
- Complete docstrings
- Updated README with import examples
- Troubleshooting guide

### Artifacts
- Excel test files
- Test data generation script
- Test coverage report

---

## Configuration File Example

### Current `config.yaml` Template

```yaml
# Wareflow Analysis Configuration
# Generated by wareflow-analysis

database:
  path: warehouse.db

imports:
  produits:
    source: data/produits.xlsx
    table: produits
    primary_key: no_produit

  mouvements:
    source: data/mouvements.xlsx
    table: mouvements
    primary_key: oid

  commandes:
    source: data/commandes.xlsx
    table: commandes
    primary_key: commande
```

### Extended Configuration (Future Enhancement)

```yaml
database:
  path: warehouse.db

imports:
  produits:
    source: data/produits.xlsx
    table: produits
    primary_key: no_produit
    sheet: Sheet1  # Optional sheet name
    column_mappings:
      nom_produit: description  # Source → Target

  mouvements:
    source: data/mouvements.xlsx
    table: mouvements
    primary_key: oid
    value_mappings:
      type:
        ENTRÉE: inbound
        SORTIE: outbound
        TRANSFERT: transfer
        AJUSTEMENT: adjustment
    transformations:
      status: COALESCE(etat_superieur, etat_inferieur, etat)

validation:
  strict: true  # Reject invalid rows
  log_errors: import_errors.log
  skip_duplicates: true
```

---

## Error Handling Strategy

### Validation Errors

| Error Type | Action | User Message |
|------------|--------|--------------|
| Missing config.yaml | Exit | "Not in a wareflow project (config.yaml not found)" |
| Missing warehouse.db | Exit | "Database not found. Run 'wareflow init' first" |
| Missing source file | Skip/Abort | "Source file not found: data/produits.xlsx" |
| Invalid column | Log and skip | "Column mismatch in produits.xlsx" |
| Invalid data type | Log and skip row | "Invalid date format in row 42" |
| Foreign key violation | Log and skip row | "Unknown product no_produit=12345" |

### Progress Display

```
Importing data from Excel files...
  ✓ produits: 1,234 rows imported
  ✓ mouvements: 45,678 rows imported
  ✓ commandes: 789 rows imported
  ✓ receptions: 234 rows imported

Import completed!
  Total: 47,935 rows in 4 tables
  Time: 12.3 seconds
  Errors: 0
```

### Error Report Example

```
Import completed with errors!
  Total: 47,930 rows imported
  Errors: 5 rows rejected

Details:
  - mouvements.xlsx: 3 errors (invalid dates in rows 102, 456, 789)
  - commandes.xlsx: 2 errors (unknown products in rows 45, 67)

See import_errors.log for details.
```

---

## Performance Considerations

### Optimization Strategies

1. **Batch Processing**
   - Read Excel in chunks (10,000 rows)
   - Insert in batches (1,000 rows)
   - Reduces memory footprint

2. **Database Indexes**
   - Already defined in schema.sql
   - Speeds up foreign key validation
   - Improves query performance

3. **Transaction Management**
   - Single transaction per table
   - Rollback on error
   - Ensures data consistency

4. **Progress Feedback**
   - Progress bar for large files
   - Regular status updates
   - ETA calculation

### Performance Targets

| Operation | Rows | Target Time |
|-----------|------|-------------|
| Small import | < 1,000 | < 5 seconds |
| Medium import | 1,000 - 10,000 | < 30 seconds |
| Large import | 10,000 - 100,000 | < 5 minutes |
| Incremental update | < 5,000 | < 10 seconds |

---

## Migration Path

### Current Template vs. Implementation

**Template Approach** (templates/import.py):
- Calls external `excel-to-sql` command
- Configuration-driven
- No custom code

**Implementation Approach**:
- Native Python implementation
- Uses pandas and openpyxl
- Full control over data processing

### Future Migration to excel-to-sql

When `excel-to-sql` becomes available with required features:
1. Keep configuration format compatible
2. Migrate validation logic
3. Switch to subprocess call
4. Remove custom code

---

## User Experience Design

This section details the complete user experience (UX) for the `import` command, covering all scenarios from successful imports to error handling.

### Design Principles

1. **Clarity** - Clear, actionable messages
2. **Transparency** - Progress bars and detailed statistics
3. **Safety** - Validation before modification, dry-run modes
4. **Flexibility** - Options for different scenarios
5. **Recovery** - Error messages with solutions
6. **Feedback** - Emojis for quick visual recognition

### Visual Language

| Icon | Meaning | Usage |
|------|---------|-------|
| ✅ | Success | Operation completed successfully |
| ❌ | Error | Operation failed with clear error |
| ⚠️  | Warning | Operation completed with warnings |
| 💡 | Information | Helpful tips and suggestions |
| 📊 | Statistics | Data statistics and metrics |
| 🔍 | Investigation | Dry-run mode, validation |
| ⏳  | Progress | Operation in progress |
| 📋 | Configuration | Config-related messages |
| 🔗 | Connection | Database connections |
| 📁 | Files | File operations |
| 📖 | Documentation | Links to docs |
| ⚡ | Performance | Speed and timing info |

---

### Scenario 1: First Successful Import

**Context**: User just created a project with `wareflow init` and placed Excel files in `data/` directory.

```bash
$ cd mon-entrepot
$ ls data/
produits.xlsx  mouvements.xlsx  commandes.xlsx

$ wareflow import
```

**Output**:
```
✓ Starting import process...

📋 Configuration loaded: config.yaml
🔗 Database: warehouse.db

Processing 3 import jobs:
  1/3 produits      (data/produits.xlsx)
  2/3 mouvements   (data/mouvements.xlsx)
  3/3 commandes    (data/commandes.xlsx)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ produits: 1,234 rows imported     [2.3s]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ mouvements: 45,678 rows imported   [8.7s]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ commandes: 789 rows imported       [1.1s]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%


✅ Import completed successfully!

📊 Summary:
  Total rows imported: 47,701
  Tables updated: 3
  Total time: 12.8 seconds

📈 Database status:
  produits:   1,234 rows
  mouvements: 45,678 rows
  commandes:    789 rows

💡 Next steps:
  wareflow analyze    # Run analyses
  wareflow status     # Check database status
```

---

### Scenario 2: Not in a Wareflow Project

**Context**: User runs command from random directory.

```bash
$ cd /random/directory
$ wareflow import
```

**Output**:
```
❌ Error: Not in a wareflow project

Reason: config.yaml not found in current directory

💡 Solutions:
  1. Navigate to your project directory: cd my-warehouse
  2. Or create a new project: wareflow init <project-name>

📖 For help: wareflow import --help
```

---

### Scenario 3: Missing Source Files

**Context**: User created project but hasn't placed Excel files yet.

```bash
$ cd mon-entrepot
$ ls data/
(empty)

$ wareflow import
```

**Output**:
```
✓ Starting import process...

📋 Configuration loaded: config.yaml
🔗 Database: warehouse.db

❌ Error: Source files not found

Missing files:
  ❌ data/produits.xlsx
  ❌ data/mouvements.xlsx
  ❌ data/commandes.xlsx

💡 Solution:
  Place your Excel files in the data/ directory:
    - produits.xlsx
    - mouvements.xlsx
    - commandes.xlsx

📖 Documentation: https://github.com/wareflowx/wareflow-analysis
```

---

### Scenario 4: Import with Warnings

**Context**: Files have minor issues (extra columns, format variations).

```bash
$ wareflow import
```

**Output**:
```
✓ Starting import process...

📋 Configuration loaded: config.yaml
🔗 Database: warehouse.db

Processing 3 import jobs...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ⚠️  produits: 1,234 rows imported   [2.3s]
     ⚠️  Warning: 3 columns ignored (EAN, Prix, Stock)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ mouvements: 45,678 rows imported    [8.7s]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ commandes: 789 rows imported        [1.1s]


⚠️  Import completed with warnings

📊 Summary:
  Total rows imported: 47,701
  Tables updated: 3
  Total time: 12.8 seconds
  Warnings: 1

⚠️  Warnings:
  produits.xlsx: Extra columns ignored (EAN, Prix, Stock)
    → These columns are not defined in the schema
    → Use --verbose to see all column names

💡 Next steps:
  wareflow analyze    # Run analyses
  wareflow status     # Check database status
```

---

### Scenario 5: Data Validation Errors

**Context**: Excel file contains invalid data (bad dates, negative quantities).

```bash
$ wareflow import
```

**Output**:
```
✓ Starting import process...

📋 Configuration loaded: config.yaml
🔗 Database: warehouse.db

Processing 3 import jobs...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ produits: 1,234 rows imported     [2.3s]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ❌ mouvements: IMPORT FAILED        [4.2s]

❌ Import failed: Data validation errors

📋 Error Details:
  Table: mouvements
  Source: data/mouvements.xlsx

  Invalid rows found:
    Row 156:    Invalid date "31/02/2025" in column date_heure
    Row 789:    Invalid date "2025-13-01" in column date_heure
    Row 1,234:  Negative quantity "-5" in column quantite
    Row 2,345:  Unknown product no_produit=99999

  Total: 4 invalid rows

💡 Solutions:
  1. Fix the data in your Excel file
  2. Run import again
  3. Or use --skip-invalid to skip problematic rows

📄 Error log: .wareflow/import_errors_20250121_143022.log

📖 Documentation: https://github.com/wareflowx/wareflow-analysis#data-validation
```

#### Option: --skip-invalid

```bash
$ wareflow import --skip-invalid
```

**Output**:
```
✓ Starting import process...

⚠️  Running in skip-invalid mode: invalid rows will be skipped

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ produits: 1,234 rows imported     [2.3s]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ⚠️  mouvements: 45,674 rows imported  [8.5s]
     ⚠️  Skipped: 4 invalid rows

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ commandes: 789 rows imported       [1.1s]


⚠️  Import completed with warnings

📊 Summary:
  Total rows imported: 47,697
  Rows skipped: 4
  Tables updated: 3
  Total time: 12.2 seconds

📄 Skipped rows log: .wareflow/skipped_rows_20250121_143045.log
```

---

### Scenario 6: Incremental Import (Update)

**Context**: User re-runs import after adding new movements.

```bash
$ wareflow import
```

**Output**:
```
✓ Starting import process...

📋 Configuration loaded: config.yaml
🔗 Database: warehouse.db

Processing 3 import jobs...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ produits: 0 new, 12 updated         [1.8s]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ mouvements: 234 new, 45,678 kept    [7.2s]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ commandes: 0 new, 789 kept          [0.9s]


✅ Import completed successfully!

📊 Summary:
  New rows: 246
  Updated rows: 12
  Unchanged rows: 46,467
  Total time: 10.3 seconds

📈 Database status:
  produits:   1,234 rows (+12 updated)
  mouvements: 45,912 rows (+234 new)
  commandes:    789 rows

💡 Last import: 2025-01-21 14:30:45
```

---

### Scenario 7: Pre-Import Validation (--dry-run)

**Context**: User wants to validate files before importing.

```bash
$ wareflow import --dry-run
```

**Output**:
```
🔍 Dry-run mode: No data will be imported

📋 Configuration: config.yaml
🔗 Database: warehouse.db

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📂 Source Files Analysis:

✅ data/produits.xlsx
  Size: 245 KB
  Sheets: 1
  Estimated rows: ~1,234
  Columns: 9
  ✓ All required columns present

✅ data/mouvements.xlsx
  Size: 8.2 MB
  Sheets: 1
  Estimated rows: ~45,678
  Columns: 19
  ✓ All required columns present

✅ data/commandes.xlsx
  Size: 156 KB
  Sheets: 1
  Estimated rows: ~789
  Columns: 16
  ✓ All required columns present

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Import Summary:
  Total files: 3
  Total estimated rows: 47,701
  Estimated time: ~15 seconds
  Database size increase: ~12 MB

✅ All checks passed! Ready to import.

💡 To proceed with the import:
  wareflow import
```

---

### Scenario 8: Verbose Mode (--verbose)

**Context**: User wants detailed technical information.

```bash
$ wareflow import --verbose
```

**Output**:
```
✓ Starting import process...

📋 Configuration loaded: config.yaml
🔗 Database: warehouse.db

[DEBUG] Parsing Excel file: data/produits.xlsx
[DEBUG] Sheet detected: Sheet1
[DEBUG] Columns found: no_produit, nom_produit, description, classe_produit, categorie_1, categorie_2, categorie_3, etat, configuration, ean_alternatif
[DEBUG] All required columns validated
[DEBUG] Data cleaning: 0 null values found
[DEBUG] Data types: no_produit=INTEGER, nom_produit=TEXT, ...

Processing 3 import jobs...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ produits: 1,234 rows imported     [2.3s]
     [INFO] Primary key: no_produit
     [INFO] Insert or replace: 1,234 rows
     [INFO] Transaction committed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ mouvements: 45,678 rows imported   [8.7s]
     [INFO] Primary key: oid
     [INFO] Validating foreign keys: no_produit → produits
     [INFO] FK validation passed: 45,678/45,678
     [INFO] Insert or replace: 45,678 rows
     [INFO] Transaction committed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ commandes: 789 rows imported       [1.1s]
     [INFO] Primary key: commande
     [INFO] Insert or replace: 789 rows
     [INFO] Transaction committed


✅ Import completed successfully!

📊 Summary:
  Total rows imported: 47,701
  Tables updated: 3
  Total time: 12.8 seconds

[DEBUG] Database checkpoint created
[DEBUG] Import log saved to: .wareflow/import_20250121_143022.log
```

---

### Scenario 9: Help Command (--help)

**Context**: User asks for help.

```bash
$ wareflow import --help
```

**Output**:
```
Import data from Excel files to SQLite database

USAGE:
  wareflow import [OPTIONS]

OPTIONS:
  --dry-run              Validate files without importing
  --skip-invalid         Skip invalid rows instead of failing
  --force                Force re-import of all data
  --verbose              Show detailed progress information
  --config PATH          Custom config file (default: config.yaml)
  --db PATH              Custom database path (default: warehouse.db)
  -h, --help             Show this message

EXAMPLES:
  wareflow import                          # Import all data
  wareflow import --dry-run                # Validate first
  wareflow import --skip-invalid           # Skip problematic rows
  wareflow import --verbose                # Show details

FILES REQUIRED:
  config.yaml    # Project configuration
  data/*.xlsx    # Excel files to import

💡 TIP: Run 'wareflow status' after import to verify data
```

---

### Scenario 10: Corrupted Database

**Context**: Database exists but is corrupted.

```bash
$ wareflow import
```

**Output**:
```
✓ Starting import process...

📋 Configuration loaded: config.yaml

❌ Error: Database corrupted

Details:
  File: warehouse.db
  Issue: SQLite database disk image is malformed

💡 Solutions:
  1. Restore from backup (if available)
  2. Reinitialize: rm warehouse.db && wareflow init .
  3. Use --recreate-db to recreate database

⚠️  WARNING: Option 2 will delete all existing data!

📖 Documentation: https://github.com/wareflowx/wareflow-analysis#troubleshooting
```

#### Option: --recreate-db

```bash
$ wareflow import --recreate-db
```

**Output**:
```
⚠️  WARNING: This will DELETE and RECREATE the database!

Database: warehouse.db
Current tables: produits, mouvements, commandes, receptions
Current rows: 47,701

Type 'yes' to confirm: yes

✓ Database deleted
✓ Database recreated with schema
✓ Starting import...

[Import proceeds normally...]
```

---

### Command Options Summary

| Option | Purpose | When to Use |
|--------|---------|-------------|
| `--dry-run` | Validate without importing | Before first import, after file changes |
| `--skip-invalid` | Skip problematic rows | When you have some bad data but want to import the rest |
| `--force` | Re-import all data | When you want to refresh entire database |
| `--verbose` | Show detailed info | When troubleshooting or debugging |
| `--config PATH` | Custom config file | When using non-standard configuration |
| `--db PATH` | Custom database | When using multiple databases |
| `--recreate-db` | Recreate database | When database is corrupted |

---

### Error Message Format

All error messages follow this structure:

```
❌ Error: [Short Description]

Details:
  [Technical details]

💡 Solutions:
  1. [First solution]
  2. [Second solution]
  3. [Third solution]

📖 Documentation: [Link to docs]
```

---

### Progress Display Format

Progress bars use ASCII characters for terminal compatibility:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
```

For files > 10MB, show percentage and ETA:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45% (ETA: 2.3s)
```

---

### Log Files

Log files are stored in `.wareflow/` directory:

| Log File | Purpose |
|----------|---------|
| `import_YYYYMMDD_HHMMSS.log` | Detailed import log (verbose mode) |
| `import_errors_YYYYMMDD_HHMMSS.log` | Validation errors |
| `skipped_rows_YYYYMMDD_HHMMSS.log` | Skipped rows details |
| `.wareflow/import_history.json` | Import history tracking |

---

## Conclusion

The `import` command is the **critical foundation** on which everything else depends. A robust implementation here will greatly facilitate future development.

**Key Success Factors**:
1. Proper error handling and validation
2. Clear progress feedback
3. Comprehensive test coverage
4. Well-documented code
5. Performance optimization

**Next Steps After Import**:
1. Implement `analyze` command with basic SQL queries
2. Implement `export` command with Excel generation
3. Implement `run` command for full pipeline
4. Add advanced analysis features

---

*Document created: 2025-01-21*
*Status: Implementation Plan - Ready for Development*
*Priority: HIGH - Critical for project progression*
