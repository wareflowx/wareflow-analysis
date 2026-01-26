"""Analyze view for the GUI.

This module provides the analysis view for running warehouse analyses
including ABC classification and inventory analysis.
"""

import customtkinter as ctk
from typing import Optional, Callable


class AnalyzeView(ctk.CTkFrame):
    """Analyze view for running warehouse analyses.

    This view provides:
    - Analysis type selection (ABC, Inventory)
    - Parameter configuration
    - Analysis execution with progress tracking
    - Results preview

    Attributes:
        master: Parent widget
        state_manager: StateManager instance
        db_path: Path to database
        on_complete: Optional callback when analysis completes
    """

    def __init__(
        self,
        master,
        state_manager,
        db_path,
        on_complete: Optional[Callable] = None,
        **kwargs
    ):
        """Initialize the AnalyzeView.

        Args:
            master: Parent widget
            state_manager: StateManager instance
            db_path: Path to database
            on_complete: Optional callback when analysis completes
            **kwargs: Additional arguments for CTkFrame
        """
        super().__init__(master, **kwargs)

        self.state_manager = state_manager
        self.db_path = db_path
        self.on_complete = on_complete
        self.is_analyzing = False
        self.last_results = None

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the UI components."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Title
        self.grid_rowconfigure(1, weight=0)  # Analysis type
        self.grid_rowconfigure(2, weight=0)  # Parameters
        self.grid_rowconfigure(3, weight=0)  # Actions
        self.grid_rowconfigure(4, weight=0)  # Progress
        self.grid_rowconfigure(5, weight=1)  # Results
        self.grid_rowconfigure(6, weight=0)  # Buttons

        # Title
        title_label = ctk.CTkLabel(
            self,
            text="📊 Warehouse Analysis",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")

        # Analysis type section
        self._build_analysis_type()

        # Parameters section
        self._build_parameters()

        # Action buttons
        self._build_actions()

        # Progress section
        self._build_progress()

        # Results section
        self._build_results()

        # Bottom buttons
        self._build_bottom_buttons()

    def _build_analysis_type(self) -> None:
        """Build the analysis type selection section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(
            frame,
            text="Analysis Type",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        # Analysis type radio buttons
        radio_frame = ctk.CTkFrame(frame, fg_color="transparent")
        radio_frame.pack(padx=15, pady=(0, 15))

        self.analysis_type_var = ctk.StringVar(value="abc")

        ctk.CTkRadioButton(
            radio_frame,
            text="ABC Classification (Pareto Analysis)",
            variable=self.analysis_type_var,
            value="abc",
            command=self._on_analysis_type_changed
        ).pack(anchor="w", pady=2)

        ctk.CTkRadioButton(
            radio_frame,
            text="Inventory Analysis (Product Catalog Statistics)",
            variable=self.analysis_type_var,
            value="inventory",
            command=self._on_analysis_type_changed
        ).pack(anchor="w", pady=2)

    def _build_parameters(self) -> None:
        """Build the parameters section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(
            frame,
            text="Parameters",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        # Parameters container
        param_frame = ctk.CTkFrame(frame, fg_color="transparent")
        param_frame.pack(padx=15, pady=(0, 15), fill="x")

        # Lookback days (for ABC analysis)
        days_frame = ctk.CTkFrame(param_frame, fg_color="transparent")
        days_frame.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(days_frame, text="Lookback Period (days):").grid(row=0, column=0, sticky="w")

        self.days_entry = ctk.CTkEntry(days_frame, width=100)
        self.days_entry.insert(0, "90")
        self.days_entry.grid(row=0, column=1, padx=(10, 0))

        ctk.CTkLabel(
            days_frame,
            text="Only used for ABC analysis",
            font=ctk.CTkFont(size=10)
        ).grid(row=1, column=0, columnspan=2, sticky="w")

    def _build_actions(self) -> None:
        """Build the action buttons section."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.analyze_btn = ctk.CTkButton(
            frame,
            text="▶ Run Analysis",
            width=200,
            height=40,
            fg_color="blue",
            hover_color="darkblue",
            command=self._on_run_analysis
        )
        self.analyze_btn.pack()

    def _build_progress(self) -> None:
        """Build the progress section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.progress_label = ctk.CTkLabel(
            frame,
            text="Ready",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(padx=15, pady=(15, 10))

        self.progress_bar = ctk.CTkProgressBar(frame)
        self.progress_bar.pack(padx=15, pady=(0, 15), fill="x")
        self.progress_bar.set(0)

    def _build_results(self) -> None:
        """Build the results display section."""
        frame = ctk.CTkFrame(self)
        frame.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")

        ctk.CTkLabel(
            frame,
            text="Results",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(padx=15, pady=(15, 10))

        self.results_text = ctk.CTkTextbox(
            frame,
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.results_text.pack(padx=15, pady=(0, 15), fill="both", expand=True)
        self.results_text.insert("1.0", "Run an analysis to see results here...")

    def _build_bottom_buttons(self) -> None:
        """Build the bottom action buttons."""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=6, column=0, padx=20, pady=(10, 20), sticky="ew")

        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack()

        self.export_btn = ctk.CTkButton(
            button_frame,
            text="📤 Export Results",
            width=150,
            state="disabled",
            command=self._on_export_results
        )
        self.export_btn.grid(row=0, column=0, padx=5)

        self.clear_btn = ctk.CTkButton(
            button_frame,
            text="Clear Results",
            width=150,
            command=self._on_clear_results
        )
        self.clear_btn.grid(row=0, column=1, padx=5)

        self.close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            width=150,
            command=self._on_close
        )
        self.close_btn.grid(row=0, column=2, padx=5)

    def _on_analysis_type_changed(self) -> None:
        """Handle analysis type radio button change."""
        analysis_type = self.analysis_type_var.get()

        # Enable/disable days entry based on analysis type
        if analysis_type == "abc":
            self.days_entry.configure(state="normal")
        else:
            self.days_entry.configure(state="disabled")

    def _on_run_analysis(self) -> None:
        """Handle run analysis button click."""
        if self.is_analyzing:
            return

        if not self.state_manager.is_database_ready():
            self._append_results("Error: Database not ready. Please import data first.")
            return

        analysis_type = self.analysis_type_var.get()

        self.is_analyzing = True
        self.analyze_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Running analysis...")
        self._append_results(f"\n{'='*60}\n")
        self._append_results(f"Running {analysis_type.upper()} analysis...\n")
        self._append_results(f"{'='*60}\n\n")

        # Run analysis in thread
        from wareflow_analysis.gui.widgets import run_in_thread

        def analysis_operation():
            if analysis_type == "abc":
                from wareflow_analysis.analyze.abc import ABCAnalysis

                try:
                    days = int(self.days_entry.get())
                except ValueError:
                    days = 90

                analyzer = ABCAnalysis(self.db_path)
                success, message = analyzer.connect()

                if not success:
                    return False, message

                try:
                    results = analyzer.run(days)
                    analyzer.close()
                    return True, results
                except Exception as e:
                    analyzer.close()
                    return False, str(e)

            elif analysis_type == "inventory":
                from wareflow_analysis.analyze.inventory import InventoryAnalysis

                analyzer = InventoryAnalysis(self.db_path)
                success, message = analyzer.connect()

                if not success:
                    return False, message

                try:
                    results = analyzer.run()
                    analyzer.close()
                    return True, results
                except Exception as e:
                    analyzer.close()
                    return False, str(e)

        def on_complete(result):
            success, data = result

            if success:
                self.last_results = data
                self.last_analysis_type = analysis_type

                # Format and display results
                output = self._format_results(analysis_type, data)
                self._append_results(output)

                self.progress_label.configure(text="Analysis completed successfully")
                self.progress_bar.set(1.0)
                self.export_btn.configure(state="normal")

                if self.on_complete:
                    self.on_complete(analysis_type, data)
            else:
                self._append_results(f"Error: {data}\n")
                self.progress_label.configure(text="Analysis failed")

            self.is_analyzing = False
            self.analyze_btn.configure(state="normal")

        def on_error(error):
            self._append_results(f"Exception: {error}\n")
            self.progress_label.configure(text="Analysis failed with exception")
            self.is_analyzing = False
            self.analyze_btn.configure(state="normal")

        run_in_thread(
            operation=analysis_operation,
            on_complete=on_complete,
            on_error=on_error
        )

    def _format_results(self, analysis_type: str, results) -> str:
        """Format analysis results for display.

        Args:
            analysis_type: Type of analysis
            results: Analysis results

        Returns:
            Formatted results string
        """
        if analysis_type == "abc":
            return self._format_abc_results(results)
        elif analysis_type == "inventory":
            return self._format_inventory_results(results)
        return str(results)

    def _format_abc_results(self, results) -> str:
        """Format ABC analysis results.

        Args:
            results: ABC analysis results

        Returns:
            Formatted string
        """
        lines = []

        lines.append("ABC Classification Results\n")
        lines.append("-" * 40 + "\n")

        if "summary" in results:
            summary = results["summary"]
            lines.append(f"Analysis Period: Last {summary.get('days', 90)} days\n")
            lines.append(f"Total Products: {summary.get('total_products', 0):,}\n")
            lines.append("\n")

        if "class_distribution" in results:
            dist = results["class_distribution"]
            lines.append("Class Distribution:\n")
            for class_name, count in dist.items():
                percentage = (count / results["summary"]["total_products"] * 100) if results["summary"]["total_products"] > 0 else 0
                lines.append(f"  Class {class_name}: {count:,} products ({percentage:.1f}%)\n")

        if "top_products" in results:
            lines.append("\nTop Products:\n")
            for i, product in enumerate(results["top_products"][:10], 1):
                lines.append(f"  {i}. {product}\n")

        return "".join(lines)

    def _format_inventory_results(self, results) -> str:
        """Format inventory analysis results.

        Args:
            results: Inventory analysis results

        Returns:
            Formatted string
        """
        lines = []

        lines.append("Inventory Analysis Results\n")
        lines.append("-" * 40 + "\n")

        if "total_products" in results:
            lines.append(f"Total Products: {results['total_products']:,}\n")

        if "active_products" in results:
            lines.append(f"Active Products: {results['active_products']:,}\n")

        if "categories" in results:
            lines.append(f"\nCategories: {results['categories']:,}\n")

        if "data_quality" in results:
            lines.append("\nData Quality:\n")
            for metric, value in results["data_quality"].items():
                lines.append(f"  {metric}: {value}\n")

        return "".join(lines)

    def _append_results(self, text: str) -> None:
        """Append text to results display.

        Args:
            text: Text to append
        """
        self.results_text.insert("end", text)
        self.results_text.see("end")

    def _on_export_results(self) -> None:
        """Handle export results button click."""
        if not self.last_results:
            return

        from tkinter import filedialog

        analysis_type = getattr(self, "last_analysis_type", "abc")

        filename = filedialog.asksaveasfilename(
            title="Export Analysis Results",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=f"{analysis_type}_report.xlsx"
        )

        if filename:
            self._export_results(filename)

    def _export_results(self, output_path: str) -> None:
        """Export results to Excel file.

        Args:
            output_path: Path to output file
        """
        try:
            from pathlib import Path
            from datetime import datetime

            analysis_type = getattr(self, "last_analysis_type", "abc")
            output_path = Path(output_path)

            # Create output directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Export based on analysis type
            if analysis_type == "abc":
                from wareflow_analysis.export.reports.abc_report import ABCReportExporter
                exporter = ABCReportExporter()
                exporter.export(self.last_results, output_path)
            elif analysis_type == "inventory":
                from wareflow_analysis.export.reports.inventory_report import InventoryReportExporter
                exporter = InventoryReportExporter()
                exporter.export(self.last_results, output_path)

            self._append_results(f"\n✓ Results exported to: {output_path}\n")
        except Exception as e:
            self._append_results(f"\n✗ Export failed: {e}\n")

    def _on_clear_results(self) -> None:
        """Handle clear results button click."""
        self.results_text.delete("1.0", "end")
        self.last_results = None
        self.export_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Ready")

    def _on_close(self) -> None:
        """Handle close button click."""
        if self.on_complete:
            self.on_complete(None)
