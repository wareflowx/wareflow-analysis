"""Status view for the GUI.

This module provides the status view showing database status,
configuration information, and project statistics.
"""

import customtkinter as ctk
from typing import Optional, Callable


class StatusView(ctk.CTkFrame):
    """Status view for project and database status.

    This view displays:
    - Project configuration details
    - Database schema and tables
    - Table row counts and statistics
    - File sizes and timestamps

    Attributes:
        master: Parent widget
        state_manager: StateManager instance
        on_complete: Optional callback when view closes
    """

    def __init__(self, master, state_manager, on_complete: Optional[Callable] = None, **kwargs):
        """Initialize the StatusView.

        Args:
            master: Parent widget
            state_manager: StateManager instance
            on_complete: Optional callback when view closes
            **kwargs: Additional arguments for CTkFrame
        """
        super().__init__(master, **kwargs)

        self.state_manager = state_manager
        self.on_complete = on_complete

        self._build_ui()
        self._refresh_status()

        # Register for state changes
        self.state_manager.register_listener(self._on_state_change)

    def _build_ui(self) -> None:
        """Build the UI components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Title
        self.grid_rowconfigure(1, weight=0)  # Project info
        self.grid_rowconfigure(2, weight=1)  # Database info
        self.grid_rowconfigure(3, weight=1)  # Config info
        self.grid_rowconfigure(4, weight=0)  # Buttons

        # Title
        title_label = ctk.CTkLabel(
            self,
            text="📊 Project Status",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Project information section
        self._build_project_info()

        # Database information section
        self._build_database_info()

        # Configuration information section
        self._build_config_info()

        # Action buttons
        self._build_buttons()

    def _build_project_info(self) -> None:
        """Build the project information section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(
            frame,
            text="Project Information",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        # Info container
        self.project_info_text = ctk.CTkTextbox(
            frame,
            height=100,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.project_info_text.pack(padx=15, pady=(0, 15), fill="both", expand=True)
        self.project_info_text.configure(state="disabled")

    def _build_database_info(self) -> None:
        """Build the database information section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

        ctk.CTkLabel(
            frame,
            text="Database Information",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        # Info container
        self.database_info_text = ctk.CTkTextbox(
            frame,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.database_info_text.pack(padx=15, pady=(0, 15), fill="both", expand=True)
        self.database_info_text.configure(state="disabled")

    def _build_config_info(self) -> None:
        """Build the configuration information section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")

        ctk.CTkLabel(
            frame,
            text="Configuration File (config.yaml)",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        # Info container
        self.config_info_text = ctk.CTkTextbox(
            frame,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.config_info_text.pack(padx=15, pady=(0, 15), fill="both", expand=True)
        self.config_info_text.configure(state="disabled")

    def _build_buttons(self) -> None:
        """Build the action buttons section."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=4, column=0, padx=20, pady=(10, 20), sticky="ew")

        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack()

        refresh_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Refresh",
            width=150,
            command=self._refresh_status
        )
        refresh_btn.grid(row=0, column=0, padx=5)

        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            width=150,
            command=self._on_close
        )
        close_btn.grid(row=0, column=1, padx=5)

    def _refresh_status(self) -> None:
        """Refresh all status information."""
        # Update project info
        self._update_project_info()

        # Update database info
        self._update_database_info()

        # Update config info
        self._update_config_info()

    def _update_project_info(self) -> None:
        """Update project information display."""
        self.project_info_text.configure(state="normal")
        self.project_info_text.delete("1.0", "end")

        if not self.state_manager.is_project_loaded():
            self.project_info_text.insert("1.0", "No project loaded\n")
        else:
            project_dir = self.state_manager.get_project_dir()
            self.project_info_text.insert("1.0", f"Project Path: {project_dir}\n")
            self.project_info_text.insert("end", f"Config File: {self.state_manager.config_path}\n")
            self.project_info_text.insert("end", f"Database: {self.state_manager.db_path}\n")

            if self.state_manager.last_operation:
                self.project_info_text.insert(
                    "end",
                    f"\nLast Operation:\n  {self.state_manager.last_operation}\n"
                )
                if self.state_manager.last_operation_time:
                    time_str = self.state_manager.last_operation_time.strftime("%Y-%m-%d %H:%M:%S")
                    self.project_info_text.insert("end", f"  at {time_str}\n")

        self.project_info_text.configure(state="disabled")

    def _update_database_info(self) -> None:
        """Update database information display."""
        self.database_info_text.configure(state="normal")
        self.database_info_text.delete("1.0", "end")

        if not self.state_manager.is_database_ready():
            self.database_info_text.insert("1.0", "❌ Database not ready\n\n")
            self.database_info_text.insert("2.0", "Possible reasons:\n")
            self.database_info_text.insert("end", "  - No project loaded\n")
            self.database_info_text.insert("end", "  - Database file does not exist\n")
            self.database_info_text.insert("end", "  - Run 'Import Data' to create the database\n")
        else:
            stats = self.state_manager.get_database_stats()

            self.database_info_text.insert("1.0", f"✅ Database Status\n\n")
            self.database_info_text.insert("end", f"Database: {stats.get('database_path', 'N/A')}\n")

            db_size = self._get_file_size(stats.get('database_path'))
            self.database_info_text.insert("end", f"Size: {db_size}\n\n")

            tables = stats.get("tables", {})
            if tables:
                total_rows = sum(tables.values())
                self.database_info_text.insert("end", f"Tables ({len(tables)}, {total_rows:,} total rows):\n\n")

                for table_name, row_count in tables.items():
                    self.database_info_text.insert(
                        "end",
                        f"  {table_name:20} {row_count:>10,} rows\n"
                    )
            else:
                self.database_info_text.insert("end", "No tables found or no data imported.\n")

        self.database_info_text.configure(state="disabled")

    def _update_config_info(self) -> None:
        """Update configuration information display."""
        self.config_info_text.configure(state="normal")
        self.config_info_text.delete("1.0", "end")

        if not self.state_manager.is_project_loaded():
            self.config_info_text.insert("1.0", "No project loaded\n")
        else:
            config_path = self.state_manager.config_path

            if not config_path or not config_path.exists():
                self.config_info_text.insert("1.0", f"❌ Config file not found: {config_path}\n")
            else:
                try:
                    import yaml

                    with open(config_path, "r") as f:
                        config = yaml.safe_load(f)

                    self.config_info_text.insert("1.0", f"✅ Configuration File: {config_path}\n")
                    self.config_info_text.insert("end", f"Size: {self._get_file_size(config_path)}\n\n")

                    # Database configuration
                    if "database" in config:
                        self.config_info_text.insert("end", "Database Configuration:\n")
                        db_config = config["database"]
                        for key, value in db_config.items():
                            self.config_info_text.insert("end", f"  {key}: {value}\n")
                        self.config_info_text.insert("end", "\n")

                    # Import configuration
                    if "imports" in config:
                        imports = config["imports"]
                        self.config_info_text.insert("end", f"Import Configuration ({len(imports)} imports):\n\n")

                        for table_name, import_config in imports.items():
                            self.config_info_text.insert("end", f"  Table: {table_name}\n")
                            self.config_info_text.insert("end", f"    Source: {import_config.get('source', 'N/A')}\n")
                            self.config_info_text.insert("end", f"    Primary Key: {import_config.get('primary_key', 'N/A')}\n")
                            self.config_info_text.insert("end", "\n")

                except Exception as e:
                    self.config_info_text.insert("1.0", f"❌ Error reading config: {e}\n")

        self.config_info_text.configure(state="disabled")

    def _get_file_size(self, path) -> str:
        """Get human-readable file size.

        Args:
            path: Path to file

        Returns:
            Human-readable file size
        """
        try:
            from pathlib import Path

            path = Path(path)
            if not path.exists():
                return "N/A"

            size = path.stat().st_size

            for unit in ["B", "KB", "MB", "GB"]:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0

            return f"{size:.1f} TB"
        except Exception:
            return "N/A"

    def _on_state_change(self, event: str) -> None:
        """Handle state change events.

        Args:
            event: Event type
        """
        if event in ["project_changed", "database_changed"]:
            self._refresh_status()

    def _on_close(self) -> None:
        """Handle close button click."""
        # Unregister listener
        self.state_manager.unregister_listener(self._on_state_change)

        if self.on_complete:
            self.on_complete(None)

    def cleanup(self) -> None:
        """Clean up resources."""
        self.state_manager.unregister_listener(self._on_state_change)
