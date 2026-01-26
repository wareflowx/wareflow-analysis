"""Home view (dashboard) for the GUI.

This module provides the main dashboard view showing project status,
database statistics, and quick action buttons.
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional, Callable


class HomeView(ctk.CTkFrame):
    """Home dashboard view.

    This view displays:
    - Project path and status
    - Database statistics
    - Quick action buttons
    - Recent activity log

    Attributes:
        master: Parent widget
        state_manager: StateManager instance
        on_action_callback: Callback for action button clicks
    """

    def __init__(
        self,
        master,
        state_manager,
        on_action_callback: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        """Initialize the HomeView.

        Args:
            master: Parent widget
            state_manager: StateManager instance
            on_action_callback: Optional callback for action buttons
            **kwargs: Additional arguments for CTkFrame
        """
        super().__init__(master, **kwargs)

        self.state_manager = state_manager
        self.on_action_callback = on_action_callback

        self._build_ui()
        self._refresh_display()

        # Register for state changes
        self.state_manager.register_listener(self._on_state_change)

    def _build_ui(self) -> None:
        """Build the UI components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=0)  # Project info
        self.grid_rowconfigure(2, weight=0)  # Database stats
        self.grid_rowconfigure(3, weight=0)  # Quick actions
        self.grid_rowconfigure(4, weight=1)  # Activity log

        # Title
        title_label = ctk.CTkLabel(
            self,
            text="📦 Wareflow Analysis Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Project Info Frame
        self._build_project_info()

        # Database Stats Frame
        self._build_database_stats()

        # Quick Actions Frame
        self._build_quick_actions()

        # Activity Log Frame
        self._build_activity_log()

    def _build_project_info(self) -> None:
        """Build the project information section."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        frame.grid_columnconfigure(0, weight=0)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(2, weight=0)

        # Label
        ctk.CTkLabel(
            frame,
            text="Project:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=(0, 10), sticky="w")

        # Project path
        self.project_path_label = ctk.CTkLabel(
            frame,
            text="No project loaded",
            font=ctk.CTkFont(size=13)
        )
        self.project_path_label.grid(row=0, column=1, sticky="w")

        # Buttons frame
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.grid(row=0, column=2, padx=(10, 0))

        # New project button
        new_btn = ctk.CTkButton(
            button_frame,
            text="+ New",
            width=80,
            fg_color="green",
            hover_color="darkgreen",
            command=self._on_new_project
        )
        new_btn.grid(row=0, column=0, padx=2)

        # Browse button
        browse_btn = ctk.CTkButton(
            button_frame,
            text="Open...",
            width=80,
            command=self._on_open_project
        )
        browse_btn.grid(row=0, column=1, padx=2)

    def _build_database_stats(self) -> None:
        """Build the database statistics section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Title
        ctk.CTkLabel(
            frame,
            text="Database Status",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        # Stats container
        self.stats_text = ctk.CTkTextbox(
            frame,
            height=120,
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.stats_text.pack(padx=15, pady=(0, 15), fill="both", expand=True)
        self.stats_text.configure(state="disabled")

    def _build_quick_actions(self) -> None:
        """Build the quick actions section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Title
        ctk.CTkLabel(
            frame,
            text="Quick Actions",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        # Button container
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack(padx=15, pady=(0, 15))

        # Action buttons
        actions = [
            ("📥 Import Data", "import"),
            ("📊 Run ABC Analysis", "analyze_abc"),
            ("📈 Run Inventory Analysis", "analyze_inventory"),
            ("📤 Export Report", "export"),
            ("✓ Validate Data", "validate"),
        ]

        for i, (label, action) in enumerate(actions):
            btn = ctk.CTkButton(
                button_frame,
                text=label,
                width=180,
                height=35,
                command=lambda a=action: self._on_action(a)
            )
            btn.grid(row=i // 3, column=i % 3, padx=5, pady=5)

    def _build_activity_log(self) -> None:
        """Build the activity log section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=4, column=0, padx=20, pady=(10, 20), sticky="nsew")

        # Title
        ctk.CTkLabel(
            frame,
            text="Recent Activity",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        # Log text
        self.activity_text = ctk.CTkTextbox(
            frame,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.activity_text.pack(padx=15, pady=(0, 15), fill="both", expand=True)
        self.activity_text.configure(state="disabled")

    def _on_new_project(self) -> None:
        """Handle new project button click."""
        from wareflow_analysis.gui.widgets.project_dialog import NewProjectDialog

        NewProjectDialog(
            self,
            on_project_created=self._on_project_created
        )

    def _on_open_project(self) -> None:
        """Handle open project button click."""
        from wareflow_analysis.gui.widgets.project_dialog import OpenProjectDialog

        OpenProjectDialog(
            self,
            on_project_opened=self._on_project_opened
        )

    def _on_project_created(self, project_path: Path) -> None:
        """Handle project creation callback.

        Args:
            project_path: Path to the created project
        """
        success = self.state_manager.set_project_dir(project_path)
        if success:
            self._refresh_display()
            self._log(f"Project created: {project_path.name}")
        else:
            self._log("Error: Failed to load newly created project")

    def _on_project_opened(self, project_path: Path) -> None:
        """Handle project opened callback.

        Args:
            project_path: Path to the opened project
        """
        success = self.state_manager.set_project_dir(project_path)
        if success:
            self._refresh_display()
            self._log(f"Project opened: {project_path.name}")
        else:
            self._log("Error: Failed to load project")

    def _on_action(self, action: str) -> None:
        """Handle action button click.

        Args:
            action: Action identifier
        """
        if self.on_action_callback:
            self.on_action_callback(action)

    def _on_state_change(self, event: str) -> None:
        """Handle state change events.

        Args:
            event: Event type
        """
        if event in ["project_changed", "database_changed"]:
            self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh the display with current state."""
        # Update project path
        if self.state_manager.is_project_loaded():
            project_path = str(self.state_manager.get_project_dir())
            self.project_path_label.configure(text=project_path)
        else:
            self.project_path_label.configure(text="No project loaded")

        # Update database stats
        self._update_database_stats()

    def _update_database_stats(self) -> None:
        """Update database statistics display."""
        self.stats_text.configure(state="normal")
        self.stats_text.delete("1.0", "end")

        if not self.state_manager.is_database_ready():
            self.stats_text.insert("1.0", "❌ Database not ready\n\n")
            self.stats_text.insert("2.0", "Run 'Import Data' to create the database")
        else:
            stats = self.state_manager.get_database_stats()

            self.stats_text.insert("1.0", f"✅ Database: {stats.get('database_path', 'N/A')}\n\n")

            tables = stats.get("tables", {})
            if tables:
                self.stats_text.insert("end", "Tables:\n")
                for table_name, row_count in tables.items():
                    self.stats_text.insert("end", f"  {table_name:20} {row_count:>10,} rows\n")
            else:
                self.stats_text.insert("end", "No data imported yet\n")

        self.stats_text.configure(state="disabled")

    def _log(self, message: str) -> None:
        """Add a message to the activity log.

        Args:
            message: Message to log
        """
        self.activity_text.configure(state="normal")
        self.activity_text.insert("end", f"• {message}\n")
        self.activity_text.see("end")
        self.activity_text.configure(state="disabled")

    def cleanup(self) -> None:
        """Clean up resources."""
        self.state_manager.unregister_listener(self._on_state_change)
