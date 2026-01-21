# Excel-to-SQL Integration

## Overview

This document explains how **excel-to-sql** integrates with the **wareflow-analysis** system and serves as the foundational data import/export layer.

## What is Excel-to-SQL?

**excel-to-sql** is a powerful CLI tool and Python SDK developed by wareflowx for importing Excel files into SQLite databases with advanced data transformation, validation, and quality profiling.

**Repository**: https://github.com/wareflowx/excel-to-sql
**Version**: 0.2.0+
**License**: MIT
**Language**: Python 3.10+

### Key Features

#### Core Functionality
- 📥 **Smart Import** - Import Excel files into SQLite with automatic schema detection
- 📤 **Flexible Export** - Export SQL data back to Excel with formatting
- 🔁 **Incremental Imports** - Only process changed files using content hashing
- 📑 **Multi-Sheet Support** - Import/export multiple sheets in one operation
- ⚡ **High Performance** - Powered by Pandas and SQLAlchemy 2.0
- 🔄 **UPSERT Logic** - Automatically insert new rows or update existing ones
- 🧹 **Data Cleaning** - Automatic whitespace trimming and empty row removal

#### Advanced Transformations
- 🔄 **Value Mapping** - Standardize data values (e.g., "ENTRÉE" → "inbound", "NY" → "New York")
- ➕ **Calculated Columns** - Create derived columns using expressions
- 🔗 **Reference Validation** - Foreign key validation against lookup tables
- 🎣 **Pre/Post Hooks** - Execute custom code during import/export pipeline

#### Data Validation
- ✅ **Custom Validators** - Range, regex, unique, not-null, enum validators
- 📏 **Validation Rules** - Declarative rule-based validation system
- 🔍 **Data Profiling** - Automatic quality analysis with detailed reports
- 🏷️ **Metadata Tracking** - Tag and categorize imports with rich metadata

#### Developer Experience
- 🐍 **Python SDK** - Full-featured programmatic API
- 🎯 **Type Hints** - Complete type annotations throughout
- 📚 **Well Documented** - Comprehensive documentation and examples
- 🧪 **Well Tested** - Extensive test coverage

---

## Integration with Wareflow-Analysis

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              WAREFLOW-ANALYSIS SYSTEM                        │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 1: DATA INFRASTRUCTURE (excel-to-sql)       │   │
│  │  - Excel/SQLite import/export                        │   │
│  │  - Data transformation & validation                   │   │
│  │  - Quality profiling                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 2: WAREFLOW DOMAIN LOGIC                      │   │
│  │  - Warehouse-specific analyses                        │   │
│  │  - KPI calculations                                  │   │
│  │  - Performance metrics                                │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Layer 3: REPORTING & EXPORT                         │   │
│  │  - Excel report generation                           │   │
│  │  - Visualization                                     │   │
│  │  - Business insights                                  │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Role in the System

**excel-to-sql** serves as the **data infrastructure layer**, providing:

1. **Data Ingestion**: Import Excel files into SQLite database
2. **Data Transformation**: Clean, map, and validate data
3. **Data Export**: Export database back to Excel when needed
4. **Quality Assurance**: Validate data quality and profile issues

**wareflow-analysis** builds on top of this foundation with:
- Warehouse-specific analyses
- Performance KPIs
- Operational metrics
- Tailored reports

---

## Why Use Excel-to-SQL?

### Benefits of Integration

#### 1. Accelerated Development

| Without excel-to-sql | With excel-to-sql |
|---------------------|-------------------|
| Implement import logic (5-7 days) | Use existing SDK (1-2 days) |
| Write transformation code | Use built-in features |
| Create validators from scratch | Use 12+ included validators |
| Build data profiling | Use existing profiling tools |
| **Total: 15-22 days** | **Total: 10-16 days** |

**Time Saved**: 5-6 days of development

#### 2. Richer Features Out-of-the-Box

By using excel-to-sql, wareflow-analysis immediately gains:

- ✅ **Value Mapping** - Essential for WMS code translation
- ✅ **Calculated Columns** - Combine split fields, derive metrics
- ✅ **Reference Validation** - FK validation against product tables
- ✅ **Data Profiling** - Quality reports on imported data
- ✅ **Incremental Imports** - Only process changed files
- ✅ **Multi-Sheet Support** - Handle complex Excel files

#### 3. Separation of Concerns

