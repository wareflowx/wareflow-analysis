# Wareflow Analysis CLI

CLI tool for warehouse data analysis automation.

## Installation

```bash
# Clone repository
git clone https://github.com/your-username/wareflow-analysis
cd wareflow-analysis

# Install with uv
uv sync
```

## Usage

### Create a new project

```bash
uv run wareflow init my-warehouse
```

This creates a complete project structure:
- `config.yaml` - Configuration for excel-to-sql
- `schema.sql` - Database schema
- `scripts/` - Analysis and export scripts
- `data/` - Place your Excel files here
- `output/` - Generated reports
- `warehouse.db` - SQLite database (empty)

### Use the project

```bash
cd my-warehouse

# Place your Excel files in data/
# - produits.xlsx
# - mouvements.xlsx
# - commandes.xlsx

# Import data
wareflow import

# Run analyses
wareflow analyze

# Generate reports
wareflow export
```

### Full pipeline

```bash
# Run everything at once
wareflow run
```

## Commands

- `wareflow init <name>` - Initialize new project
- `wareflow import` - Import Excel data to SQLite
- `wareflow analyze` - Run database analyses
- `wareflow export` - Generate Excel reports
- `wareflow run` - Run full pipeline (import -> analyze -> export)
- `wareflow status` - Show database status

## Development

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Format code
uv run ruff format .

# Lint code
uv run ruff check .
```

## Tech Stack

- **uv**: Modern Python package manager
- **Typer**: CLI framework
- **pandas**: Data manipulation
- **openpyxl**: Excel file handling
- **pytest**: Testing framework

## License

MIT License
