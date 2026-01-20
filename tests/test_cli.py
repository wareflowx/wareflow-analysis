"""Tests for CLI commands."""

from pathlib import Path
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


def test_init_creates_project(tmp_path: Path) -> None:
    """Test that init command creates a complete project structure."""
    project_name = "test-warehouse"
    # Change to temp directory for test
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["init", project_name])

        assert result.exit_code == 0
        assert "created successfully" in result.stdout or "successfully" in result.stdout

        # Check that project directory was created
        # In isolated_filesystem, the cwd is the temp_dir
        project_path = Path.cwd() / project_name
        assert project_path.exists()
        assert project_path.is_dir()

        # Check directory structure
        assert (project_path / "data").exists()
        assert (project_path / "output").exists()
        assert (project_path / "scripts").exists()

        # Check template files
        assert (project_path / "config.yaml").exists()
        assert (project_path / "schema.sql").exists()
        assert (project_path / "README.md").exists()
        assert (project_path / "scripts" / "import.py").exists()
        assert (project_path / "scripts" / "analyze.py").exists()
        assert (project_path / "scripts" / "export.py").exists()

        # Check database was created
        assert (project_path / "warehouse.db").exists()


def test_init_fails_on_existing_directory(tmp_path: Path) -> None:
    """Test that init fails if directory already exists."""
    project_name = "existing-project"
    # Create the project directory before testing
    with runner.isolated_filesystem(temp_dir=tmp_path):
        existing_path = Path.cwd() / project_name
        existing_path.mkdir()

        result = runner.invoke(app, ["init", project_name])

        assert result.exit_code == 1


def test_init_fails_on_invalid_name() -> None:
    """Test that init fails with invalid project name."""
    result = runner.invoke(app, ["init", ""])
    assert result.exit_code == 1

    result = runner.invoke(app, ["init", "invalid name!"])
    assert result.exit_code == 1

    result = runner.invoke(app, ["init", "_invalid"])
    assert result.exit_code == 1