| Concern | excel-to-sql | wareflow-analysis |
|---------|--------------|-------------------|
| **Purpose** | Generic data import/export | Warehouse analytics |
| **Scope** | Universal Excel/SQLite | Warehouse-specific KPIs |
| **Target Users** | Any data professional | Warehouse managers |
| **Evolution** | Independent of wareflow | Focused on domain |

#### 4. Maintenance Benefits

- **Single Responsibility**: excel-to-sql focuses on data I/O
- **Independent Updates**: Can upgrade excel-to-sql without touching wareflow
- **Code Reuse**: Multiple projects can benefit from excel-to-sql
- **Less Code to Maintain**: wareflow-analysis has less code to manage

---

## Technical Integration

### Dependency Management

#### pyproject.toml

```toml
[project]
name = "wareflow-analysis"
version = "0.1.1"
description = "Warehouse data analysis CLI tool"
requires-python = ">=3.10"
dependencies = [
    "typer>=0.21",
    "pandas>=2.0",
    "openpyxl>=3.0",
    "excel-to-sql>=0.2.0",  # ← Data import/export layer
    "pyyaml>=6.0",           # ← Configuration parsing
]
```

#### Installation

```bash
# Install wareflow-analysis with all dependencies
pip install wareflow-analysis

# excel-to-sql will be installed automatically
```

---

## Configuration

### Mapping excel-to-sql to Wareflow Structure

The wareflow `config.yaml` needs to be compatible with excel-to-sql's expected format.

#### Option A: Native excel-to-sql Format (Recommended)

**File**: `templates/config.yaml`

```yaml
# Wareflow Analysis Configuration
# Generated by wareflow-analysis
# Compatible with excel-to-sql v0.2.0+

mappings:
  produits:
    target_table: produits
    source: data/produits.xlsx
    primary_key:
      - no_produit

    column_mappings:
      # Auto-detect columns, but can specify explicit mappings
      no_produit:
        target: no_produit
        type: integer
      nom_produit:
        target: nom_produit
        type: string
      etat:
        target: etat
        type: string

    value_mappings:
      # Map French WMS codes to English
      etat:
        ACTIF: active
        INACTIF: inactive

    validation_rules:
      - column: no_produit
        type: unique
      - column: nom_produit
        type: not_null

  mouvements:
    target_table: mouvements
    source: data/mouvements.xlsx
    primary_key:
      - oid

    column_mappings:
      oid:
        target: oid
        type: integer
      no_produit:
        target: no_produit
        type: integer
        reference:
          table: produits
          column: no_produit
      type:
        target: type
        type: string

    value_mappings:
      # Map French movement types to English
      type:
        ENTRÉE: inbound
        SORTIE: outbound
        TRANSFERT: transfer
        AJUSTEMENT: adjustment

    calculated_columns:
      - name: date_heure_clean
        expression: COALESCE(date_heure_2, date_heure)

    validation_rules:
      - column: oid
        type: unique
      - column: no_produit
        type: reference
        params:
          table: produits
          column: no_produit

  commandes:
    target_table: commandes
    source: data/commandes.xlsx
    primary_key:
      - commande

    column_mappings:
      commande:
        target: commande
        type: string
      etat:
        target: etat
        type: string

    value_mappings:
      # Map order statuses
      etat:
        EN_COURS: pending
        TERMINÉ: completed
        ANNULÉ: cancelled

    calculated_columns:
      - name: etat_combine
        # Combine split status fields
        expression: |
          CASE
            WHEN etat_superieur IS NOT NULL THEN etat_superieur
            WHEN etat_inferieur IS NOT NULL THEN etat_inferieur
            ELSE etat
          END
```

#### Option B: Simplified Wareflow Format

**File**: `templates/config.yaml`

```yaml
# Simplified wareflow configuration
# Will be converted to excel-to-sql format by importer

database:
  path: warehouse.db

imports:
  produits:
    source: data/produits.xlsx
    table: produits
    primary_key: no_produit

    # Wareflow-specific transformations
    transformations:
      value_mappings:
        etat:
          ACTIF: active
          INACTIF: inactive

  mouvements:
    source: data/mouvements.xlsx
    table: mouvements
    primary_key: oid

    transformations:
      value_mappings:
        type:
          ENTRÉE: inbound
          SORTIE: outbound
          TRANSFERT: transfer

      calculated_columns:
        date_heure_clean: COALESCE(date_heure_2, date_heure)

  commandes:
    source: data/commandes.xlsx
    table: commandes
    primary_key: commande

    transformations:
      value_mappings:
        etat:
          EN_COURS: pending
          TERMINÉ: completed
```

