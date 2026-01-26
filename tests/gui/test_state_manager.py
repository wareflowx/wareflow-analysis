"""Tests for StateManager."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import yaml

from wareflow_analysis.gui.controllers.state_manager import (
    StateManager,
    get_state_manager,
    reset_state_manager,
)


class TestStateManager:
    """Test suite for StateManager class."""

    def test_init(self):
        """Test StateManager initialization."""
        manager = StateManager()

        assert manager.project_dir is None
        assert manager.db_path is None
        assert manager.config_path is None
        assert manager.database_exists is False
        assert manager.config_exists is False
        assert manager.last_operation is None
        assert manager.last_operation_time is None

    def test_default_settings(self):
        """Test default settings."""
        manager = StateManager()

        assert manager.settings["remember_last_project"] is True
        assert manager.settings["auto_create_backup"] is True
        assert manager.settings["verbose_output"] is True
        assert manager.settings["theme"] == "System"
        assert manager.settings["confirm_destructive"] is True

    def test_set_project_dir_valid(self):
        """Test setting a valid project directory."""
        manager = StateManager()

        with TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            config_file = project_dir / "config.yaml"

            # Create a valid config file
            with open(config_file, "w") as f:
                yaml.dump({"database": {"path": "warehouse.db"}}, f)

            success = manager.set_project_dir(project_dir)

            assert success is True
            assert manager.project_dir == project_dir
            assert manager.config_path == config_file
            assert manager.config_exists is True
            assert manager.db_path == project_dir / "warehouse.db"

    def test_set_project_dir_invalid(self):
        """Test setting an invalid project directory."""
        manager = StateManager()

        with TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            # No config.yaml created

            success = manager.set_project_dir(project_dir)

            assert success is False
            assert manager.project_dir is None

    def test_is_project_loaded(self):
        """Test is_project_loaded method."""
        manager = StateManager()

        assert manager.is_project_loaded() is False

        with TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            config_file = project_dir / "config.yaml"

            with open(config_file, "w") as f:
                yaml.dump({"database": {"path": "warehouse.db"}}, f)

            manager.set_project_dir(project_dir)
            assert manager.is_project_loaded() is True

    def test_is_database_ready(self):
        """Test is_database_ready method."""
        manager = StateManager()

        assert manager.is_database_ready() is False

        with TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            config_file = project_dir / "config.yaml"
            db_file = project_dir / "warehouse.db"

            with open(config_file, "w") as f:
                yaml.dump({"database": {"path": "warehouse.db"}}, f)

            manager.set_project_dir(project_dir)

            # Database doesn't exist yet
            assert manager.is_database_ready() is False

            # Create database file
            db_file.touch()

            manager.update_database_state()
            assert manager.is_database_ready() is True

    def test_get_project_dir(self):
        """Test get_project_dir method."""
        manager = StateManager()

        assert manager.get_project_dir() is None

        with TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            config_file = project_dir / "config.yaml"

            with open(config_file, "w") as f:
                yaml.dump({"database": {"path": "warehouse.db"}}, f)

            manager.set_project_dir(project_dir)
            assert manager.get_project_dir() == project_dir

    def test_get_setting(self):
        """Test getting settings."""
        manager = StateManager()

        assert manager.get_setting("verbose_output") is True
        assert manager.get_setting("nonexistent", "default") == "default"
        assert manager.get_setting("nonexistent") is None

    def test_set_setting(self):
        """Test setting settings."""
        manager = StateManager()

        manager.set_setting("verbose_output", False)
        assert manager.get_setting("verbose_output") is False

        manager.set_setting("new_setting", "value")
        assert manager.get_setting("new_setting") == "value"

    def test_set_last_operation(self):
        """Test setting last operation."""
        from datetime import datetime

        manager = StateManager()

        manager.set_last_operation("Test operation")

        assert manager.last_operation == "Test operation"
        assert manager.last_operation_time is not None
        assert isinstance(manager.last_operation_time, datetime)

    def test_update_database_state(self):
        """Test updating database state."""
        manager = StateManager()

        with TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            config_file = project_dir / "config.yaml"
            db_file = project_dir / "warehouse.db"

            with open(config_file, "w") as f:
                yaml.dump({"database": {"path": "warehouse.db"}}, f)

            manager.set_project_dir(project_dir)

            # Database doesn't exist
            manager.update_database_state()
            assert manager.database_exists is False

            # Create database
            db_file.touch()
            manager.update_database_state()
            assert manager.database_exists is True

    def test_register_listener(self):
        """Test registering state change listeners."""
        manager = StateManager()

        events = []
        listener = lambda event: events.append(event)

        manager.register_listener(listener)

        manager.set_setting("test", "value")

        assert len(events) == 1
        assert events[0] == "settings_changed"

    def test_unregister_listener(self):
        """Test unregistering state change listeners."""
        manager = StateManager()

        events = []
        listener = lambda event: events.append(event)

        manager.register_listener(listener)
        manager.unregister_listener(listener)

        manager.set_setting("test", "value")

        assert len(events) == 0

    def test_reset(self):
        """Test resetting state manager."""
        manager = StateManager()

        with TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            config_file = project_dir / "config.yaml"

            with open(config_file, "w") as f:
                yaml.dump({"database": {"path": "warehouse.db"}}, f)

            manager.set_project_dir(project_dir)
            manager.set_last_operation("Test")

            manager.reset()

            assert manager.project_dir is None
            assert manager.database_exists is False
            assert manager.config_exists is False
            assert manager.last_operation is None

    def test_global_state_manager(self):
        """Test global state manager singleton."""
        reset_state_manager()

        manager1 = get_state_manager()
        manager2 = get_state_manager()

        assert manager1 is manager2

    def test_reset_global_state_manager(self):
        """Test resetting global state manager."""
        manager1 = get_state_manager()

        reset_state_manager()

        manager2 = get_state_manager()

        assert manager1 is not manager2
