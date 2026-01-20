# Wareflow Analysis - Pragmatic Implementation Plan

## Objective

Create a functional analysis system for **a single warehouse** with a globally extensible architecture.

**Approach**: Implement global functionality first, extend with specific data later.

---

## The Wareflow CLI Approach

Instead of manually creating project structure, use a **CLI tool** that initializes everything.

### Installation

```bash
pip install wareflow-analysis
```

### Initialize a New Project

```bash
wareflow init my-warehouse
```

This single command creates a complete project structure (see below).

### CLI Commands

```bash
wareflow init <project-name>     # Initialize new project
wareflow import                  # Import data from Excel files
wareflow analyze                 # Run all analyses
wareflow export                  # Generate Excel reports
wareflow run                     # Full pipeline (import → analyze → export)
wareflow status                  # Show database status
```

---

## Two Different Structures

### 1. CLI Package Structure (installed via pip)

The code of the `wareflow-analysis` tool itself:

```
wareflow-analysis/              (PyPI package)
├── wareflow/
│   ├── __init__.py
│   ├── cli.py                  # Typer CLI implementation
│   ├── init.py                 # Init command logic (copy files)
│   ├── import.py               # Import command (calls excel-to-sql)
│   ├── analyze.py              # Analyze command (runs SQL views)
│   ├── export.py               # Export command (generates Excel)
│   ├── run.py                  # Full pipeline orchestrator
│   ├── status.py               # Status command
│   ├── templates/              # Static files to copy (no template engine)
│   │   ├── config.yaml
│   │   ├── schema.sql
│   │   ├── import.py           # User's import script
│   │   ├── analyze.py          # User's analysis script
│   │   ├── export.py           # User's export script
│   │   └── README.md
│   └── schema/
│       ├── base.sql            # Core database schema
│       ├── views.sql           # Predefined analysis views
│       └── indexes.sql         # Database indexes
├── setup.py
└── README.md
```

**Purpose**: This is the **software package** that users install once. Contains all the logic and templates to create projects.

### 2. User Project Structure (created by `wareflow init`)

What gets created when a user runs `wareflow init my-warehouse`:

```
my-warehouse/                   (user's project)
├── config.yaml                 # excel-to-sql configuration (copied from templates)
├── schema.sql                  # Database schema (copied from templates)
├── scripts/
│   ├── import.py               # Import script (copied from templates)
│   ├── analyze.py              # Analysis script (copied from templates)
│   └── export.py               # Export script (copied from templates)
├── data/
│   ├── .gitkeep
│   ├── produits.xlsx           # User places their files here
│   ├── mouvements.xlsx
│   └── commandes.xlsx
├── output/
│   └── .gitkeep                # Generated reports go here
├── warehouse.db                # Empty SQLite database (created with schema.sql)
└── README.md                   # Quick start guide (copied from templates)
```

**Purpose**: This is the **user's project** for a specific warehouse. Contains their data and configuration.

---

## How It Works

### When user runs `wareflow init my-warehouse`

1. Create directory `my-warehouse/`
2. Create subdirectories: `data/`, `output/`, `scripts/`
3. Copy static files from `wareflow/templates/` to project:
   - `config.yaml`
   - `schema.sql`
   - `scripts/import.py`
   - `scripts/analyze.py`
   - `scripts/export.py`
   - `README.md`
4. Create empty SQLite database using `wareflow/schema/base.sql`
5. Create `.gitkeep` files in empty directories

### When user runs `wareflow import`

1. Read `config.yaml` in current directory
2. Call `excel-to-sql import --config config.yaml`
3. Import data from `data/*.xlsx` to `warehouse.db`

### When user runs `wareflow analyze`

1. Connect to `warehouse.db`
2. Execute views from `wareflow/schema/views.sql`
3. Create/update analysis views in database

### When user runs `wareflow export`

1. Connect to `warehouse.db`
2. Query analysis views
3. Generate Excel reports in `output/`

### When user runs `wareflow run`

Execute: `import` → `analyze` → `export` (full pipeline)

---

## What We Have (Current Schema)

### Available Tables
- **produits**: Global product catalog (no_produit INTEGER)
- **mouvements**: All stock movements with timestamps
- **commandes**: Customer orders with statuses
- **receptions**: Supplier receipts

### What We Don't Have (for now)
- Stock/inventory table
- Explicit warehouse identification
- Performance time block tracking

**Strategy**: Work with what we have, add the rest later.

---

