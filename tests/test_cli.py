"""Tests for CLI commands."""

from typer.testing import CliRunner

from wareflow_analysis.cli import app

runner = CliRunner()


def test_cli_help() -> None:
    """Test that --help works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Wareflow Analysis" in result.stdout


def test_init_command_exists() -> None:
    """Test that init command exists."""
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "Initialize a new Wareflow analysis project" in result.stdout


def test_import_data_command_exists() -> None:
    """Test that import-data command exists."""
    result = runner.invoke(app, ["import-data", "--help"])
    assert result.exit_code == 0
    assert "Import data from Excel files" in result.stdout


def test_analyze_command_exists() -> None:
    """Test that analyze command exists."""
    result = runner.invoke(app, ["analyze", "--help"])
    assert result.exit_code == 0
    assert "Run all analyses" in result.stdout


def test_export_command_exists() -> None:
    """Test that export command exists."""
    result = runner.invoke(app, ["export", "--help"])
    assert result.exit_code == 0
    assert "Generate Excel reports" in result.stdout


def test_run_command_exists() -> None:
    """Test that run command exists."""
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    assert "Run full pipeline" in result.stdout


def test_status_command_exists() -> None:
    """Test that status command exists."""
    result = runner.invoke(app, ["status", "--help"])
    assert result.exit_code == 0
    assert "Show database status" in result.stdout


def test_init_not_implemented() -> None:
    """Test that init command shows not implemented message."""
    result = runner.invoke(app, ["init", "test-project"])
    assert result.exit_code == 0
    assert "Not implemented yet" in result.stdout
