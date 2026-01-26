"""Project management dialog for creating and opening projects.

This module provides dialogs for:
- Creating a new wareflow project
- Opening an existing project
"""

import os
import customtkinter as ctk
from pathlib import Path
from typing import Optional, Callable


class NewProjectDialog(ctk.CTkToplevel):
    """Dialog for creating a new project.

    This dialog allows users to:
    - Choose a project directory
    - Enter a project name
    - Create a new wareflow project

    Attributes:
        parent: Parent window
        on_project_created: Callback when project is created
    """

    def __init__(
        self,
        parent,
        on_project_created: Optional[Callable[[Path], None]] = None,
        **kwargs
    ):
        """Initialize the NewProjectDialog.

        Args:
            parent: Parent window
            on_project_created: Optional callback when project is created
            **kwargs: Additional arguments for CTkToplevel
        """
        super().__init__(parent, **kwargs)

        self.on_project_created = on_project_created
        self.project_path: Optional[Path] = None

        self._setup_window()
        self._build_ui()

        # Make modal
        self.grab_set()

    def _setup_window(self) -> None:
        """Setup window properties."""
        self.title("Create New Project")
        self.geometry("500x350")

        # Center on parent
        self.update_idletasks()
        if self.master:
            x = self.master.winfo_x() + (self.master.winfo_width() - 500) // 2
            y = self.master.winfo_y() + (self.master.winfo_height() - 350) // 2
            self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        """Build the UI components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Title
        self.grid_rowconfigure(1, weight=0)  # Location
        self.grid_rowconfigure(2, weight=0)  # Name
        self.grid_rowconfigure(3, weight=1)  # Info
        self.grid_rowconfigure(4, weight=0)  # Buttons

        # Title
        title = ctk.CTkLabel(
            self,
            text="📁 Create New Wareflow Project",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Location frame
        location_frame = ctk.CTkFrame(self, fg_color="transparent")
        location_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        location_frame.grid_columnconfigure(0, weight=0)
        location_frame.grid_columnconfigure(1, weight=1)
        location_frame.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(
            location_frame,
            text="Location:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.location_entry = ctk.CTkEntry(location_frame, placeholder_text="Select parent directory")
        self.location_entry.grid(row=0, column=1, padx=5, sticky="ew")
        self.location_entry.insert(0, str(Path.home() / "Documents"))

        browse_btn = ctk.CTkButton(
            location_frame,
            text="Browse...",
            width=80,
            command=self._browse_location
        )
        browse_btn.grid(row=0, column=2, padx=(5, 0), sticky="e")

        # Name frame
        name_frame = ctk.CTkFrame(self, fg_color="transparent")
        name_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        name_frame.grid_columnconfigure(0, weight=0)
        name_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            name_frame,
            text="Project name:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.name_entry = ctk.CTkEntry(name_frame, placeholder_text="my-warehouse")
        self.name_entry.grid(row=0, column=1, padx=5, sticky="ew")

        # Info text
        info_label = ctk.CTkLabel(
            self,
            text="This will create a new directory with:\n"
                 "• config.yaml\n"
                 "• data/ (for Excel files)\n"
                 "• output/ (for reports)\n"
                 "• scripts/ (for custom scripts)",
            font=ctk.CTkFont(size=11),
            justify="left"
        )
        info_label.grid(row=3, column=0, padx=20, pady=10, sticky="nw")

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=4, column=0, padx=20, pady=(10, 20), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=0)
        button_frame.grid_columnconfigure(2, weight=0)

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=100,
            command=self.destroy
        ).grid(row=0, column=1, padx=5)

        create_btn = ctk.CTkButton(
            button_frame,
            text="Create",
            width=100,
            fg_color="green",
            hover_color="darkgreen",
            command=self._create_project
        )
        create_btn.grid(row=0, column=2, padx=5)

    def _browse_location(self) -> None:
        """Browse for project location."""
        from tkinter import filedialog

        location = filedialog.askdirectory(
            title="Select Parent Directory",
            initialdir=self.location_entry.get()
        )

        if location:
            self.location_entry.delete(0, "end")
            self.location_entry.insert(0, location)

    def _create_project(self) -> None:
        """Create the project."""
        location = self.location_entry.get().strip()
        name = self.name_entry.get().strip()

        if not location:
            self._show_error("Please select a location")
            return

        if not name:
            self._show_error("Please enter a project name")
            return

        # Validate name
        if not name.replace("-", "").replace("_", "").isalnum():
            self._show_error(
                "Project name must contain only letters, numbers, hyphens, and underscores"
            )
            return

        # Create project path
        project_path = Path(location) / name

        if project_path.exists():
            self._show_error(f"Directory '{name}' already exists")
            return

        try:
            # Import the CLI init function
            from wareflow_analysis.cli import app as cli_app
            from typer.testing import CliRunner

            # Change to parent directory
            original_cwd = os.getcwd()
            os.chdir(location)

            try:
                # Run wareflow init
                runner = CliRunner()
                result = runner.invoke(
                    cli_app,
                    ["init", name, "--force"],
                    catch_exceptions=False
                )

                if result.exit_code != 0:
                    raise Exception(result.stderr or "Failed to create project")

            finally:
                os.chdir(original_cwd)

            self.project_path = project_path

            # Call callback
            if self.on_project_created:
                self.on_project_created(project_path)

            self._show_success("Project created successfully!")
            self.destroy()

        except Exception as e:
            self._show_error(f"Failed to create project: {str(e)}")

    def _show_error(self, message: str) -> None:
        """Show an error message.

        Args:
            message: Error message
        """
        from tkinter import messagebox
        messagebox.showerror("Error", message, parent=self)

    def _show_success(self, message: str) -> None:
        """Show a success message.

        Args:
            message: Success message
        """
        from tkinter import messagebox
        messagebox.showinfo("Success", message, parent=self)


class OpenProjectDialog(ctk.CTkToplevel):
    """Dialog for opening an existing project.

    This dialog allows users to browse and select an existing
    wareflow project directory.

    Attributes:
        parent: Parent window
        on_project_opened: Callback when project is opened
    """

    def __init__(
        self,
        parent,
        on_project_opened: Optional[Callable[[Path], None]] = None,
        **kwargs
    ):
        """Initialize the OpenProjectDialog.

        Args:
            parent: Parent window
            on_project_opened: Optional callback when project is opened
            **kwargs: Additional arguments for CTkToplevel
        """
        super().__init__(parent, **kwargs)

        self.on_project_opened = on_project_opened
        self.project_path: Optional[Path] = None

        self._setup_window()
        self._build_ui()

        # Make modal
        self.grab_set()

    def _setup_window(self) -> None:
        """Setup window properties."""
        self.title("Open Project")
        self.geometry("500x200")

        # Center on parent
        self.update_idletasks()
        if self.master:
            x = self.master.winfo_x() + (self.master.winfo_width() - 500) // 2
            y = self.master.winfo_y() + (self.master.winfo_height() - 200) // 2
            self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        """Build the UI components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Title
        self.grid_rowconfigure(1, weight=1)  # Info
        self.grid_rowconfigure(2, weight=0)  # Buttons

        # Title
        title = ctk.CTkLabel(
            self,
            text="📂 Open Wareflow Project",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Info text
        info_label = ctk.CTkLabel(
            self,
            text="Select a directory containing config.yaml\n"
                 "to open an existing wareflow project.",
            font=ctk.CTkFont(size=11),
            justify="center"
        )
        info_label.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # Buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=0)
        button_frame.grid_columnconfigure(2, weight=0)

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=100,
            command=self.destroy
        ).grid(row=0, column=1, padx=5)

        browse_btn = ctk.CTkButton(
            button_frame,
            text="Browse...",
            width=100,
            fg_color="blue",
            hover_color="darkblue",
            command=self._browse_project
        )
        browse_btn.grid(row=0, column=2, padx=5)

    def _browse_project(self) -> None:
        """Browse for project directory."""
        from tkinter import filedialog

        project_dir = filedialog.askdirectory(
            title="Select Project Directory",
            initialdir=str(Path.home())
        )

        if not project_dir:
            return

        project_path = Path(project_dir)

        # Check if it's a valid project
        config_file = project_path / "config.yaml"
        if not config_file.exists():
            self._show_error(
                f"'{project_path.name}' is not a valid wareflow project.\n"
                f"config.yaml not found."
            )
            return

        self.project_path = project_path

        # Call callback
        if self.on_project_opened:
            self.on_project_opened(project_path)

        self.destroy()

    def _show_error(self, message: str) -> None:
        """Show an error message.

        Args:
            message: Error message
        """
        from tkinter import messagebox
        messagebox.showerror("Error", message, parent=self)