## Simplified Architecture

```
┌─────────────────────────────────────────────────┐
│  EXCEL SOURCE FILES                             │
│  - produits.xlsx                                │
│  - mouvements.xlsx                              │
│  - commandes.xlsx                               │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│  EXCEL-TO-SQL (v0.2.0)                          │
│  - Automatic import with mappings              │
│  - Data validation                              │
│  - Transformations (values, calculations)       │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│  WAREFLOW.DB (SQLite)                           │
│  - produits, mouvements, commandes              │
│  - Materialized views (analyses)                │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│  AUTOMATED ANALYSES                             │
│  - Performance by task type                     │
│  - Global KPIs                                  │
│  - Product performance                          │
└────────────────┬────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────┐
│  EXPORT REPORTS                                 │
│  - Multi-sheet Excel files                      │
│  - Charts and KPIs                              │
└─────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: CLI Foundation (Week 1)

**Objective**: Create a working `wareflow` CLI package with `init` command functional

**Success Criteria**:
- Can install with `pip install`
- `wareflow init test-project` creates complete project structure
- Created project has all files and empty database
- Can run `wareflow --version` and `wareflow --help`

---

## 1.1 Package Dependencies

**Package Manager**: `uv` (modern Python package manager)

**Core dependencies**:
```python
# pyproject.toml
dependencies = [
    "typer>=0.9",           # Modern CLI framework (type-friendly)
    "excel-to-sql>=0.2.0",  # Excel to SQL import
    "pandas>=2.0",          # Data manipulation
    "openpyxl>=3.0",        # Excel write
]
```

**Dev dependencies**:
```python
[dependency-groups]
dev = [
    "pytest>=7.0",          # Testing
    "pytest-cov",           # Coverage
    "ruff>=0.1",            # Linting and formatting (uv-compatible)
]
```

**Why uv and typer**:
- `uv`: Fast package manager (10-100x faster than pip), better dependency resolution
- `typer`: Modern CLI library built on typer, great editor support, less boilerplate

---

## 1.2 CLI Command Specifications

### `wareflow init <project-name>`

**What it does**:
1. Validate project name (no special chars, not empty)
2. Check if directory already exists
3. Create project directory structure
4. Copy all template files to project
5. Create empty SQLite database with schema
6. Create `.gitkeep` files in empty directories
7. Print success message with next steps

**Error handling**:
- Directory exists → Error with message
- Invalid project name → Error with constraints
- Permission denied → Error with message
- Missing templates → Error

**Output**:
```
✓ Project 'my-warehouse' created successfully!

Next steps:
  cd my-warehouse
  # Place your Excel files in data/ directory
  wareflow import
```

### `wareflow --version`

**Output**:
```
wareflow-analysis v0.1.0
```

### `wareflow --help`

**Output**:
```
Wareflow Analysis - Warehouse data analysis CLI

