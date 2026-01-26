"""Import view for the GUI.

This module provides the import view for importing Excel data
into the database with progress tracking.
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional, Callable


class ImportView(ctk.CTkFrame):
    """Import view for Excel data import.

    This view provides:
    - File selection for Excel files
    - Configuration generation (Auto-Pilot)
    - Import execution with progress tracking
    - Import summary with success/error counts

    Attributes:
        master: Parent widget
        state_manager: StateManager instance
        on_complete: Optional callback when import completes
    """

    def __init__(self, master, state_manager, on_complete: Optional[Callable] = None, **kwargs):
        """Initialize the ImportView.

        Args:
            master: Parent widget
            state_manager: StateManager instance
            on_complete: Optional callback when import completes
            **kwargs: Additional arguments for CTkFrame
        """
        super().__init__(master, **kwargs)

        self.state_manager = state_manager
        self.on_complete = on_complete
        self.is_importing = False

        self._build_ui()
        self._load_existing_config()

    def _build_ui(self) -> None:
        """Build the UI components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Title
        self.grid_rowconfigure(1, weight=0)  # Config section
        self.grid_rowconfigure(2, weight=0)  # File selection
        self.grid_rowconfigure(3, weight=0)  # Options
        self.grid_rowconfigure(4, weight=0)  # Progress
        self.grid_rowconfigure(5, weight=1)  # Output log
        self.grid_rowconfigure(6, weight=0)  # Buttons

        # Title
        title_label = ctk.CTkLabel(
            self,
            text="📥 Import Excel Data",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Configuration section
        self._build_config_section()

        # File selection section
        self._build_file_selection()

        # Options section
        self._build_options()

        # Progress section
        self._build_progress()

        # Output log section
        self._build_output_log()

        # Action buttons
        self._build_action_buttons()

    def _build_config_section(self) -> None:
        """Build the configuration generation section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(
            frame,
            text="1️⃣ Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack(padx=15, pady=(0, 15))

        self.generate_config_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            button_frame,
            text="Generate config from Excel files (Auto-Pilot)",
            variable=self.generate_config_var
        ).pack(anchor="w")

    def _build_file_selection(self) -> None:
        """Build the file selection section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(
            frame,
            text="2️⃣ Source Files",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        # File entries
        file_frame = ctk.CTkFrame(frame, fg_color="transparent")
        file_frame.pack(padx=15, pady=(0, 15), fill="x")

        self.file_entries = {}
        self.file_labels = {
            "Products": "Products Excel file",
            "Movements": "Movements Excel file",
            "Orders": "Orders Excel file",
        }

        for i, (key, label) in enumerate(self.file_labels.items()):
            row_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
            row_frame.grid(row=i, column=0, sticky="ew", pady=5)
            file_frame.grid_rowconfigure(i, weight=1)

            ctk.CTkLabel(row_frame, text=label, width=150).grid(row=0, column=0, sticky="w")

            entry = ctk.CTkEntry(row_frame)
            entry.grid(row=0, column=1, sticky="ew", padx=(10, 5))
            row_frame.grid_columnconfigure(1, weight=1)

            btn = ctk.CTkButton(
                row_frame,
                text="Browse...",
                width=80,
                command=lambda k=key.lower(): self._on_browse_file(k)
            )
            btn.grid(row=0, column=2)

            self.file_entries[key.lower()] = entry

    def _build_options(self) -> None:
        """Build the options section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(
            frame,
            text="3️⃣ Options",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        options_frame = ctk.CTkFrame(frame, fg_color="transparent")
        options_frame.pack(padx=15, pady=(0, 15))

        self.verbose_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_frame,
            text="Show verbose output",
            variable=self.verbose_var
        ).pack(anchor="w")

        self.backup_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_frame,
            text="Create backup before import",
            variable=self.backup_var
        ).pack(anchor="w")

    def _build_progress(self) -> None:
        """Build the progress section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(
            frame,
            text="4️⃣ Progress",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(frame)
        self.progress_bar.pack(padx=15, pady=(0, 10), fill="x")
        self.progress_bar.set(0)

        # Status label
        self.status_label = ctk.CTkLabel(
            frame,
            text="Ready to import",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(padx=15, pady=(0, 15))

    def _build_output_log(self) -> None:
        """Build the output log section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")

        ctk.CTkLabel(
            frame,
            text="5️⃣ Import Log",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        self.output_text = ctk.CTkTextbox(
            frame,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.output_text.pack(padx=15, pady=(0, 15), fill="both", expand=True)

    def _build_action_buttons(self) -> None:
        """Build the action buttons section."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=6, column=0, padx=20, pady=(10, 20), sticky="ew")

        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack()

        self.generate_btn = ctk.CTkButton(
            button_frame,
            text="Generate Config",
            width=150,
            command=self._on_generate_config
        )
        self.generate_btn.grid(row=0, column=0, padx=5)

        self.import_btn = ctk.CTkButton(
            button_frame,
            text="Start Import",
            width=150,
            command=self._on_start_import,
            fg_color="green"
        )
        self.import_btn.grid(row=0, column=1, padx=5)

        self.close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            width=150,
            command=self._on_close
        )
        self.close_btn.grid(row=0, column=2, padx=5)

    def _load_existing_config(self) -> None:
        """Load existing configuration if available."""
        if not self.state_manager.is_project_loaded():
            return

        config_path = self.state_manager.config_path
        if not config_path or not config_path.exists():
            return

        try:
            import yaml
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            # Load file paths from config
            imports = config.get("imports", {})
            for key, entry in self.file_entries.items():
                if key in imports:
                    entry.delete(0, "end")
                    entry.insert(0, imports[key].get("source", ""))

            self._log("Configuration loaded from existing config.yaml")
        except Exception as e:
            self._log(f"Error loading config: {e}")

    def _on_browse_file(self, file_key: str) -> None:
        """Handle browse file button click.

        Args:
            file_key: Key identifying which file to browse for
        """
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            title=f"Select {self.file_labels[file_key.capitalize()]}",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )

        if path:
            self.file_entries[file_key].delete(0, "end")
            self.file_entries[file_key].insert(0, path)

    def _on_generate_config(self) -> None:
        """Handle generate config button click."""
        if not self.state_manager.is_project_loaded():
            self._log("Error: No project loaded")
            return

        self._log("Generating configuration with Auto-Pilot...")

        try:
            from wareflow_analysis.data_import.importer import init_import_config

            data_dir = self.state_manager.project_dir / "data"
            success, message = init_import_config(
                data_dir,
                self.state_manager.project_dir,
                verbose=True
            )

            if success:
                self._log(f"✓ {message}")
                self._load_existing_config()
            else:
                self._log(f"✗ Error: {message}")
        except Exception as e:
            self._log(f"✗ Error generating config: {e}")

    def _on_start_import(self) -> None:
        """Handle start import button click."""
        if self.is_importing:
            return

        if not self.state_manager.is_project_loaded():
            self._log("Error: No project loaded")
            return

        self.is_importing = True
        self.import_btn.configure(state="disabled")
        self.generate_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self._log("Starting import...")

        # Run import in thread
        from wareflow_analysis.gui.widgets import run_in_thread

        def import_operation():
            from wareflow_analysis.data_import.importer import run_import

            success, message = run_import(
                self.state_manager.project_dir,
                verbose=self.verbose_var.get()
            )

            return success, message

        def on_complete(result):
            success, message = result
            if success:
                self._log(f"✓ {message}")
                self.status_label.configure(text="Import completed successfully")
                self.progress_bar.set(1.0)

                # Refresh database stats
                self.state_manager.refresh_database_stats()

                if self.on_complete:
                    self.on_complete(success)
            else:
                self._log(f"✗ Error: {message}")
                self.status_label.configure(text="Import failed")

            self.is_importing = False
            self.import_btn.configure(state="normal")
            self.generate_btn.configure(state="normal")

        def on_error(error):
            self._log(f"✗ Exception: {error}")
            self.status_label.configure(text="Import failed with exception")
            self.is_importing = False
            self.import_btn.configure(state="normal")
            self.generate_btn.configure(state="normal")

        def on_progress(message):
            self._log(message)
            # Update progress bar (estimated)
            current = self.progress_bar.get()
            self.progress_bar.set(min(current + 0.1, 0.9))

        run_in_thread(
            operation=import_operation,
            on_complete=on_complete,
            on_error=on_error,
            on_progress=on_progress
        )

    def _on_close(self) -> None:
        """Handle close button click."""
        if self.on_complete:
            self.on_complete(None)

    def _log(self, message: str) -> None:
        """Add a message to the output log.

        Args:
            message: Message to log
        """
        self.output_text.insert("end", f"{message}\n")
        self.output_text.see("end")
