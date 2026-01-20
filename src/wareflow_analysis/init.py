"""Project initialization logic."""

import sqlite3
from pathlib import Path

from wareflow_analysis import templates_dir


def validate_project_name(project_name: str) -> tuple[bool, str]:
    """Validate project name.

    Args:
        project_name: Name to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not project_name:
        return False, "Project name cannot be empty"

    if not project_name.replace("-", "").replace("_", "").isalnum():
        return False, "Project name must contain only alphanumeric characters, hyphens, and underscores"

    if project_name.startswith(("_", "-")):
        return False, "Project name cannot start with hyphen or underscore"

    return True, ""


def create_project_structure(project_path: Path) -> None:
    """Create project directory structure.

    Args:
        project_path: Path to project directory
    """
    # Create directories
    (project_path / "data").mkdir(parents=True, exist_ok=True)
    (project_path / "output").mkdir(parents=True, exist_ok=True)
    (project_path / "scripts").mkdir(parents=True, exist_ok=True)


def copy_templates(project_path: Path) -> None:
    """Copy template files to project.

    Args:
        project_path: Path to project directory
    """
    # Copy config.yaml
    config_src = templates_dir / "config.yaml"
    config_dst = project_path / "config.yaml"
    config_dst.write_text(config_src.read_text())

    # Copy schema.sql
    schema_src = templates_dir / "schema.sql"
    schema_dst = project_path / "schema.sql"
    schema_dst.write_text(schema_src.read_text())

    # Copy README.md
    readme_src = templates_dir / "README.md"
    readme_dst = project_path / "README.md"
    readme_dst.write_text(readme_src.read_text())

    # Copy scripts
    for script_name in ["import.py", "analyze.py", "export.py"]:
        script_src = templates_dir / script_name
        script_dst = project_path / "scripts" / script_name
        script_dst.write_text(script_src.read_text())


def create_database(project_path: Path) -> None:
    """Create empty SQLite database with schema.

    Args:
        project_path: Path to project directory
    """
    schema_path = templates_dir / "schema.sql"
    schema_sql = schema_path.read_text()

    db_path = project_path / "warehouse.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()


def create_gitkeep_files(project_path: Path) -> None:
    """Create .gitkeep files in empty directories.

    Args:
        project_path: Path to project directory
    """
    (project_path / "data" / ".gitkeep").touch()
    (project_path / "output" / ".gitkeep").touch()


def initialize_project(project_name: str, base_dir: Path | None = None) -> tuple[bool, str]:
    """Initialize a new Wareflow project.

    Args:
        project_name: Name of the project to create
        base_dir: Base directory for project creation (defaults to cwd)

    Returns:
        Tuple of (success, message)
    """
    # Validate project name
    is_valid, error_msg = validate_project_name(project_name)
    if not is_valid:
        return False, error_msg

    # Check if directory already exists
    base = base_dir if base_dir is not None else Path.cwd()
    project_path = base / project_name
    if project_path.exists():
        return False, f"Directory '{project_name}' already exists"

    try:
        # Create project structure
        create_project_structure(project_path)

        # Copy template files
        copy_templates(project_path)

        # Create database
        create_database(project_path)

        # Create .gitkeep files
        create_gitkeep_files(project_path)

        return True, f"✓ Project '{project_name}' created successfully!"
    except PermissionError:
        return False, "Permission denied: Cannot create project directory"
    except Exception as e:
        return False, f"Error creating project: {e}"
