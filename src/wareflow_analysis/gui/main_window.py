"""Main window for the Wareflow Analysis GUI.

This module provides the main application window with navigation
between different views.
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional

from wareflow_analysis.gui.controllers.state_manager import get_state_manager
from wareflow_analysis.gui.views import (
    HomeView,
    ImportView,
    AnalyzeView,
    ExportView,
    StatusView,
)


class MainWindow(ctk.CTk):
    """Main application window.

    This window provides:
    - Navigation between views
    - Menu bar
    - Status bar
    - View management

    Attributes:
        state_manager: StateManager instance
        current_view: Currently displayed view
        views: Dictionary of available views
    """

    def __init__(self):
        """Initialize the MainWindow."""
        super().__init__()

        self.state_manager = get_state_manager()
        self.current_view: Optional[ctk.CTkFrame] = None
        self.views = {}

        self._setup_window()
        self._build_ui()
        self._show_home_view()

    def _setup_window(self) -> None:
        """Setup window properties."""
        self.title("Wareflow Analysis")
        self.geometry("1000x700")

        # Set minimum size
        self.minsize(800, 600)

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Navigation
        self.grid_rowconfigure(1, weight=1)  # Content
        self.grid_rowconfigure(2, weight=0)  # Status bar

    def _build_ui(self) -> None:
        """Build the UI components."""
        # Navigation bar
        self._build_navigation()

        # Content container
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # Status bar
        self._build_status_bar()

    def _build_navigation(self) -> None:
        """Build the navigation bar."""
        nav_frame = ctk.CTkFrame(self, height=60)
        nav_frame.grid(row=0, column=0, sticky="ew")
        nav_frame.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            nav_frame,
            text="📦 Wareflow Analysis",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        # Navigation buttons
        button_frame = ctk.CTkFrame(nav_frame, fg_color="transparent")
        button_frame.grid(row=0, column=1, padx=20, sticky="e")

        self.nav_buttons = {}
        nav_items = [
            ("🏠 Home", "home"),
            ("📥 Import", "import"),
            ("📊 Analyze", "analyze"),
            ("📤 Export", "export"),
            ("📊 Status", "status"),
        ]

        for i, (label, view_name) in enumerate(nav_items):
            btn = ctk.CTkButton(
                button_frame,
                text=label,
                width=100,
                command=lambda v=view_name: self._navigate_to(v)
            )
            btn.grid(row=0, column=i, padx=2)
            self.nav_buttons[view_name] = btn

        # Set home button as default
        self._set_active_nav("home")

    def _build_status_bar(self) -> None:
        """Build the status bar."""
        status_frame = ctk.CTkFrame(self, height=30)
        status_frame.grid(row=2, column=0, sticky="ew")

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready",
            anchor="w",
            font=ctk.CTkFont(size=11)
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        # Project indicator
        self.project_label = ctk.CTkLabel(
            status_frame,
            text="No project",
            anchor="e",
            font=ctk.CTkFont(size=11)
        )
        self.project_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        status_frame.grid_columnconfigure(1, weight=1)

        # Update project label
        self._update_project_label()

        # Register for state changes
        self.state_manager.register_listener(self._on_state_change)

    def _show_home_view(self) -> None:
        """Show the home view."""
        self._show_view("home", lambda: HomeView(
            self.content_frame,
            self.state_manager,
            on_action_callback=self._on_home_action
        ))

    def _show_import_view(self) -> None:
        """Show the import view."""
        self._show_view("import", lambda: ImportView(
            self.content_frame,
            self.state_manager,
            on_complete=self._on_operation_complete
        ))

    def _show_analyze_view(self) -> None:
        """Show the analyze view."""
        if not self.state_manager.is_database_ready():
            self._show_error("Database not ready. Please import data first.")
            return

        self._show_view("analyze", lambda: AnalyzeView(
            self.content_frame,
            self.state_manager,
            self.state_manager.db_path,
            on_complete=self._on_operation_complete
        ))

    def _show_export_view(self) -> None:
        """Show the export view."""
        if not self.state_manager.is_database_ready():
            self._show_error("Database not ready. Please import data first.")
            return

        self._show_view("export", lambda: ExportView(
            self.content_frame,
            self.state_manager,
            self.state_manager.db_path,
            on_complete=self._on_operation_complete
        ))

    def _show_status_view(self) -> None:
        """Show the status view."""
        self._show_view("status", lambda: StatusView(
            self.content_frame,
            self.state_manager,
            on_complete=self._on_operation_complete
        ))

    def _show_view(self, view_name: str, view_factory) -> None:
        """Show a view.

        Args:
            view_name: Name of the view
            view_factory: Factory function to create the view
        """
        # Cleanup current view
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None

        # Create and show new view
        view = view_factory()
        view.grid(row=0, column=0, sticky="nsew")
        self.current_view = view

        # Store for reuse
        self.views[view_name] = view

        # Update navigation
        self._set_active_nav(view_name)

        # Update status
        self._update_status(f"View: {view_name.capitalize()}")

    def _navigate_to(self, view_name: str) -> None:
        """Navigate to a view.

        Args:
            view_name: Name of the view to navigate to
        """
        if view_name == "home":
            self._show_home_view()
        elif view_name == "import":
            self._show_import_view()
        elif view_name == "analyze":
            self._show_analyze_view()
        elif view_name == "export":
            self._show_export_view()
        elif view_name == "status":
            self._show_status_view()

    def _set_active_nav(self, active_view: str) -> None:
        """Set the active navigation button.

        Args:
            active_view: Name of the active view
        """
        for view_name, button in self.nav_buttons.items():
            if view_name == active_view:
                button.configure(fg_color="blue", hover_color="darkblue")
            else:
                button.configure(fg_color="gray", hover_color="darkgray")

    def _on_home_action(self, action: str) -> None:
        """Handle action from home view.

        Args:
            action: Action identifier
        """
        if action == "import":
            self._navigate_to("import")
        elif action == "analyze_abc":
            self._navigate_to("analyze")
            # Set ABC as default
            if self.current_view and hasattr(self.current_view, "analysis_type_var"):
                self.current_view.analysis_type_var.set("abc")
        elif action == "analyze_inventory":
            self._navigate_to("analyze")
            # Set Inventory as default
            if self.current_view and hasattr(self.current_view, "analysis_type_var"):
                self.current_view.analysis_type_var.set("inventory")
        elif action == "export":
            self._navigate_to("export")
        elif action == "validate":
            self._show_info("Validation will be implemented in the next version")

    def _on_operation_complete(self, result) -> None:
        """Handle operation completion.

        Args:
            result: Operation result
        """
        if result is None:
            # Operation was cancelled
            return

        if isinstance(result, bool):
            if result:
                self._update_status("Operation completed successfully")
            else:
                self._update_status("Operation failed")
        elif isinstance(result, str):
            self._update_status(f"Completed: {result}")
        else:
            self._update_status("Operation completed")

        # Refresh database state
        self.state_manager.update_database_state()

    def _on_state_change(self, event: str) -> None:
        """Handle state change events.

        Args:
            event: Event type
        """
        if event == "project_changed":
            self._update_project_label()

    def _update_status(self, message: str) -> None:
        """Update the status bar.

        Args:
            message: Status message
        """
        self.status_label.configure(text=message)

    def _update_project_label(self) -> None:
        """Update the project label in status bar."""
        if self.state_manager.is_project_loaded():
            project_dir = self.state_manager.get_project_dir()
            self.project_label.configure(text=f"Project: {project_dir.name}")
        else:
            self.project_label.configure(text="No project loaded")

    def _show_info(self, message: str) -> None:
        """Show an info dialog.

        Args:
            message: Info message
        """
        from tkinter import messagebox
        messagebox.showinfo("Information", message)

    def _show_error(self, message: str) -> None:
        """Show an error dialog.

        Args:
            message: Error message
        """
        from tkinter import messagebox
        messagebox.showerror("Error", message)

    def cleanup(self) -> None:
        """Clean up resources before closing."""
        if self.current_view and hasattr(self.current_view, "cleanup"):
            self.current_view.cleanup()

        self.state_manager.unregister_listener(self._on_state_change)


def main():
    """Main entry point for the GUI application."""
    # Set appearance mode
    ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"

    # Set default color theme
    ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

    # Create and run app
    app = MainWindow()

    # Handle cleanup on close
    app.protocol("WM_DELETE_WINDOW", lambda: (app.cleanup(), app.destroy()))

    app.mainloop()
