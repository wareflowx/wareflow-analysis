"""Wareflow Analysis CLI."""

import typer

from wareflow_analysis.init import initialize_project

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
        typer.echo("  wareflow import")
    else:
        typer.echo(f"Error: {message}", err=True)
        raise typer.Exit(1)


@app.command()
def import_data() -> None:
    """Import data from Excel files to SQLite."""
    typer.echo("Import command not implemented yet")


@app.command()
def analyze() -> None:
    """Run all analyses."""
    typer.echo("Analyze command not implemented yet")


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
    typer.echo("Status command not implemented yet")


def cli() -> None:
    """Entry point for the CLI."""
    app()
