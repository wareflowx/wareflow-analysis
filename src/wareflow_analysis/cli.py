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
from wareflow_analysis.analyze.inventory import InventoryAnalysis
from wareflow_analysis.export.reports.inventory_report import InventoryReportExporter
from wareflow_analysis.export.reports.abc_report import ABCReportExporter
from wareflow_analysis.database.manager import DatabaseManager

app = typer.Typer(
    name="wareflow",
    help="Wareflow Analysis - Warehouse data analysis CLI",
    add_completion=False,
)


@app.command()
def init(
    project_name: str = typer.Argument(
        None,
        show_default="current directory",
        help="Name of the project to create (optional, initializes in current directory if not provided)",
    ),
) -> None:
    """Initialize a new Wareflow analysis project.

    If PROJECT_NAME is omitted, initializes the project in the current directory.
    Use 'wareflow init .' to explicitly initialize in current directory.
    """
    success, message = initialize_project(project_name)

    if success:
        typer.echo(message)
        typer.echo("\nNext steps:")
        if project_name and project_name != ".":
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
      - inventory: Product catalog statistics

    Examples:
        wareflow analyze                    # Run ABC analysis (default)
        wareflow analyze --name abc         # Explicit ABC analysis
        wareflow analyze --name inventory   # Inventory analysis
        wareflow analyze --days 60          # 60-day lookback period
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
    elif name == "inventory":
        analyzer = InventoryAnalysis(db_path)
        success, message = analyzer.connect()

        if not success:
            typer.echo(f"Error: {message}", err=True)
            raise typer.Exit(1)

        try:
            typer.echo("\nRunning Inventory Analysis...")
            results = analyzer.run()
            output = analyzer.format_output(results)
            typer.echo(output)
            analyzer.close()
        except Exception as e:
            analyzer.close()
            typer.echo(f"Error: Analysis failed - {e}", err=True)
            raise typer.Exit(1)
    else:
        typer.echo(
            f"Error: Unknown analysis '{name}'. Available: abc, inventory",
            err=True,
        )
        raise typer.Exit(1)


@app.command()
def export(
    analysis: str = typer.Option(
        "inventory",
        "--analysis",
        "-a",
        help="Analysis to export (inventory or abc)",
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output filename (default: auto-generated with timestamp)",
    ),
    dir: str = typer.Option(
        "output",
        "--dir",
        "-d",
        help="Output directory",
    ),
) -> None:
    """Generate Excel reports from analysis results.

    Exports analysis results to formatted Excel files with multiple sheets.

    Examples:
        wareflow export                          # Export inventory with auto filename
        wareflow export --analysis abc           # Export ABC classification
        wareflow export --output report.xlsx     # Custom filename
        wareflow export --dir reports/           # Custom directory
    """
    from datetime import datetime

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

    # Run the requested analysis and export
    if analysis == "inventory":
        typer.echo("\nRunning Inventory Analysis...")

        # Run analysis
        analyzer = InventoryAnalysis(db_path)
        success, message = analyzer.connect()

        if not success:
            typer.echo(f"Error: {message}", err=True)
            raise typer.Exit(1)

        try:
            results = analyzer.run()
            analyzer.close()
        except Exception as e:
            analyzer.close()
            typer.echo(f"Error: Analysis failed - {e}", err=True)
            raise typer.Exit(1)

        # Generate output filename if not provided
        if output is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"inventory_report_{timestamp}.xlsx"

        # Create output directory if it doesn't exist
        output_dir = project_dir / dir
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / output

        # Export to Excel
        typer.echo(f"Exporting to {output_path}...")
        try:
            exporter = InventoryReportExporter()
            exporter.export(results, output_path)
            typer.echo(f"\n[OK] Report exported successfully: {output_path}")
        except Exception as e:
            typer.echo(f"Error: Export failed - {e}", err=True)
            raise typer.Exit(1)
    elif analysis == "abc":
        typer.echo("\nRunning ABC Classification Analysis...")

        # Run analysis
        analyzer = ABCAnalysis(db_path)
        success, message = analyzer.connect()

        if not success:
            typer.echo(f"Error: {message}", err=True)
            raise typer.Exit(1)

        try:
            results = analyzer.run(days=90)
            analyzer.close()
        except Exception as e:
            analyzer.close()
            typer.echo(f"Error: Analysis failed - {e}", err=True)
            raise typer.Exit(1)

        # Generate output filename if not provided
        if output is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"abc_report_{timestamp}.xlsx"

        # Create output directory if it doesn't exist
        output_dir = project_dir / dir
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / output

        # Export to Excel
        typer.echo(f"Exporting to {output_path}...")
        try:
            exporter = ABCReportExporter()
            exporter.export(results, output_path)
            typer.echo(f"\n[OK] Report exported successfully: {output_path}")
        except Exception as e:
            typer.echo(f"Error: Export failed - {e}", err=True)
            raise typer.Exit(1)
    else:
        typer.echo(
            f"Error: Unknown analysis '{analysis}'. Available: inventory, abc",
            err=True,
        )
        raise typer.Exit(1)


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


