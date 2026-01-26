# Wareflow Analysis

Warehouse data analysis tool for ABC classification, inventory analysis, and reporting.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Features

- **CLI Interface**: Command-line tool for automation and scripting
- **GUI Application**: User-friendly graphical interface for non-technical users
- **ABC Analysis**: Classify products by importance (A/B/C categories)
- **Inventory Analysis**: Analyze warehouse stock and movements
- **Excel Export**: Generate professional Excel reports with formatting
- **SQLite Storage**: Local database for fast queries and data persistence

## Installation

### Option 1: Using pip (Recommended for developers)

```bash
pip install wareflow-analysis
```

### Option 2: Using the standalone Windows executable (Recommended for users)

Download the latest `Warehouse-GUI.exe` from the [Releases](https://github.com/wareflowx/wareflow-analysis/releases) page. No Python installation required.

## Quick Start

### Using the GUI (Recommended for non-technical users)

If installed via pip:
```bash
wareflow-gui
```

Or run the executable directly:
```bash
./Warehouse-GUI.exe
```

The GUI provides an intuitive interface for:
- Creating and managing projects
- Importing Excel data
- Running analyses
- Exporting reports

### Using the CLI (Recommended for automation)

1. Initialize a new project:
   ```bash
   mkdir my-warehouse
   cd my-warehouse
   wareflow init
   ```

2. Place your Excel files in the `data/` directory:
   - produits.xlsx (Products catalog)
   - mouvements.xlsx (Stock movements)
   - commandes.xlsx (Orders)

3. Import data:
   ```bash
   wareflow import
   ```

4. Run analyses:
   ```bash
   wareflow analyze abc
   wareflow analyze inventory
   ```

5. Generate reports:
   ```bash
   wareflow export abc --output output/abc_report.xlsx
   wareflow export inventory --output output/inventory_report.xlsx
   ```

## CLI Commands

| Command | Description |
|---------|-------------|
| `wareflow init` | Initialize a new project |
| `wareflow import` | Import Excel data to SQLite |
| `wareflow analyze abc` | Run ABC classification analysis |
| `wareflow analyze inventory` | Run inventory analysis |
| `wareflow export abc` | Export ABC analysis to Excel |
| `wareflow export inventory` | Export inventory analysis to Excel |
| `wareflow status` | Show database and project status |
| `wareflow run` | Run the complete pipeline |

## Project Structure

After initialization, your project will have:

```
my-warehouse/
├── config.yaml          # Excel-to-SQL configuration
├── data/                # Place your Excel files here
│   ├── produits.xlsx
│   ├── mouvements.xlsx
│   └── commandes.xlsx
├── output/              # Generated reports will be saved here
├── warehouse.db         # SQLite database
└── scripts/             # Custom analysis scripts
```

## Development

### Building from Source

See [BUILD.md](BUILD.md) for detailed build instructions.

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Building the Windows Executable

See [BUILD.md](BUILD.md) for instructions on building the standalone executable.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

- **Issues**: [GitHub Issues](https://github.com/wareflowx/wareflow-analysis/issues)
- **Documentation**: [Project Docs](https://github.com/wareflowx/wareflow-analysis)

## Acknowledgments

Built with:
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern GUI framework
- [Pandas](https://pandas.pydata.org/) - Data analysis
- [OpenPyXL](https://openpyxl.readthedocs.io/) - Excel handling
- [PyYAML](https://pyyaml.org/) - Configuration management