---

## Implementation

### Using the Excel-to-SQL SDK

**File**: `src/wareflow_analysis/import/importer.py`

```python
"""Wareflow import command using excel-to-sql SDK."""

from pathlib import Path
from typing import Tuple
import yaml

class WareflowImporter:
    """Importer using excel-to-sql SDK."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.config_path = project_dir / "config.yaml"

    def run_import(self) -> Tuple[bool, str]:
        """Execute import using excel-to-sql."""

        if not self.config_path.exists():
            return False, "config.yaml not found"

        # Load wareflow config
        config = self._load_config()

        # Convert to excel-to-sql format if needed
        excel_to_sql_config = self._convert_config(config)

        # Use excel-to-sql SDK
        from excel_to_sql import ExcelToSqlite

        db_path = self.project_dir / config['database']['path']
        sdk = ExcelToSqlite(db_path=str(db_path))

        try:
            # Import each mapping
            results = []
            for mapping_name, mapping_config in excel_to_sql_config['mappings'].items():
                result = sdk.import_excel(
                    file_path=mapping_config['source'],
                    mapping_name=mapping_name,
                    mapping_config=mapping_config
                )
                results.append(result)

            total_rows = sum(r.get('rows_imported', 0) for r in results)
            return True, f"Imported {total_rows:,} rows from {len(results)} files"

        except Exception as e:
            return False, f"Import failed: {e}"

    def _load_config(self) -> dict:
        """Load wareflow configuration."""
        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def _convert_config(self, wareflow_config: dict) -> dict:
        """Convert wareflow config to excel-to-sql format."""

        excel_to_sql_config = {"mappings": {}}

        for import_name, import_config in wareflow_config.get('imports', {}).items():
            excel_to_sql_config['mappings'][import_name] = {
                "target_table": import_config['table'],
                "source": import_config['source'],
                "primary_key": [import_config['primary_key']],
                "column_mappings": {},
            }

            # Add transformations if present
            if 'transformations' in import_config:
                transformations = import_config['transformations']

                # Value mappings
                if 'value_mappings' in transformations:
                    excel_to_sql_config['mappings'][import_name]['value_mappings'] = []
                    for column, mappings in transformations['value_mappings'].items():
                        excel_to_sql_config['mappings'][import_name]['value_mappings'].append({
                            "column": column,
                            "mappings": mappings
                        })

                # Calculated columns
                if 'calculated_columns' in transformations:
                    excel_to_sql_config['mappings'][import_name]['calculated_columns'] = []
                    for col_name, expression in transformations['calculated_columns'].items():
                        excel_to_sql_config['mappings'][import_name]['calculated_columns'].append({
                            "name": col_name,
                            "expression": expression
                        })

        return excel_to_sql_config
```

### Alternative: Direct CLI Call

**File**: `src/wareflow_analysis/import/importer.py`

```python
"""Wareflow import command using excel-to-sql CLI."""

import subprocess
from pathlib import Path
from typing import Tuple

def run_import(project_dir: Path) -> Tuple[bool, str]:
    """Execute import by calling excel-to-sql CLI."""

    config_path = project_dir / "config.yaml"

    if not config_path.exists():
        return False, "config.yaml not found"

    # Call excel-to-sql CLI
    result = subprocess.run(
        ["excel-to-sql", "import", "--config", str(config_path)],
        capture_output=True,
        text=True,
        cwd=project_dir
    )

    if result.returncode == 0:
        return True, result.stdout
    else:
        return False, result.stderr
```

---

## Wareflow-Specific Features

### Handling WMS Data Quirks

French WMS systems have specific characteristics that excel-to-sql features handle perfectly:

#### 1. French WMS Codes

**Problem**: Source data uses French codes
```python
# Source: mouvements.xlsx
type: "ENTRÉE", "SORTIE", "TRANSFERT"
```

**Solution**: Value mapping
```yaml
value_mappings:
  type:
    ENTRÉE: inbound
    SORTIE: outbound
    TRANSFERT: transfer
```

#### 2. Split Status Fields

**Problem**: Status split across 3 columns
```python
# Source: commandes.xlsx
etat_superieur: "TERMINÉ"
etat_inferieur: null
etat: null
```

