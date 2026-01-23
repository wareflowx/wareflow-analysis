"""Wareflow Analysis CLI."""

from pathlib import Path
import typer

from wareflow_analysis.init import initialize_project
from wareflow_analysis.data_import.importer import (
    get_import_status,
    init_import_config,
    run_import,
)
from wareflow_analysis.validation.validator import Validator
from wareflow_analysis.validation.reporters import ValidationReporter
from wareflow_analysis.analyze.abc import ABCAnalysis

app = typer.Typer(
    name="wareflow",
    help="Wareflow Analysis - Warehouse data analysis CLI",
    add_completion=False,
)


@app.command()
def init(
    project_name: str = typer.Argument(
        ...,
        help="Name of the project to create",
    ),
) -> None:
    """Initialize a new Wareflow analysis project."""
    success, message = initialize_project(project_name)

    if success:
        typer.echo(message)
        typer.echo("\nNext steps:")
        typer.echo(f"  cd {project_name}")
        typer.echo("  # Place your Excel files in data/ directory")
        typer.echo("  wareflow import-data --init")
    else:
        typer.echo(f"Error: {message}", err=True)
        raise typer.Exit(1)


@app.command()
def import_data(
    init_config: bool = typer.Option(
        False,
        "--init",
        "-i",
        help="Generate import configuration using Auto-Pilot",
    ),
    verbose: bool = typer.Option(
        True,
        "--quiet/--verbose",
        "-q/-v",
        help="Control output verbosity",
    ),
) -> None:
    """Import data from Excel files to SQLite using Auto-Pilot Mode.

    Examples:
        wareflow import-data --init        # Generate configuration first
        wareflow import-data               # Import using existing configuration
        wareflow import-data --quiet       # Import with minimal output
    """
    # Check we're in a wareflow project
    project_dir = Path.cwd()
    config_file = project_dir / "config.yaml"

    if not config_file.exists():
        typer.echo(
            "Error: Not in a wareflow project directory. "
            "Run 'wareflow init' first.",
            err=True,
        )
        raise typer.Exit(1)

    # Initialize configuration if requested
    if init_config:
        data_dir = project_dir / "data"
        success, message = init_import_config(data_dir, project_dir, verbose)

        if not success:
            typer.echo(f"Error: {message}", err=True)
            raise typer.Exit(1)

        typer.echo(message)
        return

    # Run import using existing configuration
    success, message = run_import(project_dir, verbose)

    if not success:
        typer.echo(f"Error: {message}", err=True)
        raise typer.Exit(1)

    typer.echo(message)


@app.command()
def analyze(
    name: str = typer.Option(
        "abc",
        "--name",
        "-n",
        help="Analysis to run (default: abc)",
    ),
    days: int = typer.Option(
        90,
        "--days",
        "-d",
        help="Lookback period in days (default: 90)",
    ),
) -> None:
    """Run warehouse analysis.

    Performs analytics on imported warehouse data to generate insights.
    Currently supported analyses:
      - abc: ABC classification (Pareto analysis)

    Examples:
        wareflow analyze                 # Run ABC analysis (default)
        wareflow analyze --name abc      # Explicit ABC analysis
        wareflow analyze --days 60       # 60-day lookback period
    """
    # Check we're in a wareflow project
    project_dir = Path.cwd()
    config_file = project_dir / "config.yaml"

    if not config_file.exists():
        typer.echo(
            "Error: Not in a wareflow project directory. "
            "Run 'wareflow init' first.",
            err=True,
        )
        raise typer.Exit(1)

    db_path = project_dir / "warehouse.db"

    if not db_path.exists():
        typer.echo(
            "Error: Database not found. Run 'wareflow import-data' first.",
            err=True,
        )
        raise typer.Exit(1)

    # Run the requested analysis
    if name == "abc":
        analyzer = ABCAnalysis(db_path)
        success, message = analyzer.connect()

        if not success:
            typer.echo(f"Error: {message}", err=True)
            raise typer.Exit(1)

        try:
            typer.echo(f"\nRunning ABC Classification analysis (last {days} days)...")
            results = analyzer.run(days)
            output = analyzer.format_output(results)
            typer.echo(output)
            analyzer.close()
        except Exception as e:
            analyzer.close()
            typer.echo(f"Error: Analysis failed - {e}", err=True)
            raise typer.Exit(1)
    else:
        typer.echo(
            f"Error: Unknown analysis '{name}'. Available: abc",
            err=True,
        )
        raise typer.Exit(1)


@app.command()
def export() -> None:
    """Generate Excel reports."""
    typer.echo("Export command not implemented yet")


@app.command()
def run() -> None:
    """Run full pipeline (import -> analyze -> export)."""
    typer.echo("Run command not implemented yet")


@app.command()
def status() -> None:
    """Show database status."""
    # Check we're in a wareflow project
    project_dir = Path.cwd()
    config_file = project_dir / "config.yaml"

    if not config_file.exists():
        typer.echo("Error: Not in a wareflow project directory.", err=True)
        raise typer.Exit(1)

    status_info = get_import_status(project_dir)

    typer.echo("\n" + "=" * 50)
    typer.echo("WAREFLOW PROJECT STATUS")
    typer.echo("=" * 50)

    if not status_info["database_exists"]:
        typer.echo("\nDatabase: Not created yet")
        typer.echo("\nRun 'wareflow import' to create the database.")
    else:
        typer.echo(f"\nDatabase: {status_info.get('database_path', 'warehouse.db')}")
        typer.echo("\nTables:")

        if status_info["tables"]:
            for table_name, row_count in status_info["tables"].items():
                typer.echo(f"  {table_name:20} {row_count:>10,} rows")
        else:
            typer.echo("  (no data imported yet)")
            if "error" in status_info:
                typer.echo(f"\nError reading database: {status_info['error']}")

    typer.echo("\n" + "=" * 50)


@app.command()
def validate(
    strict: bool = typer.Option(
        False,
        "--strict",
        "-s",
        help="Treat warnings as errors",
    ),
) -> None:
    """Validate Excel files before import.

    Performs comprehensive validation of Excel files in the data/ directory,
    checking for missing columns, duplicate primary keys, data type mismatches,
    null values, and more.

    Examples:
        wareflow validate                 # Validate all files
        wareflow validate --strict       # Fail on warnings too
    """
    # Check we're in a wareflow project
    project_dir = Path.cwd()
    config_file = project_dir / "config.yaml"

    if not config_file.exists():
        typer.echo(
            "Error: Not in a wareflow project directory. "
            "Run 'wareflow init' first.",
            err=True,
        )
        raise typer.Exit(1)

    # Run validation
    validator = Validator(project_dir)
    reporter = ValidationReporter(verbose=True)

    result = validator.validate_project(strict=strict)

    # Print results
    reporter.print_result(result)

    # Exit with error code if validation failed
    if not result.success:
        raise typer.Exit(1)


def cli() -> None:
    """Entry point for the CLI."""
    app()
