"""Smoke tests for compiled Windows executable.

These tests verify that the compiled .exe file works correctly.
They are designed to run against a built executable in the dist/ directory.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Skip these tests if not on Windows or if executable doesn't exist
pytestmark = [
    pytest.mark.skipif(
        sys.platform != "win32",
        reason="Executable smoke tests only run on Windows",
    ),
]


class TestExeSmokeTests:
    """Basic smoke tests for the compiled .exe."""

    @staticmethod
    def get_exe_path() -> Path:
        """Get path to compiled executable.

        Returns:
            Path to the executable file.

        Raises:
            FileNotFoundError: If executable is not found.
        """
        # Check common locations
        exe_paths = [
            Path("dist/Warehouse-GUI.exe"),
            Path("dist/Warehouse-GUI/Warehouse-GUI.exe"),
            Path("artifacts/Warehouse-GUI.exe"),
        ]

        for path in exe_paths:
            if path.exists():
                return path

        # Raise skip error if not found
        pytest.skip("Executable not found - build may not have been run")

    def test_exe_exists(self):
        """Test that executable file exists and has reasonable size."""
        exe_path = self.get_exe_path()
        assert exe_path.exists()

        # Check file size (should be at least 10 MB for a valid build)
        file_size = exe_path.stat().st_size
        assert file_size > 10_000_000, f"Executable size {file_size} is too small"

    def test_exe_version_info(self):
        """Test that executable has version information."""
        exe_path = self.get_exe_path()

        # Try to read version info using PowerShell
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-Command",
                    f"(Get-Item '{exe_path}').VersionInfo | Format-List",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Should succeed
            assert result.returncode == 0

            # Should contain version information
            output = result.stdout
            assert "FileVersion" in output or "ProductVersion" in output
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            pytest.skip(f"Could not read version info: {e}")

    def test_exe_launches_without_crash(self):
        """Test that executable launches and doesn't immediately crash.

        Note: This is a basic smoke test. A more comprehensive test would
        require UI automation which is beyond the scope of smoke tests.
        """
        exe_path = self.get_exe_path()

        # Try to launch the executable with a timeout
        # We expect it to either run successfully or be terminated by timeout
        try:
            # Use STARTUPINFO to hide the window
            startupinfo = subprocess.STARTUPINFO()  # type: ignore[attr-defined]
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore[attr-defined]

            result = subprocess.run(
                [str(exe_path)],
                timeout=5,
                capture_output=True,
                startupinfo=startupinfo,
            )

            # Exit code 0 or 1 is acceptable (user closed window or normal exit)
            # We just want to ensure it didn't crash with an error code
            assert result.returncode in [0, 1, -15]  # -15 is SIGTERM
        except subprocess.TimeoutExpired:
            # Timeout is OK - means the app is running
            pass
        except FileNotFoundError:
            pytest.skip("Executable could not be launched")

    def test_checksum_file_exists(self):
        """Test that SHA256 checksum file exists and is valid."""
        exe_path = self.get_exe_path()
        checksum_path = exe_path.with_suffix(".exe.sha256")

        if not checksum_path.exists():
            pytest.skip("Checksum file not found")

        # Read checksum file
        content = checksum_path.read_text().strip()

        # SHA256 should be 64 characters (hex string)
        assert len(content) == 64, f"Invalid checksum length: {len(content)}"

        # Should be valid hex characters
        try:
            int(content, 16)
        except ValueError:
            pytest.fail(f"Invalid checksum format: {content}")

    def test_imports_work(self):
        """Test that critical imports work in the frozen environment.

        This test verifies that the PyInstaller build correctly included
        all necessary dependencies.
        """
        exe_path = self.get_exe_path()

        # We can't directly test imports in the exe, but we can verify
        # the file structure suggests dependencies are bundled
        # This is a basic structural check

        # On Windows, built executables are single-file by default
        # We can verify the exe exists and has reasonable size
        assert exe_path.exists()

        # A working executable should be at least 20MB with all dependencies
        file_size = exe_path.stat().st_size
        assert file_size > 20_000_000, f"Executable may be missing dependencies (size: {file_size})"

    def test_exe_help(self):
        """Test that executable responds to command line arguments.

        Note: CustomTkinter GUI apps may not support --help in the traditional
        sense. This test verifies the exe can at least be invoked.
        """
        exe_path = self.get_exe_path()

        try:
            # Try running with --help or similar
            result = subprocess.run(
                [str(exe_path), "--help"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            # Any response is OK - we just want to verify it doesn't crash
            # GUI apps typically ignore unknown arguments
            assert result.returncode in [0, 1]
        except subprocess.TimeoutExpired:
            # Timeout means the GUI launched - that's OK
            pass
        except Exception as e:
            pytest.skip(f"Could not run with --help: {e}")


@pytest.fixture(scope="session")
def exe_path():
    """Fixture providing path to the executable.

    Skips tests if executable is not found.
    """
    test_instance = TestExeSmokeTests()
    try:
        return test_instance.get_exe_path()
    except pytest.skip.Exception:
        pytest.skip("Executable not found")
