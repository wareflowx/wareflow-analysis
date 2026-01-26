"""Tests for OutputHandler."""

import pytest
from wareflow_analysis.common.output_handler import OutputHandler


class TestOutputHandler:
    """Test suite for OutputHandler class."""

    def test_init_cli_mode(self):
        """Test OutputHandler initialization in CLI mode."""
        handler = OutputHandler(mode="cli")
        assert handler.mode == "cli"
        assert handler.verbose is True
        assert handler.callback is None

    def test_init_gui_mode(self):
        """Test OutputHandler initialization in GUI mode."""
        callback = lambda msg: None
        handler = OutputHandler(mode="gui", callback=callback)
        assert handler.mode == "gui"
        assert handler.callback == callback

    def test_init_invalid_mode(self):
        """Test OutputHandler with invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid mode"):
            OutputHandler(mode="invalid")

    def test_print_in_cli_mode(self, capsys):
        """Test print method in CLI mode."""
        handler = OutputHandler(mode="cli", verbose=True)
        handler.print("Test message")

        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_print_in_gui_mode(self):
        """Test print method in GUI mode."""
        messages = []
        callback = messages.append

        handler = OutputHandler(mode="gui", callback=callback, verbose=True)
        handler.print("Test message")

        assert len(messages) == 1
        assert messages[0] == "Test message"

    def test_print_respects_verbose(self, capsys):
        """Test that print respects verbose setting."""
        handler = OutputHandler(mode="cli", verbose=False)
        handler.print("Test message")

        captured = capsys.readouterr()
        assert "Test message" not in captured.out

    def test_print_with_force(self, capsys):
        """Test print with force flag overrides verbose."""
        handler = OutputHandler(mode="cli", verbose=False)
        handler.print("Test message", force=True)

        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_error_in_cli_mode(self, capsys):
        """Test error method in CLI mode."""
        handler = OutputHandler(mode="cli")
        handler.error("Test error")

        captured = capsys.readouterr()
        assert "Error: Test error" in captured.err

    def test_error_in_gui_mode(self):
        """Test error method in GUI mode."""
        messages = []
        callback = messages.append

        handler = OutputHandler(mode="gui", callback=callback)
        handler.error("Test error")

        assert len(messages) == 1
        assert "ERROR: Test error" in messages[0]

    def test_warning_in_cli_mode(self, capsys):
        """Test warning method in CLI mode."""
        handler = OutputHandler(mode="cli")
        handler.warning("Test warning")

        captured = capsys.readouterr()
        assert "Warning: Test warning" in captured.out

    def test_warning_in_gui_mode(self):
        """Test warning method in GUI mode."""
        messages = []
        callback = messages.append

        handler = OutputHandler(mode="gui", callback=callback)
        handler.warning("Test warning")

        assert len(messages) == 1
        assert "WARNING: Test warning" in messages[0]

    def test_success_in_cli_mode(self, capsys):
        """Test success method in CLI mode."""
        handler = OutputHandler(mode="cli")
        handler.success("Test success")

        captured = capsys.readouterr()
        assert "✓ Test success" in captured.out

    def test_success_in_gui_mode(self):
        """Test success method in GUI mode."""
        messages = []
        callback = messages.append

        handler = OutputHandler(mode="gui", callback=callback)
        handler.success("Test success")

        assert len(messages) == 1
        assert "SUCCESS: Test success" in messages[0]

    def test_info_in_cli_mode(self, capsys):
        """Test info method in CLI mode."""
        handler = OutputHandler(mode="cli", verbose=True)
        handler.info("Test info")

        captured = capsys.readouterr()
        assert "Test info" in captured.out

    def test_info_respects_verbose(self, capsys):
        """Test info respects verbose setting."""
        handler = OutputHandler(mode="cli", verbose=False)
        handler.info("Test info")

        captured = capsys.readouterr()
        assert "Test info" not in captured.out

    def test_debug_in_cli_mode(self, capsys):
        """Test debug method in CLI mode."""
        handler = OutputHandler(mode="cli", verbose=True)
        handler.debug("Test debug")

        captured = capsys.readouterr()
        assert "DEBUG: Test debug" in captured.out

    def test_progress_in_cli_mode(self, capsys):
        """Test progress method in CLI mode."""
        handler = OutputHandler(mode="cli")
        handler.progress(50, 100, "Processing")

        captured = capsys.readouterr()
        assert "Processing [50/100]" in captured.out
        assert "50.0%" in captured.out

    def test_progress_in_gui_mode(self):
        """Test progress method in GUI mode."""
        messages = []
        callback = messages.append

        handler = OutputHandler(mode="gui", callback=callback)
        handler.progress(50, 100, "Processing")

        assert len(messages) == 1
        assert "PROGRESS:50:100:50.0:Processing" in messages[0]

    def test_progress_zero_total(self, capsys):
        """Test progress with zero total."""
        handler = OutputHandler(mode="cli")
        handler.progress(10, 0)

        captured = capsys.readouterr()
        # Should not crash, just show 0%
        assert "0.0%" in captured.out

    def test_set_callback(self):
        """Test setting callback after initialization."""
        handler = OutputHandler(mode="gui")
        assert handler.callback is None

        callback = lambda msg: None
        handler.set_callback(callback)
        assert handler.callback == callback

    def test_set_verbose(self):
        """Test setting verbose after initialization."""
        handler = OutputHandler(mode="cli", verbose=False)
        assert handler.verbose is False

        handler.set_verbose(True)
        assert handler.verbose is True
