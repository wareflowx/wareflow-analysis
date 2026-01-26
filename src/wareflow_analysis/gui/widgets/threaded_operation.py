"""Threaded operation utility for GUI.

This module provides utilities for running operations in background threads
to prevent GUI freezing during long-running tasks.
"""

import threading
from queue import Queue
from typing import Callable, Optional, Any


class ThreadedOperation:
    """Run an operation in a background thread.

    This class executes a function in a separate thread and provides
    progress updates and result handling through callbacks.

    Attributes:
        operation: The function to execute
        callback: Optional callback for progress updates
        completion_callback: Optional callback when operation completes
        error_callback: Optional callback for error handling
        queue: Queue for thread communication
        thread: Background thread instance
    """

    def __init__(
        self,
        operation: Callable,
        callback: Optional[Callable[[str], None]] = None,
        completion_callback: Optional[Callable[[Any], None]] = None,
        error_callback: Optional[Callable[[Exception], None]] = None,
    ):
        """Initialize the ThreadedOperation.

        Args:
            operation: Function to execute in background thread
            callback: Optional callback for progress updates
            completion_callback: Optional callback when operation completes
            error_callback: Optional callback for error handling
        """
        self.operation = operation
        self.callback = callback
        self.completion_callback = completion_callback
        self.error_callback = error_callback
        self.queue = Queue()
        self.thread: Optional[threading.Thread] = None
        self._is_running = False

    def start(self) -> None:
        """Start the operation in a background thread."""
        if self._is_running:
            raise RuntimeError("Operation is already running")

        self._is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        """Run the operation and handle result."""
        try:
            result = self.operation()
            self.queue.put(("success", result))

            if self.completion_callback:
                self.completion_callback(result)
        except Exception as e:
            self.queue.put(("error", e))

            if self.error_callback:
                self.error_callback(e)
        finally:
            self._is_running = False

    def is_running(self) -> bool:
        """Check if operation is currently running.

        Returns:
            True if operation is running, False otherwise
        """
        return self._is_running

    def get_result(self, timeout: Optional[float] = None) -> tuple[str, Any]:
        """Get the operation result (blocking).

        Args:
            timeout: Optional timeout in seconds

        Returns:
            Tuple of (status, result) where status is "success" or "error"
        """
        return self.queue.get(timeout=timeout)

    def wait(self, timeout: Optional[float] = None) -> bool:
        """Wait for operation to complete.

        Args:
            timeout: Optional timeout in seconds

        Returns:
            True if operation completed, False if timeout
        """
        if self.thread:
            self.thread.join(timeout=timeout)
            return not self._is_running
        return False


def run_in_thread(
    operation: Callable,
    on_progress: Optional[Callable[[str], None]] = None,
    on_complete: Optional[Callable[[Any], None]] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
) -> ThreadedOperation:
    """Run an operation in a background thread.

    This is a convenience function that creates and starts a ThreadedOperation.

    Args:
        operation: Function to execute
        on_progress: Optional callback for progress updates
        on_complete: Optional callback when complete
        on_error: Optional callback for errors

    Returns:
        ThreadedOperation instance
    """
    threaded_op = ThreadedOperation(
        operation=operation,
        callback=on_progress,
        completion_callback=on_complete,
        error_callback=on_error,
    )
    threaded_op.start()
    return threaded_op
