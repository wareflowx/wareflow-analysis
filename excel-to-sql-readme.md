# Excel to SQLite

A powerful CLI tool and Python SDK for importing Excel files into SQLite databases with advanced data transformation, validation, and quality profiling features.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/badge/pypi/v-excel--to--sql-blue)](https://pypi.org/project/excel-to-sql/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Overview

Excel to SQLite simplifies the process of importing Excel data into SQLite databases. It provides automatic schema detection, data transformations, validation rules, and includes an intelligent Auto-Pilot mode for zero-configuration setup.

**Key Features:**
- Smart Import with automatic schema detection
- Flexible data transformations (value mappings, calculated columns)
- Comprehensive validation system
- Data quality profiling and scoring
- Auto-Pilot mode with pattern detection
- Python SDK for programmatic access
- Rich terminal output with detailed progress reporting

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Python SDK](#python-sdk)
- [Auto-Pilot Mode](#auto-pilot-mode)
- [Configuration](#configuration)
- [Examples](#examples)
- [Development](#development)
- [Contributing](#contributing)
- [Changelog](#changelog)
- [License](#license)

## Installation

### From PyPI

```bash
pip install excel-to-sql
```

### With uv

```bash
uv pip install excel-to-sql
```

### From Source

```bash
git clone https://github.com/wareflowx/excel-to-sql.git
cd excel-to-sql
uv sync
```

## Quick Start

Excel to SQLite provides two ways to get started: choose **Auto-Pilot** for automatic setup or **Manual Configuration** for complete control.

### Option 1: Auto-Pilot Mode (Recommended)

The fastest way to import Excel files. Auto-Pilot automatically detects patterns, suggests transformations, and guides you through the setup.

```bash
# Analyze Excel files and generate configuration automatically
excel-to-sql magic --data ./path/to/excels

# Interactive mode with step-by-step guidance
excel-to-sql magic --data ./path/to/excels --interactive

# Dry run to analyze without generating configuration
excel-to-sql magic --data ./path/to/excels --dry-run
```

Auto-Pilot detects:
- Primary and foreign keys automatically
- Value mappings (e.g., "1"/"0" to "Active"/"Inactive")
- Data quality issues with prioritized recommendations
- Optimal data types for each column

### Option 2: Manual Configuration

For complete control over the import process.

```bash
# 1. Initialize project
excel-to-sql init

# 2. Add mapping configuration
excel-to-sql config add --type products --table products --pk id

# 3. Import Excel file
excel-to-sql import --file products.xlsx --type products

# 4. Export data back to Excel
excel-to-sql export --table products --output report.xlsx

# 5. Profile data quality
excel-to-sql profile --table products --output quality-report.html
```

## CLI Reference

### Project Commands

#### Initialize Project

Creates a new excel-to-sql project with the required directory structure.

```bash
excel-to-sql init
```

Creates:
- `data/` - SQLite database location
- `config/` - Configuration files
- `imports/` - Imported Excel files
- `exports/` - Exported Excel files

#### Import Command

Import an Excel file into the database.

```bash
excel-to-sql import --file data.xlsx --type products
```

**Options:**
- `--file, -f` - Path to Excel file (required)
- `--type, -t` - Type configuration name (required)
- `--force` - Re-import even if content unchanged

#### Export Command

Export database data back to Excel.

```bash
excel-to-sql export --table products --output report.xlsx
```

**Options:**
- `--table` - Table name to export
- `--output, -o` - Output Excel file path

#### Profile Command

Generate data quality reports.

```bash
excel-to-sql profile --table products --output quality-report.html
```

### Configuration Commands

#### Add Type Configuration

Create a new mapping type interactively.

```bash
excel-to-sql config add --type customers --table customers --pk id
```

**Options:**
- `--add-type` - Name for the new type
- `--table` - Target table name
- `--pk` - Primary key column(s)
- `--file` - Excel file for auto-detection (optional)

#### List Types

Show all configured mapping types.

```bash
excel-to-sql config --list
```

#### Show Type Details

Display configuration for a specific type.

```bash
excel-to-sql config --show products
```

#### Remove Type

Delete a mapping type.

```bash
excel-to-sql config --remove old_type
```

### Magic Command (Auto-Pilot)

Automatic configuration and import with pattern detection.

```bash
# Automatic mode
excel-to-sql magic --data ./excels --output .excel-to-sql

# Interactive mode
excel-to-sql magic --data ./excels --interactive

# Dry run
excel-to-sql magic --data ./excels --dry-run
```

**Options:**
- `--data, -d` - Directory containing Excel files (default: current directory)
- `--output, -o` - Output directory for configuration (default: .excel-to-sql)
- `--dry-run` - Analyze without generating configuration
- `--interactive, -i` - Interactive guided setup

## Python SDK

The Python SDK provides programmatic access to all excel-to-sql features.

### Basic Usage

```python
from excel_to_sql import ExcelToSqlite

# Initialize SDK
sdk = ExcelToSqlite()

# Import Excel file with transformations
result = sdk.import_excel(
    file_path="data.xlsx",
    type_name="products",
    tags=["q1-2024", "verified"]
)

print(f"Imported {result['rows_imported']} rows")

# Query data
df = sdk.query("SELECT * FROM products WHERE price > 100")
print(df.head())

# Profile data quality
profile = sdk.profile_table("products")
print(f"Quality score: {profile['summary']['quality_score']}")
print(f"Issues found: {len(profile['issues'])}")

# Export to Excel with multi-sheet support
sdk.export_to_excel(
    output="report.xlsx",
    sheet_mapping={
        "Products": "products",
        "Categories": "SELECT * FROM categories"
    }
)
```

### Advanced Transformations

```python
from excel_to_sql import ExcelToSqlite
from excel_to_sql.transformations import ValueMapping, CalculatedColumn
from excel_to_sql.validators import ValidationRule

sdk = ExcelToSqlite()

# Configure value mappings
value_mappings = {
    "status": {"1": "Active", "0": "Inactive"},
    "state": {"NY": "New York", "CA": "California"}
}

# Configure calculated columns
calculated_columns = [
    CalculatedColumn("total", "quantity * price"),
    CalculatedColumn("tax", "total * 0.1"),
    CalculatedColumn("grand_total", "total + tax")
]

# Configure validation rules
validation_rules = [
    ValidationRule("id", "unique"),
    ValidationRule("email", "regex", pattern=r"^[^@]+@[^@]+\.[^@]+$"),
    ValidationRule("age", "range", min_value=0, max_value=120)
]
```

## Auto-Pilot Mode

Auto-Pilot mode provides zero-configuration import with intelligent pattern detection, quality scoring, and automated recommendations.

### What Auto-Pilot Detects

**Pattern Detection:**
- **Primary Keys** - Identifies unique columns automatically
- **Foreign Keys** - Detects relationships between tables
- **Value Mappings** - Finds code columns requiring translation
- **Split Fields** - Identifies redundant status columns to combine
- **Data Types** - Infers optimal SQL types from data

**Quality Analysis:**
- **Quality Score** (0-100) with letter grades (A-D)
- **Issue Detection** - Null values, duplicates, type mismatches
- **Statistical Analysis** - Value distributions, outliers
- **Data Profiling** - Column types, null percentages

**Smart Recommendations:**
- **Prioritized Suggestions** (HIGH/MEDIUM/LOW)
- **Auto-fixable Issues** with one-click corrections
- **Default Value Suggestions**
- **French Code Detection** (ENTRÉE→inbound, SORTIE→outbound, etc.)

### Auto-Pilot Components

The Auto-Pilot system consists of five main components:

**PatternDetector** - Analyzes Excel files and detects patterns with confidence scores

```python
from excel_to_sql.auto_pilot import PatternDetector

detector = PatternDetector()
patterns = detector.detect_patterns(df, "table_name")

# Returns: primary_key, foreign_keys, value_mappings, split_fields, confidence
```

**QualityScorer** - Generates comprehensive quality reports

```python
from excel_to_sql.auto_pilot import QualityScorer

scorer = QualityScorer()
report = scorer.generate_quality_report(df, "table_name")

# Returns: score (0-100), grade (A-D), issues, column_stats
```

**RecommendationEngine** - Provides prioritized, actionable recommendations

```python
from excel_to_sql.auto_pilot import RecommendationEngine

engine = RecommendationEngine()
recommendations = engine.generate_recommendations(
    df, "table_name", quality_report, patterns
)

# Returns prioritized recommendations (HIGH/MEDIUM/LOW)
```

**AutoFixer** - Automatically fixes data quality issues

```python
from excel_to_sql.auto_pilot import AutoFixer

fixer = AutoFixer()
result = fixer.apply_auto_fixes(
    df, file_path, "Sheet1", recommendations, dry_run=False
)

# Fixes: null values, French codes, split fields with backup system
```

**InteractiveWizard** - Guided configuration workflow

```python
from excel_to_sql.ui import InteractiveWizard

wizard = InteractiveWizard()
result = wizard.run_interactive_mode(
    excel_files, patterns_dict, quality_dict, output_path
)
```

### When to Use Auto-Pilot

**Perfect for:**
- Quick prototyping and testing
- Ad-hoc data imports
- Exploring new datasets
- Learning the tool
- Small to medium datasets

**Not ideal for:**
- Production deployments (use generated config as template)
- Complex custom transformations
- Highly specialized business logic
- Performance-critical operations

## Configuration

Mapping configuration is stored in `config/mappings.json`:

```json
{
  "products": {
    "target_table": "products",
    "primary_key": ["id"],
    "column_mappings": {
      "ID": {"target": "id", "type": "integer"},
      "Name": {"target": "name", "type": "string"},
      "Price": {"target": "price", "type": "float"}
    },
    "value_mappings": [
      {
        "column": "status",
        "mappings": {"1": "Active", "0": "Inactive"}
      }
    ],
    "calculated_columns": [
      {
        "name": "total",
        "expression": "quantity * price"
      }
    ],
    "validation_rules": [
      {
        "column": "id",
        "type": "unique"
      }
    ]
  }
}
```

### Column Types

Supported SQL types:
- `string` - TEXT columns (default)
- `integer` - INTEGER with Int64 (nullable)
- `float` - REAL columns
- `boolean` - BOOLEAN (0/1)
- `date` - TIMESTAMP (ISO-8601)

## Examples

### Example 1: E-commerce Product Import

```bash
# Initialize project
excel-to-sql init

# Use Auto-Pilot to analyze products
excel-to-sql magic --data ./products --interactive

# Review generated configuration
cat config/mappings.json

# Import with auto-generated configuration
excel-to-sql import --file products.xlsx --type products
```

### Example 2: Data Migration with Validation

```python
from excel_to_sql import ExcelToSqlite
from excel_to_sql.validators import ValidationRule

sdk = ExcelToSqlite()

# Add custom validation rules
rules = [
    ValidationRule("email", "regex", pattern=r"^[^@]+@[^@]+\.[^@]+$"),
    ValidationRule("age", "range", min_value=0, max_value=120),
    ValidationRule("id", "unique")
]

# Import with validation
result = sdk.import_excel(
    "customers.xlsx",
    "customers",
    validation_rules=rules
)

if result['validation_errors']:
    print(f"Found {len(result['validation_errors'])} validation errors")
```

### Example 3: Quality Analysis

```python
from excel_to_sql import ExcelToSqlite

sdk = ExcelToSqlite()

# Profile data quality
profile = sdk.profile_table("orders")

# Check quality score
score = profile['summary']['quality_score']
grade = profile['summary']['grade']
print(f"Quality Score: {score}/100 ({grade})")

# Review issues
for issue in profile['issues']:
    print(f"{issue['severity']}: {issue['column']} - {issue['message']}")

# Generate HTML report
sdk.generate_quality_report(
    "orders",
    output="quality-report.html"
)
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=excel_to_sql --cov-report=html

# Run specific test file
uv run pytest tests/test_auto_pilot.py -v
```

### Project Structure

```
excel-to-sqlite/
├── excel_to_sql/          # Main package
│   ├── cli.py            # CLI interface
│   ├── sdk/              # Python SDK
│   ├── entities/         # Domain entities
│   ├── transformations/  # Data transformations
│   ├── validators/       # Data validation
│   ├── profiling/        # Quality analysis
│   ├── auto_pilot/       # Auto-Pilot mode
│   └── ui/               # Interactive wizard
├── tests/                # Test suite
├── docs/                 # Documentation
└── config/               # Configuration files
```

### Test Coverage

- 200+ tests with comprehensive coverage
- >85% coverage on core modules
- Integration tests with real Excel fixtures
- Unit tests for all components

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

For documentation improvements, see `docs/issues/001-documentation-website.md`.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

### Version 0.3.0

**Auto-Pilot Mode - Zero-Configuration Import:**
- Pattern Detection - Automatic detection of PKs, FKs, value mappings, split fields
- Quality Scoring - Multi-dimensional data quality analysis with grades (A-D)
- Smart Recommendations - Prioritized, actionable suggestions (HIGH/MEDIUM/LOW)
- Auto-Fix Capabilities - One-click corrections for common data issues
- Interactive Wizard - Step-by-step guided configuration workflow
- French Code Support - Automatic translation (ENTRÉE→inbound, SORTIE→outbound, etc.)
- Split Field Detection - Intelligent COALESCE for redundant columns
- CLI Integration - `magic` command with --interactive flag

**Testing:**
- 143+ tests for Auto-Pilot components
- Integration tests with real Excel fixtures
- >85% coverage for core Auto-Pilot modules

**Total: 200+ tests** with comprehensive coverage across all features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- [Documentation](docs/)
- [Changelog](CHANGELOG.md)
- [Issue Tracker](https://github.com/wareflowx/excel-to-sql/issues)
- [PyPI Package](https://pypi.org/project/excel-to-sql/)
