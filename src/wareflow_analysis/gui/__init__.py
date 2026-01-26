"""Wareflow Analysis GUI.

This package provides a graphical user interface for the Wareflow Analysis
warehouse data analysis tool, built with CustomTkinter.

The GUI wraps all existing CLI functionality and provides an intuitive
interface for non-technical users.
"""

from wareflow_analysis.gui.main_window import MainWindow, main

__all__ = ["MainWindow", "main"]
