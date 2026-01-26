"""State manager for GUI application.

This module provides centralized state management for the GUI application,
tracking project status, database state, and application settings.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class StateManager:
    """Manage application state for GUI.

    This class tracks:
    - Current project directory
    - Database status
    - Configuration state
    - Recent operations
    - Application settings

    Attributes:
        project_dir: Current project directory path
        db_path: Path to database file
        config_path: Path to config file
        database_exists: Whether database file exists
        config_exists: Whether config file exists
        last_operation: Last operation performed
        settings: Application settings dictionary
    """

    def __init__(self):
        """Initialize the StateManager."""
        self.project_dir: Optional[Path] = None
        self.db_path: Optional[Path] = None
        self.config_path: Optional[Path] = None
        self.database_exists: bool = False
        self.config_exists: bool = False
        self.last_operation: Optional[str] = None
        self.last_operation_time: Optional[datetime] = None

        # Application settings
        self.settings: Dict[str, Any] = {
            "remember_last_project": True,
            "auto_create_backup": True,
            "verbose_output": True,
            "theme": "System",  # System, Light, Dark
            "confirm_destructive": True,
        }

        # Database statistics (cached)
        self.db_stats: Dict[str, Any] = {}

        # Listeners for state changes
        self._listeners: list = []

    def set_project_dir(self, project_dir: Path) -> bool:
        """Set the current project directory.

        Args:
            project_dir: Path to project directory

        Returns:
            True if project directory is valid, False otherwise
        """
        project_dir = Path(project_dir)

        # Check if it's a valid wareflow project
        config_file = project_dir / "config.yaml"
        if not config_file.exists():
            return False

        self.project_dir = project_dir
        self.config_path = config_file
        self.db_path = project_dir / "warehouse.db"
        self.config_exists = True
        self.database_exists = self.db_path.exists()

        # Clear cached stats
        self.db_stats = {}

        # Notify listeners
        self._notify_listeners("project_changed")

        return True

    def get_project_dir(self) -> Optional[Path]:
        """Get the current project directory.

        Returns:
            Current project directory path or None
        """
        return self.project_dir

    def is_project_loaded(self) -> bool:
        """Check if a project is currently loaded.

        Returns:
            True if a project is loaded, False otherwise
        """
        return self.project_dir is not None and self.config_exists

    def is_database_ready(self) -> bool:
        """Check if database is ready for operations.

        Returns:
            True if database exists and has data, False otherwise
        """
        return self.database_exists and self.is_project_loaded()

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics.

        Returns:
            Dictionary with database statistics
        """
        if not self.is_database_ready():
            return {}

        # Return cached stats if available
        if self.db_stats:
            return self.db_stats

        # Import here to avoid circular dependencies
        from wareflow_analysis.data_import.importer import get_import_status

        stats = get_import_status(self.project_dir)
        self.db_stats = stats

        return self.db_stats

    def refresh_database_stats(self) -> Dict[str, Any]:
        """Force refresh of database statistics.

        Returns:
            Dictionary with fresh database statistics
        """
        self.db_stats = {}
        return self.get_database_stats()

    def update_database_state(self) -> None:
        """Update database state (exists/doesn't exist)."""
        if self.project_dir:
            self.database_exists = self.db_path.exists() if self.db_path else False
            self.db_stats = {}
            self._notify_listeners("database_changed")

    def set_last_operation(self, operation: str) -> None:
        """Set the last performed operation.

        Args:
            operation: Description of the operation
        """
        self.last_operation = operation
        self.last_operation_time = datetime.now()
        self._notify_listeners("operation_completed")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value.

        Args:
            key: Setting key
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value.

        Args:
            key: Setting key
            value: Setting value
        """
        self.settings[key] = value
        self._notify_listeners("settings_changed")

    def register_listener(self, callback) -> None:
        """Register a listener for state changes.

        Args:
            callback: Function to call when state changes
        """
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unregister_listener(self, callback) -> None:
        """Unregister a state change listener.

        Args:
            callback: Function to remove from listeners
        """
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self, event: str) -> None:
        """Notify all listeners of a state change.

        Args:
            event: Event type that occurred
        """
        for listener in self._listeners:
            try:
                listener(event)
            except Exception:
                # Don't let listener errors break the app
                pass

    def reset(self) -> None:
        """Reset all state to initial values."""
        self.project_dir = None
        self.db_path = None
        self.config_path = None
        self.database_exists = False
        self.config_exists = False
        self.last_operation = None
        self.last_operation_time = None
        self.db_stats = {}
        self._notify_listeners("state_reset")


# Global state manager instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get the global state manager instance.

    Returns:
        Global StateManager instance
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


def reset_state_manager() -> None:
    """Reset the global state manager."""
    global _state_manager
    _state_manager = None