@app.command()
def clean(
    db: bool = typer.Option(
        False,
        "--db",
        help="Clean all tables (keep schema)",
    ),
    table: str = typer.Option(
        None,
        "--table",
        "-t",
        help="Clean specific table only",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be deleted without doing it",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt",
    ),
    backup: bool = typer.Option(
        True,
        "--backup/--no-backup",
        help="Create backup before cleaning",
    ),
) -> None:
    """Clean database data safely.

    Removes data from tables while preserving schema. Creates automatic backups
    unless --no-backup is specified.

    Examples:
        wareflow clean --db               # Clean all tables (with confirmation)
        wareflow clean --table mouvements  # Clean specific table
        wareflow clean --db --dry-run      # Preview what would be deleted
        wareflow clean --db --force        # Skip confirmation
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
    manager = DatabaseManager(db_path, project_dir)

    # Check database exists
    if not manager.database_exists():
        typer.echo(
            f"\n❌ Database not found\n\n"
            f"  File: {db_path} does not exist\n\n"
            f"💡 Solution:\n"
            f"  Run 'wareflow import-data' to create the database\n"
            f"  Or run 'wareflow init' to create a new project",
            err=True,
        )
        raise typer.Exit(1)

    # Validate options
    if not db and not table:
        typer.echo(
            "Error: Must specify either --db or --table <TABLE_NAME>",
            err=True,
        )
        raise typer.Exit(1)

    if db and table:
        typer.echo(
            "Error: Cannot specify both --db and --table",
            err=True,
        )
        raise typer.Exit(1)

    # Handle table-specific cleaning
    if table:
        # Check table exists
        available_tables = manager.get_available_tables()
        if table not in available_tables:
            typer.echo(
                f"\n❌ Table not found\n\n"
                f"  Table: '{table}' does not exist\n\n"
                f"Available tables:\n"
                f"  {', '.join(available_tables)}\n\n"
                f"💡 Use --table with a valid table name",
                err=True,
            )
            raise typer.Exit(1)

        # Get table info
        table_info = manager.get_table_info()
        target_table = next((t for t in table_info if t["name"] == table), None)
        row_count = target_table["rows"]

        if dry_run:
            typer.echo("\n🔍 Dry-run mode: No changes will be made\n")
            typer.echo(f"\nDatabase: {db_path}")
            typer.echo(f"\nWould clean:")
            typer.echo(f"  {table}: {row_count:,} rows")

            if backup:
                from datetime import datetime
                backup_name = f"{db_path.stem}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{db_path.suffix}"
                typer.echo(f"\nWould create backup: {backup_name}")

            typer.echo("\n💡 Remove --dry-run to proceed")
            return

        # Create backup if requested
        if backup:
            backup_path = manager.backup_database()
            typer.echo(f"✓ Creating backup: {backup_path.name}")

        # Confirm action
        confirmed = manager.confirm_action(
            f"⚠️  This will delete all data from '{table}' table\n\n"
            f"Table: {table} ({row_count:,} rows)",
            force=force
        )

        if not confirmed:
            typer.echo("Cancelled")
            raise typer.Exit(0)

        # Clean table
        deleted = manager.clean_table(table)
        typer.echo(f"✓ Cleaning table: {table} ({deleted:,} rows deleted)")

        # Show preserved tables
        other_tables = [t for t in available_tables if t != table]
        if other_tables:
            table_info = manager.get_table_info()
            preserved = [f"{t['name']} ({t['rows']:,} rows)" for t in table_info if t["name"] in other_tables]
            typer.echo(f"\n✓ Other tables preserved: {', '.join(preserved)}")

        typer.echo("\n✅ Table cleaned successfully")

    # Handle full database cleaning
    if db:
        table_info = manager.get_table_info()
        total_rows = sum(t["rows"] for t in table_info)

        if dry_run:
            typer.echo("\n🔍 Dry-run mode: No changes will be made\n")
            typer.echo(f"\nDatabase: {db_path} ({manager.format_size(manager.get_database_size())})")
            typer.echo("\nWould clean:")
            for table in table_info:
                typer.echo(f"  {table['name']}: {table['rows']:,} rows")
            typer.echo(f"\nTotal: {total_rows:,} rows")

            if backup:
                from datetime import datetime
                backup_name = f"{db_path.stem}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{db_path.suffix}"
                typer.echo(f"\nWould create backup: {backup_name}")

            typer.echo(f"\nResulting database size: ~192 KB")

            typer.echo("\n💡 Remove --dry-run to proceed")
            return

        # Create backup if requested
        if backup:
            backup_path = manager.backup_database()
            typer.echo(f"✓ Creating backup: {backup_path.name}")

        # Confirm action
        table_list = "\n".join([f"  {t['name']}: {t['rows']:,} rows" for t in table_info])
        confirmed = manager.confirm_action(
            f"⚠️  WARNING: This will delete all data from the database\n\n"
            f"Database: {db_path} ({manager.format_size(manager.get_database_size())})\n\n"
            f"Tables to clean:\n"
            f"{table_list}\n\n"
            f"Total: {total_rows:,} rows",
            force=force
        )

        if not confirmed:
            typer.echo("Cancelled")
            raise typer.Exit(0)

        # Clean all tables
        deleted_rows = manager.clean_all_tables()

        for table_name, count in deleted_rows.items():
            typer.echo(f"✓ Cleaning table: {table_name} ({count:,} rows deleted)")

        typer.echo("✓ Vacuuming database...")
        typer.echo(f"\n✅ Database cleaned successfully")
        typer.echo(f"   Schema preserved, all data removed")
        typer.echo(f"   Database size: {manager.format_size(manager.get_database_size())} (empty)")

        typer.echo("\n💡 Next step:")
        typer.echo("   Run 'wareflow import-data' to import fresh data")


@app.command()
def reset(
    hard: bool = typer.Option(
        False,
        "--hard",
        help="Delete entire project directory (DANGEROUS)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be deleted without doing it",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompts",
    ),
) -> None:
    """Reset project to clean state.

    Performs a soft reset by default (clean database). Use --hard for complete
    project deletion (DANGEROUS - requires special confirmation).

    Examples:
        wareflow reset                   # Soft reset (clean database only)
        wareflow reset --hard            # Delete entire project
        wareflow reset --dry-run          # Preview what would be deleted
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

    # Handle soft reset (default)
    if not hard:
        manager = DatabaseManager(db_path, project_dir)

        if not manager.database_exists():
            typer.echo(
                "\n✅ Project is already clean (no database found)"
            )
            return

        if dry_run:
            table_info = manager.get_table_info()
            total_rows = sum(t["rows"] for t in table_info)

            typer.echo("\n🔍 Dry-run mode: No changes will be made\n")
            typer.echo(f"\nWould delete: {db_path}")
            typer.echo(f"Database size: {manager.format_size(manager.get_database_size())}")
            typer.echo(f"Total rows: {total_rows:,}")

            typer.echo("\n💡 Remove --dry-run to proceed")
            return

        # Confirm soft reset
        confirmed = manager.confirm_action(
            f"⚠️  This will delete all data from the database\n\n"
            f"Project: {project_dir}",
            force=force
        )

        if not confirmed:
            typer.echo("Cancelled")
            raise typer.Exit(0)

        # Create backup
        backup_path = manager.backup_database()
        typer.echo(f"✓ Creating backup: {backup_path.name}")

        # Clean database
        deleted_rows = manager.clean_all_tables()
        total_rows = sum(deleted_rows.values())

        typer.echo(f"✓ Deleted {total_rows:,} rows from {len(deleted_rows)} table(s)")
        typer.echo("✓ Vacuuming database...")

        typer.echo("\n✅ Project reset successfully")
        typer.echo(f"   Database: {db_path.name} cleaned")
        typer.echo(f"   Config: {config_file.name} preserved")
        typer.echo(f"   Data directory: data/ preserved")

        typer.echo("\n💡 Next step:")
        typer.echo("   Run 'wareflow import-data' to import fresh data")

        return

    # Handle hard reset (DANGEROUS)
    if hard:
        if dry_run:
            typer.echo("\n🔍 Dry-run mode: No changes will be made\n")
            typer.echo(f"\nWould delete entire project directory:")
            typer.echo(f"  {project_dir}")

            # Count files
            all_files = list(project_dir.rglob("*"))
            typer.echo(f"\nFiles: {len(all_files):,} items")

            typer.echo("\n⚠️  DANGEROUS: This cannot be undone!")
            typer.echo("\n💡 Remove --dry-run to proceed")
            return

        typer.echo("\n⚠️  DANGEROUS: Hard reset will delete the entire project directory")
        typer.echo(f"\nProject: {project_dir}")
        typer.echo("\nThis will delete:")
        typer.echo("  - Database files")
        typer.echo("  - Configuration files")
        typer.echo("  - Data files (Excel imports)")
        typer.echo("  - Output files")
        typer.echo("  - All project data")

        if not force:
            # Require special confirmation for hard reset
            response = input("\nType 'DELETE_EVERYTHING' to confirm: ")
            if response != "DELETE_EVERYTHING":
                typer.echo("Cancelled")
                raise typer.Exit(0)
        else:
            # With --force, still require confirmation but less strict
            confirmed = manager.confirm_action(
                "⚠️  This will delete the entire project directory",
                force=False  # Always require confirmation for hard reset
            )
            if not confirmed:
                typer.echo("Cancelled")
                raise typer.Exit(0)

        # Perform hard reset
        import shutil
        try:
            shutil.rmtree(project_dir)
            typer.echo(f"\n✅ Project directory deleted: {project_dir}")
            typer.echo("\n💡 Run 'wareflow init' to create a new project")
        except Exception as e:
            typer.echo(f"\n❌ Error: Failed to delete project directory: {e}", err=True)
            raise typer.Exit(1)


def cli() -> None:
    """Entry point for the CLI."""
    app()