**Solution**: Calculated column with COALESCE
```yaml
calculated_columns:
  - name: etat_combine
    expression: |
      COALESCE(etat_superieur, etat_inferieur, etat)
```

#### 3. Reference Validation

**Problem**: Movements reference products that might not exist

**Solution**: Reference validator
```yaml
validation_rules:
  - column: no_produit
    type: reference
    params:
      table: produits
      column: no_produit
```

---

## Data Flow with excel-to-sql

### Complete Pipeline

```
┌─────────────────────────────────────────────────────┐
│ 1. EXCEL SOURCE FILES                              │
│    - data/produits.xlsx                            │
│    - data/mouvements.xlsx                           │
│    - data/commandes.xlsx                            │
└──────────────┬──────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────┐
│ 2. EXCEL-TO-SQL (Data Infrastructure Layer)        │
│    ✓ Read Excel files                               │
│    ✓ Apply value mappings                            │
│    ✓ Calculate derived columns                      │
│    ✓ Validate references                             │
│    ✓ Clean and profile data                         │
│    ✓ UPSERT to SQLite                                │
└──────────────┬──────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────┐
│ 3. WAREFLOW.DB (SQLite Database)                    │
│    ✓ produits, mouvements, commandes               │
│    ✓ Clean and validated data                       │
│    ✓ Quality metadata                               │
└──────────────┬──────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────┐
│ 4. WAREFLOW-ANALYSIS (Domain Logic Layer)          │
│    ✓ Warehouse-specific analyses                   │
│    ✓ Performance KPIs                              │
│    ✓ Operational metrics                           │
└──────────────┬──────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────────────────┐
│ 5. EXCEL REPORTS (Export Layer)                   │
│    ✓ Multi-sheet reports                           │
│    ✓ Charts and visualizations                      │
│    ✓ Business insights                             │
└─────────────────────────────────────────────────────┘
```

---

## Examples

### Example 1: Basic Import

```bash
# Initialize project
$ wareflow init mon-entrepot
$ cd mon-entrepot

# Place Excel files in data/
$ cp /path/to/produits.xlsx data/
$ cp /path/to/mouvements.xlsx data/
$ cp /path/to/commandes.xlsx data/

# Run import (uses excel-to-sql under the hood)
$ wareflow import

✓ Starting import process...
📋 Configuration loaded: config.yaml
🔗 Database: warehouse.db

Processing 3 import jobs...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ produits: 1,234 rows imported     [2.3s]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ mouvements: 45,678 rows imported   [8.7s]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
  ✓ commandes: 789 rows imported       [1.1s]


✅ Import completed successfully!

📊 Summary:
  Total rows imported: 47,701
  Tables updated: 3
  Data quality score: 98.5%
```

### Example 2: Import with Validation

```bash
$ wareflow import --verbose

✓ Starting import process...
[DEBUG] Loading excel-to-sql SDK
[DEBUG] Config: 3 mappings defined

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 produits
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[INFO] Reading: data/produits.xlsx
[INFO] Applying value mappings: etat
[INFO] Validating references: none
[INFO] Quality profiling: 0 errors, 3 warnings
  ⚠️  Warning: 156 products have null description
[INFO] Imported: 1,234 rows
```

### Example 3: Incremental Import

```bash
# First import
$ wareflow import
✅ 47,701 rows imported

# Add new movements to Excel file
# (only 234 new rows added)

# Run import again (incremental)
$ wareflow import

✓ Import completed successfully!
  Mode: incremental
  New rows: 234
  Updated rows: 12
  Skipped rows: 47,455
  Time: 2.1 seconds (vs 12.8s for full)
```

---

## Data Quality Features

### Profiling Reports

excel-to-sql provides automatic data quality profiling:

```bash
# After import, get quality report
$ excel-to-sql profile --table mouvements --output quality-report.html

✓ Quality report generated: quality-report.html

# Report includes:
# - Null percentage per column
# - Unique value counts
# - Data type distribution
# - Outlier detection
# - Reference integrity check
```

### Validation Results

```bash
$ excel-to-sql status

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 DATA QUALITY STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Table: produits
  Quality Score: 98.5%
  Issues: 3
    ⚠️  156 null descriptions (12.6%)
    ⚠️  23 invalid dates
    ⚠️  1 duplicate product ID

Table: mouvements
  Quality Score: 99.2%
  Issues: 2
    ⚠️  4 unknown product references
    ⚠️  89 future dates

Table: commandes
  Quality Score: 100%
  Issues: 0
  ✅ Perfect data quality
```