Usage: wareflow [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show version and exit
  --help     Show this message and exit

Commands:
  init     Initialize a new Wareflow analysis project
  import   Import data from Excel files to SQLite
  analyze  Run all analyses
  export   Generate Excel reports
  run      Run full pipeline (import → analyze → export)
  status   Show database status
```

---

## 1.3 Template Files Content

### config.yaml (template)

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

### schema.sql (template)

```sql
-- Wareflow Analysis Schema
-- Core database schema

-- Products table
CREATE TABLE produits (
    no_produit INTEGER PRIMARY KEY,
    nom_produit TEXT,
    description TEXT,
    classe_produit TEXT,
    categorie_1 TEXT,
    categorie_2 TEXT,
    categorie_3 TEXT,
    etat TEXT,
    configuration TEXT,
    ean_alternatif TEXT
);

-- Movements table
CREATE TABLE mouvements (
    oid INTEGER PRIMARY KEY,
    no_produit INTEGER,
    nom_produit TEXT,
    type TEXT,
    site_source TEXT,
    zone_source TEXT,
    localisation_source TEXT,
    conteneur_source TEXT,
    site_cible TEXT,
    zone_cible TEXT,
    localisation_cible TEXT,
    conteneur_cible TEXT,
    quantite_uoi TEXT,
    quantite INTEGER,
    unite TEXT,
    date_heure DATETIME,
    usager TEXT,
    raison REAL,
    lot_expiration REAL,
    date_expiration REAL,
    date_heure_2 TEXT,
    FOREIGN KEY (no_produit) REFERENCES produits(no_produit)
);

-- Orders table
CREATE TABLE commandes (
    commande TEXT PRIMARY KEY,
    type_commande TEXT,
    demandeur TEXT,
    destinataire TEXT,
    no_destinataire INTEGER,
    priorite INTEGER,
    vague TEXT,
    date_requise DATETIME,
    lignes INTEGER,
    chargement TEXT,
    transporteur TEXT,
    etat_inferieur TEXT,
    etat_superieur TEXT,
    etat TEXT,
    statut_prepositionnement_max TEXT,
    statut_prepositionnement_actuel TEXT
);

-- Receptions table
CREATE TABLE receptions (
    no_reference INTEGER PRIMARY KEY,
    reception INTEGER,
    quantite_recue INTEGER,
    produit INTEGER,
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

-- Indexes
CREATE INDEX idx_mouvements_produit ON mouvements(no_produit);
CREATE INDEX idx_mouvements_date ON mouvements(date_heure);
CREATE INDEX idx_mouvements_usager ON mouvements(usager);
CREATE INDEX idx_mouvements_type ON mouvements(type);
```

### scripts/import.py (template)

```python
"""
Wareflow Import Script
Import Excel files to SQLite database
"""
import subprocess
import sys
from pathlib import Path

def run_import():
    """Run excel-to-sql import"""
    config_path = Path("config.yaml")

    if not config_path.exists():
        print("Error: config.yaml not found!")
        print("Are you in a wareflow project directory?")
        sys.exit(1)

    print("Importing data from Excel files...")
    result = subprocess.run(
        ["excel-to-sql", "import", "--config", "config.yaml"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Import failed: {result.stderr}")
        sys.exit(1)

    print("✓ Import completed!")
    print(result.stdout)

if __name__ == "__main__":
    run_import()
```

### scripts/analyze.py (template)

```python
"""
Wareflow Analyze Script
Run analysis views on database
"""
import sqlite3
from pathlib import Path

def run_analyses():
    """Run all analysis views"""
    db_path = Path("warehouse.db")

    if not db_path.exists():
        print("Error: warehouse.db not found!")
        print("Run 'wareflow import' first.")
        return

    print("Running analyses...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get table info
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print(f"\nTables in database: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")

    # Get row counts
    print("\nRow counts:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  {table[0]}: {count:,} rows")

    conn.close()
    print("\n✓ Analyses completed!")

if __name__ == "__main__":
    run_analyses()
```

### scripts/export.py (template)

```python
"""
Wareflow Export Script
Generate Excel reports from database
"""
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

def run_export():
    """Generate Excel reports"""
    db_path = Path("warehouse.db")

    if not db_path.exists():
        print("Error: warehouse.db not found!")
        print("Run 'wareflow import' first.")
        return

    print("Generating Excel reports...")
    conn = sqlite3.connect(db_path)

    # Simple export: all tables
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"report_{timestamp}.xlsx"

    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for table in tables:
            df = pd.read_sql(f"SELECT * FROM {table} LIMIT 1000", conn)
            df.to_excel(writer, sheet_name=table[:31], index=False)  # Excel limit

    conn.close()
    print(f"✓ Report generated: {output_file}")

if __name__ == "__main__":
    run_export()
```

### README.md (template)

```markdown
# Wareflow Analysis Project

Warehouse data analysis project generated by wareflow-analysis CLI.

## Quick Start

1. Place your Excel files in the `data/` directory:
   - produits.xlsx
   - mouvements.xlsx
   - commandes.xlsx

2. Import data:
   ```bash
   wareflow import
   ```

3. Run analyses:
   ```bash
   wareflow analyze
   ```

4. Generate reports:
   ```bash
   wareflow export
   ```

## Full Pipeline

Run everything at once:
```bash
wareflow run
```

## Project Structure

- `config.yaml` - Configuration for excel-to-sql
- `data/` - Place your Excel source files here
- `output/` - Generated reports will be saved here
- `scripts/` - Analysis and export scripts
- `warehouse.db` - SQLite database

## Commands

- `wareflow import` - Import Excel data to SQLite
- `wareflow analyze` - Run database analyses
- `wareflow export` - Generate Excel reports
- `wareflow run` - Run full pipeline
- `wareflow status` - Show database status
```

---

## 1.4 Package Files Structure

### pyproject.toml

```toml
[project]
name = "wareflow-analysis"
version = "0.1.0"
description = "Warehouse data analysis CLI tool"
readme = "README.md"
requires-python = ">=3.8"
authors = [
    { name = "Wareflow Team" }
]
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]

dependencies = [
    "typer>=0.9",
    "excel-to-sql>=0.2.0",
    "pandas>=2.0",
    "openpyxl>=3.0",
]

[project.scripts]
wareflow = "wareflow.cli:cli"

[dependency-groups]
dev = [
    "pytest>=7.0",
    "pytest-cov",
    "ruff>=0.1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py38"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### README.md (package)

```markdown
# Wareflow Analysis CLI

CLI tool for warehouse data analysis automation.

## Installation

```bash
pip install wareflow-analysis
```

## Usage

```bash
# Create a new project
wareflow init my-warehouse

# Use the project
cd my-warehouse
wareflow import
wareflow analyze
wareflow export
```

## Commands

- `wareflow init <name>` - Initialize new project
- `wareflow import` - Import Excel data
- `wareflow analyze` - Run analyses
- `wareflow export` - Generate reports
- `wareflow run` - Full pipeline
```

---

## 1.5 Testing Strategy

### Unit Tests

**test_init.py**:
```python
def test_init_creates_directory():
    """Test that init creates project directory"""
    pass

def test_init_copies_templates():
    """Test that all template files are copied"""
    pass

def test_init_creates_database():
    """Test that empty database is created"""
    pass

def test_init_existing_directory_fails():
    """Test that init fails if directory exists"""
    pass
```

### Integration Tests

**test_cli.py**:
```python
def test_cli_help():
    """Test that --help works"""
    pass

def test_cli_version():
    """Test that --version works"""
    pass

def test_full_init_flow():
    """Test complete init workflow"""
    pass
```

---

## 1.6 Development Workflow

### Local Development

```bash
# Install uv (one time)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or on Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Create project and install dependencies
uv sync

# Run CLI
uv run wareflow --version
uv run wareflow init test-project

# Run tests
uv run pytest

# Format and lint
uv run ruff check wareflow/
uv run ruff format wareflow/
```

### Building Package

```bash
# Build package with uv
uv build

# Test locally
uv pip install dist/wareflow_analysis-0.1.0-py3-none-any.whl

# Or publish to PyPI
uv publish
```

### Why uv vs pip

**uv advantages**:
- 10-100x faster than pip
- Built-in dependency management (no separate venv needed)
- Better lock files (like Cargo for Rust)
- Unified tooling (sync, build, publish, run)
- Modern Python tooling (pyproject.toml first)

---

## 1.7 Phase 1 Checklist

### Package Structure
- [ ] Create package directory structure
- [ ] Create setup.py with dependencies
- [ ] Create README.md for package
- [ ] Add entry point for CLI

### CLI Implementation
- [ ] Create cli.py with Typer framework
- [ ] Implement --version command
- [ ] Implement --help command
- [ ] Implement all command stubs (init, import, analyze, export, run, status)

### Init Command
- [ ] Implement init.py with directory creation logic
- [ ] Create all template files (config.yaml, schema.sql, scripts/*.py, README.md)
- [ ] Implement file copying logic
- [ ] Implement database creation with schema
- [ ] Add error handling (existing dir, invalid name, permissions)

### Testing
- [ ] Write unit tests for init
- [ ] Write integration tests for CLI
- [ ] Test local installation
- [ ] Test package build

### Documentation
- [ ] Document CLI commands
- [ ] Document project structure
- [ ] Document template files
- [ ] Create usage examples

---

## 1.8 Success Verification

After completing Phase 1, user should be able to:

```bash
# Clone/download package
git clone https://github.com/user/wareflow-analysis
cd wareflow-analysis

# Install with uv
uv sync

# Check it works
uv run wareflow --version
# Output: wareflow-analysis v0.1.0

# Create project
uv run wareflow init test-warehouse
# Output: ✓ Project 'test-warehouse' created successfully!

# Verify structure
cd test-warehouse
ls -la
# Shows: config.yaml, schema.sql, scripts/, data/, output/, warehouse.db, README.md

# Verify database
sqlite3 warehouse.db .tables
# Shows: produits, mouvements, commandes, receptions

# Run help
uv run wareflow --help
# Shows all commands with descriptions
```

---

*Document created: 2025-01-20*
*Last updated: 2025-01-20*
*Approach: Pragmatic and scalable*
*Focus: CLI foundation first, then incremental feature development*
*Tech stack: uv (package manager) + typer (CLI framework)*
