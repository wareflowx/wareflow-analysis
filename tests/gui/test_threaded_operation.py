"""Tests for ThreadedOperation."""

import pytest
import time

from wareflow_analysis.gui.widgets.threaded_operation import (
    ThreadedOperation,
    run_in_thread,
)


class TestThreadedOperation:
    """Test suite for ThreadedOperation class."""

    def test_init(self):
        """Test ThreadedOperation initialization."""
        operation = lambda: "result"

        threaded_op = ThreadedOperation(operation)

        assert threaded_op.operation == operation
        assert threaded_op.callback is None
        assert threaded_op.completion_callback is None
        assert threaded_op.error_callback is None
        assert threaded_op._is_running is False

    def test_with_callbacks(self):
        """Test ThreadedOperation with callbacks."""
        operation = lambda: "result"
        progress_callback = lambda msg: None
        completion_callback = lambda result: None
        error_callback = lambda error: None

        threaded_op = ThreadedOperation(
            operation=operation,
            callback=progress_callback,
            completion_callback=completion_callback,
            error_callback=error_callback,
        )

        assert threaded_op.callback == progress_callback
        assert threaded_op.completion_callback == completion_callback
        assert threaded_op.error_callback == error_callback

    def test_successful_operation(self):
        """Test running a successful operation."""
        def operation():
            return "success"

        results = []
        completion_callback = results.append

        threaded_op = ThreadedOperation(
            operation=operation,
            completion_callback=completion_callback,
        )

        threaded_op.start()
        threaded_op.wait(timeout=5)

        assert len(results) == 1
        assert results[0] == "success"
        assert threaded_op.is_running() is False

    def test_failing_operation(self):
        """Test running a failing operation."""
        def operation():
            raise ValueError("Test error")

        errors = []
        error_callback = errors.append

        threaded_op = ThreadedOperation(
            operation=operation,
            error_callback=error_callback,
        )

        threaded_op.start()
        threaded_op.wait(timeout=5)

        assert len(errors) == 1
        assert isinstance(errors[0], ValueError)
        assert str(errors[0]) == "Test error"

    def test_get_result_success(self):
        """Test getting result from successful operation."""
        def operation():
            return "result"

        threaded_op = ThreadedOperation(operation=operation)
        threaded_op.start()

        status, result = threaded_op.get_result(timeout=5)

        assert status == "success"
        assert result == "result"

    def test_get_result_error(self):
        """Test getting result from failed operation."""
        def operation():
            raise ValueError("Test error")

        threaded_op = ThreadedOperation(operation=operation)
        threaded_op.start()

        status, result = threaded_op.get_result(timeout=5)

        assert status == "error"
        assert isinstance(result, ValueError)

    def test_is_running(self):
        """Test is_running method."""
        def slow_operation():
            time.sleep(0.2)
            return "done"

        threaded_op = ThreadedOperation(operation=slow_operation)

        assert threaded_op.is_running() is False

        threaded_op.start()
        assert threaded_op.is_running() is True

        threaded_op.wait(timeout=5)
        assert threaded_op.is_running() is False

    def test_start_already_running(self):
        """Test starting an already running operation."""
        def slow_operation():
            time.sleep(0.2)
            return "done"

        threaded_op = ThreadedOperation(operation=slow_operation)
        threaded_op.start()

        with pytest.raises(RuntimeError, match="already running"):
            threaded_op.start()

        threaded_op.wait(timeout=5)

    def test_wait_timeout(self):
        """Test wait with timeout."""
        def slow_operation():
            time.sleep(0.5)
            return "done"

        threaded_op = ThreadedOperation(operation=slow_operation)
        threaded_op.start()

        # Wait with short timeout
        completed = threaded_op.wait(timeout=0.1)

        assert completed is False

        # Wait for completion
        completed = threaded_op.wait(timeout=1)
        assert completed is True

    def test_run_in_thread_convenience(self):
        """Test run_in_thread convenience function."""
        def operation():
            time.sleep(0.05)  # Small delay to ensure thread starts
            return "result"

        results = []
        completion_callback = results.append

        threaded_op = run_in_thread(
            operation=operation,
            on_complete=completion_callback,
        )

        assert isinstance(threaded_op, ThreadedOperation)
        # Give thread a moment to start
        time.sleep(0.01)
        assert threaded_op.is_running() is True

        threaded_op.wait(timeout=5)

        assert len(results) == 1
        assert results[0] == "result"

    def test_progress_callback(self):
        """Test progress callback during operation."""
        def operation():
            return "result"

        progress_messages = []

        threaded_op = ThreadedOperation(
            operation=operation,
            callback=progress_messages.append,
        )

        threaded_op.start()
        threaded_op.wait(timeout=5)

        # Progress callback is stored but not automatically called
        # The operation needs to call it manually
        assert threaded_op.callback is not None

    def test_multiple_operations(self):
        """Test running multiple operations concurrently."""
        def operation(value):
            time.sleep(0.1)
            return value * 2

        results = []

        operations = []
        for i in range(5):
            op = ThreadedOperation(
                operation=lambda v=i: operation(v),
                completion_callback=results.append,
            )
            op.start()
            operations.append(op)

        # Wait for all
        for op in operations:
            op.wait(timeout=5)

        assert len(results) == 5
        assert sorted(results) == [0, 2, 4, 6, 8]
