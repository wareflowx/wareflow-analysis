"""Flexible output handler for CLI and GUI modes.

This module provides a unified output interface that can work with both
CLI (print statements) and GUI (callback functions) modes.
"""

from typing import Callable, Optional, Any
import sys


class OutputHandler:
    """Handle output for both CLI and GUI modes.

    This class provides a flexible way to handle output that works in
    both CLI and GUI contexts. In CLI mode, it prints to stdout/stderr.
    In GUI mode, it sends messages to a callback function.

    Attributes:
        mode: Output mode - "cli" or "gui"
        callback: Optional callback function for GUI mode
        verbose: Whether to enable verbose output
    """

    def __init__(
        self,
        mode: str = "cli",
        callback: Optional[Callable[[str], None]] = None,
        verbose: bool = True
    ):
        """Initialize the OutputHandler.

        Args:
            mode: Output mode - "cli" or "gui"
            callback: Optional callback function for GUI mode
            verbose: Whether to enable verbose output
        """
        if mode not in ["cli", "gui"]:
            raise ValueError(f"Invalid mode: {mode}. Must be 'cli' or 'gui'")

        self.mode = mode
        self.callback = callback
        self.verbose = verbose

    def print(self, message: str, force: bool = False) -> None:
        """Print a message based on the current mode.

        Args:
            message: The message to print
            force: If True, print even if verbose is False
        """
        if not self.verbose and not force:
            return

        if self.mode == "cli":
            print(message)
        elif self.mode == "gui" and self.callback:
            self.callback(message)

    def error(self, message: str) -> None:
        """Print an error message based on the current mode.

        Args:
            message: The error message to print
        """
        if self.mode == "cli":
            print(f"Error: {message}", file=sys.stderr)
        elif self.mode == "gui" and self.callback:
            self.callback(f"ERROR: {message}")

    def warning(self, message: str) -> None:
        """Print a warning message based on the current mode.

        Args:
            message: The warning message to print
        """
        if self.mode == "cli":
            print(f"Warning: {message}")
        elif self.mode == "gui" and self.callback:
            self.callback(f"WARNING: {message}")

    def success(self, message: str) -> None:
        """Print a success message based on the current mode.

        Args:
            message: The success message to print
        """
        if self.mode == "cli":
            print(f"✓ {message}")
        elif self.mode == "gui" and self.callback:
            self.callback(f"SUCCESS: {message}")

    def info(self, message: str) -> None:
        """Print an info message based on the current mode.

        Args:
            message: The info message to print
        """
        if not self.verbose:
            return

        if self.mode == "cli":
            print(f"  {message}")
        elif self.mode == "gui" and self.callback:
            self.callback(f"INFO: {message}")

    def debug(self, message: str) -> None:
        """Print a debug message based on the current mode.

        Args:
            message: The debug message to print
        """
        if not self.verbose:
            return

        if self.mode == "cli":
            print(f"DEBUG: {message}")
        elif self.mode == "gui" and self.callback:
            self.callback(f"DEBUG: {message}")

    def progress(self, current: int, total: int, message: str = "") -> None:
        """Show progress for long-running operations.

        Args:
            current: Current progress value
            total: Total value for progress calculation
            message: Optional message to display with progress
        """
        percentage = (current / total * 100) if total > 0 else 0

        if self.mode == "cli":
            if message:
                print(f"{message} [{current}/{total}] ({percentage:.1f}%)")
            else:
                print(f"Progress: {current}/{total} ({percentage:.1f}%)")
        elif self.mode == "gui" and self.callback:
            self.callback(f"PROGRESS:{current}:{total}:{percentage}:{message}")

    def set_callback(self, callback: Callable[[str], None]) -> None:
        """Set or update the callback function.

        Args:
            callback: The callback function to set
        """
        self.callback = callback

    def set_verbose(self, verbose: bool) -> None:
        """Set verbose mode.

        Args:
            verbose: Whether to enable verbose output
        """
        self.verbose = verbose