---

## Best Practices

### 1. Configuration Management

**Use version control for configs**:
```bash
# Track configuration changes
git add config.yaml
git commit -m "Update product mappings"
```

**Use environment-specific configs**:
```bash
# Development
config.dev.yaml

# Production
config.prod.yaml
```

### 2. Value Mapping Standards

**Standardize codes early**:
```yaml
value_mappings:
  # Always use English canonical values
  etat:
    ACTIF: active
    INACTIF: inactive
    EN_ATTENTE: pending
  type:
    ENTRÉE: inbound
    SORTIE: outbound
```

### 3. Validation Strategy

**Validate early and often**:
```yaml
validation_rules:
  # Critical: unique primary keys
  - column: no_produit
    type: unique

  # Important: referential integrity
  - column: no_produit
    type: reference
    params:
      table: produits
      column: no_produit

  # Nice to have: data quality
  - column: quantite
    type: range
    params:
      min: 0
      max: 1000000
```

### 4. Incremental Imports

**Track file changes**:
```bash
# excel-to-sql automatically tracks file hashes
# Only reimports changed files

$ wareflow import
✓ Checking file modifications...
  produits.xlsx: unchanged (skipped)
  mouvements.xlsx: modified (234 new rows)
  commandes.xlsx: unchanged (skipped)

  Processing: 1/3 files
```

---

## Troubleshooting

### Common Issues

#### Issue 1: excel-to-sql not found

```bash
$ wareflow import
❌ Error: excel-to-sql command not found

💡 Solution:
  pip install excel-to-sql
```

#### Issue 2: Configuration format mismatch

```bash
$ wareflow import
❌ Error: Invalid config format

💡 Solution:
  Check config.yaml matches excel-to-sql expected format
  See: https://github.com/wareflowx/excel-to-sql#configuration
```

#### Issue 3: Validation errors

```bash
$ wareflow import
❌ Validation failed: 4 unknown product references

💡 Solution:
  1. Fix data in Excel files
  2. Or use --skip-validation flag
  3. Or add products table first
```

---

## Migration from Custom Import

### If Custom Code Was Written

If you started implementing custom import logic before discovering excel-to-sql:

**Benefits of switching**:
- ✅ Less code to maintain
- ✅ More features (value mapping, validators, profiling)
- ✅ Better error handling
- ✅ Continuous improvements from excel-to-sql updates

**Migration steps**:
1. Install excel-to-sql
2. Convert config.yaml to excel-to-sql format
3. Update import command to use SDK
4. Remove custom import code
5. Test thoroughly

---

## Version Compatibility

### excel-to-sql Versions

| Version | Features Used by wareflow | Status |
|---------|----------------------------|--------|
| 0.1.x | Basic import/export | ❌ Too limited |
| **0.2.0** | All required features | ✅ **Recommended** |
| 0.3.x+ | Future enhancements | ✅ Compatible |

**Minimum required version**: excel-to-sql >= 0.2.0

---

## Conclusion

**excel-to-sql** is the **foundational data layer** that makes wareflow-analysis possible. By using excel-to-sql:

1. **Faster development** - Save 5-6 days of initial work
2. **Richer features** - Advanced transformations and validation
3. **Better separation** - Generic I/O separated from domain logic
4. **Easier maintenance** - Less code to maintain in wareflow-analysis
5. **Continuous improvement** - Benefit from excel-to-sql updates

The **wareflow-analysis** project can focus on what makes it unique: **warehouse analytics and insights**, while relying on excel-to-sql for robust data import/export.

---

## Next Steps

1. **Install excel-to-sql**:
   ```bash
   pip install excel-to-sql>=0.2.0
   ```

2. **Update import.md** feature document to reflect excel-to-sql integration

3. **Test integration** with sample warehouse data

4. **Update templates/config.yaml** to use excel-to-sql format

5. **Implement import command** using SDK (1-2 days)

---

*Document created: 2025-01-21*
*Related: [import.md](features/import.md), [analyze.md](features/analyze.md), [export.md](features/export.md), [run.md](features/run.md)*
*excel-to-sql: https://github.com/wareflowx/excel-to-sql*
