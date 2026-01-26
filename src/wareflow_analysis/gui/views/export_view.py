"""Export view for the GUI.

This module provides the export view for generating Excel reports
from analysis results.
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime


class ExportView(ctk.CTkFrame):
    """Export view for generating Excel reports.

    This view provides:
    - Analysis source selection
    - Output filename and directory configuration
    - Export execution with progress tracking
    - Export completion dialog

    Attributes:
        master: Parent widget
        state_manager: StateManager instance
        db_path: Path to database
        on_complete: Optional callback when export completes
    """

    def __init__(
        self,
        master,
        state_manager,
        db_path,
        on_complete: Optional[Callable] = None,
        **kwargs
    ):
        """Initialize the ExportView.

        Args:
            master: Parent widget
            state_manager: StateManager instance
            db_path: Path to database
            on_complete: Optional callback when export completes
            **kwargs: Additional arguments for CTkFrame
        """
        super().__init__(master, **kwargs)

        self.state_manager = state_manager
        self.db_path = db_path
        self.on_complete = on_complete
        self.is_exporting = False

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the UI components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Title
        self.grid_rowconfigure(1, weight=0)  # Analysis source
        self.grid_rowconfigure(2, weight=0)  # Output config
        self.grid_rowconfigure(3, weight=0)  # Progress
        self.grid_rowconfigure(4, weight=1)  # Log
        self.grid_rowconfigure(5, weight=0)  # Buttons

        # Title
        title_label = ctk.CTkLabel(
            self,
            text="📤 Export Analysis Report",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Analysis source section
        self._build_analysis_source()

        # Output configuration section
        self._build_output_config()

        # Progress section
        self._build_progress()

        # Log section
        self._build_log()

        # Action buttons
        self._build_buttons()

    def _build_analysis_source(self) -> None:
        """Build the analysis source selection section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(
            frame,
            text="Analysis Source",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        # Analysis type selection
        radio_frame = ctk.CTkFrame(frame, fg_color="transparent")
        radio_frame.pack(padx=15, pady=(0, 15))

        self.analysis_var = ctk.StringVar(value="inventory")

        ctk.CTkRadioButton(
            radio_frame,
            text="Inventory Analysis Report",
            variable=self.analysis_var,
            value="inventory"
        ).pack(anchor="w", pady=2)

        ctk.CTkRadioButton(
            radio_frame,
            text="ABC Classification Report",
            variable=self.analysis_var,
            value="abc"
        ).pack(anchor="w", pady=2)

    def _build_output_config(self) -> None:
        """Build the output configuration section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(
            frame,
            text="Output Configuration",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        config_frame = ctk.CTkFrame(frame, fg_color="transparent")
        config_frame.pack(padx=15, pady=(0, 15), fill="x")

        # Output directory
        dir_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        dir_frame.grid(row=0, column=0, sticky="ew", pady=5)
        config_frame.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(dir_frame, text="Output Directory:", width=120).grid(row=0, column=0, sticky="w")

        self.dir_entry = ctk.CTkEntry(dir_frame)
        default_dir = self.state_manager.get_project_dir() / "output" if self.state_manager.is_project_loaded() else "output"
        self.dir_entry.insert(0, str(default_dir))
        self.dir_entry.grid(row=0, column=1, sticky="ew", padx=(10, 5))
        dir_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            dir_frame,
            text="Browse...",
            width=80,
            command=self._on_browse_dir
        ).grid(row=0, column=2)

        # Output filename
        file_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        file_frame.grid(row=1, column=0, sticky="ew", pady=5)

        ctk.CTkLabel(file_frame, text="Filename:", width=120).grid(row=0, column=0, sticky="w")

        self.file_entry = ctk.CTkEntry(file_frame)
        self.file_entry.grid(row=0, column=1, sticky="ew", padx=(10, 5))
        file_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            file_frame,
            text="Auto-generate",
            width=100,
            command=self._on_autogenerate_filename
        ).grid(row=0, column=2)

        # Checkbox for auto-filename
        self.autogen_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            config_frame,
            text="Auto-generate filename with timestamp",
            variable=self.autogen_var
        ).grid(row=2, column=0, sticky="w", pady=(5, 0))

    def _build_progress(self) -> None:
        """Build the progress section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.status_label = ctk.CTkLabel(
            frame,
            text="Ready to export",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(padx=15, pady=(15, 10))

        self.progress_bar = ctk.CTkProgressBar(frame)
        self.progress_bar.pack(padx=15, pady=(0, 15), fill="x")
        self.progress_bar.set(0)

    def _build_log(self) -> None:
        """Build the log section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=4, column=0, padx=20, pady=10, sticky="nsew")

        ctk.CTkLabel(
            frame,
            text="Export Log",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        self.log_text = ctk.CTkTextbox(
            frame,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.log_text.pack(padx=15, pady=(0, 15), fill="both", expand=True)

    def _build_buttons(self) -> None:
        """Build the action buttons section."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=5, column=0, padx=20, pady=(10, 20), sticky="ew")

        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack()

        self.export_btn = ctk.CTkButton(
            button_frame,
            text="▶ Export Report",
            width=150,
            height=40,
            fg_color="green",
            hover_color="darkgreen",
            command=self._on_export
        )
        self.export_btn.grid(row=0, column=0, padx=5)

        self.open_folder_btn = ctk.CTkButton(
            button_frame,
            text="Open Folder",
            width=150,
            command=self._on_open_folder
        )
        self.open_folder_btn.grid(row=0, column=1, padx=5)

        self.close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            width=150,
            command=self._on_close
        )
        self.close_btn.grid(row=0, column=2, padx=5)

    def _on_browse_dir(self) -> None:
        """Handle browse directory button click."""
        from tkinter import filedialog

        path = filedialog.askdirectory(title="Select Output Directory")

        if path:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, path)

    def _on_autogenerate_filename(self) -> None:
        """Handle auto-generate filename button click."""
        analysis = self.analysis_var.get()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{analysis}_report_{timestamp}.xlsx"
        self.file_entry.delete(0, "end")
        self.file_entry.insert(0, filename)

    def _on_export(self) -> None:
        """Handle export button click."""
        if self.is_exporting:
            return

        if not self.state_manager.is_database_ready():
            self._log("Error: Database not ready. Please import data first.")
            return

        self.is_exporting = True
        self.export_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.status_label.configure(text="Exporting...")

        # Get output path
        if self.autogen_var.get():
            self._on_autogenerate_filename()

        output_dir = Path(self.dir_entry.get())
        output_filename = self.file_entry.get()
        output_path = output_dir / output_filename

        self._log(f"Starting export to: {output_path}")

        # Run export in thread
        from wareflow_analysis.gui.widgets import run_in_thread

        def export_operation():
            analysis = self.analysis_var.get()

            # Run analysis first
            if analysis == "inventory":
                from wareflow_analysis.analyze.inventory import InventoryAnalysis
                analyzer = InventoryAnalysis(self.db_path)
                success, message = analyzer.connect()

                if not success:
                    return False, message

                try:
                    results = analyzer.run()
                    analyzer.close()
                except Exception as e:
                    analyzer.close()
                    return False, str(e)

                # Export
                from wareflow_analysis.export.reports.inventory_report import InventoryReportExporter
                exporter = InventoryReportExporter()

                try:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    exporter.export(results, output_path)
                    return True, f"Inventory report exported to {output_path}"
                except Exception as e:
                    return False, f"Export failed: {e}"

            elif analysis == "abc":
                from wareflow_analysis.analyze.abc import ABCAnalysis
                analyzer = ABCAnalysis(self.db_path)
                success, message = analyzer.connect()

                if not success:
                    return False, message

                try:
                    results = analyzer.run(days=90)
                    analyzer.close()
                except Exception as e:
                    analyzer.close()
                    return False, str(e)

                # Export
                from wareflow_analysis.export.reports.abc_report import ABCReportExporter
                exporter = ABCReportExporter()

                try:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    exporter.export(results, output_path)
                    return True, f"ABC report exported to {output_path}"
                except Exception as e:
                    return False, f"Export failed: {e}"

        def on_complete(result):
            success, message = result

            if success:
                self._log(f"✓ {message}")
                self.status_label.configure(text="Export completed successfully")
                self.progress_bar.set(1.0)

                if self.on_complete:
                    self.on_complete(str(output_path))
            else:
                self._log(f"✗ {message}")
                self.status_label.configure(text="Export failed")

            self.is_exporting = False
            self.export_btn.configure(state="normal")

        def on_error(error):
            self._log(f"✗ Exception: {error}")
            self.status_label.configure(text="Export failed with exception")
            self.is_exporting = False
            self.export_btn.configure(state="normal")

        run_in_thread(
            operation=export_operation,
            on_complete=on_complete,
            on_error=on_error
        )

    def _on_open_folder(self) -> None:
        """Handle open folder button click."""
        import subprocess
        import platform

        output_dir = Path(self.dir_entry.get())

        if not output_dir.exists():
            self._log(f"Error: Directory does not exist: {output_dir}")
            return

        try:
            if platform.system() == "Windows":
                subprocess.run(f'explorer "{output_dir}"')
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(output_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(output_dir)])
        except Exception as e:
            self._log(f"Error opening folder: {e}")

    def _on_close(self) -> None:
        """Handle close button click."""
        if self.on_complete:
            self.on_complete(None)

    def _log(self, message: str) -> None:
        """Add a message to the log.

        Args:
            message: Message to log
        """
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
