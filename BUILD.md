# Build Instructions

This document describes how to build Wareflow Analysis from source, including creating a standalone Windows executable.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Installation](#development-installation)
- [Building the Windows Executable](#building-the-windows-executable)
- [Building on Other Platforms](#building-on-other-platforms)
- [Running Tests](#running-tests)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.10 or higher
- Git
- For Windows builds: Windows 10 or later
- For development: pip and virtualenv (or uv)

## Development Installation

### Option 1: Using pip

```bash
# Clone the repository
git clone https://github.com/wareflowx/was.git
cd wareflow-analysis

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

### Option 2: Using uv (Faster)

```bash
# Clone the repository
git clone https://github.com/wareflowx/was.git
cd wareflow-analysis

# Sync dependencies with uv
uv sync

# Run tests
uv run pytest
```

## Building the Windows Executable

The Windows executable is built using PyInstaller. This creates a standalone `.exe` file that can be distributed without requiring Python installation.

### Step 1: Install Dependencies

```bash
pip install pyinstaller
pip install -e .
```

### Step 2: Build the Executable

```bash
# Build using the spec file
pyinstaller build/gui.spec --clean --noconfirm
```

This will create `dist/Warehouse-GUI.exe`.

### Step 3: Verify the Build

```bash
# Check file size (should be 50-100 MB)
ls -lh dist/Warehouse-GUI.exe

# Generate SHA256 checksum
sha256sum dist/Warehouse-GUI.exe > dist/Warehouse-GUI.exe.sha256

# Run the executable
dist/Warehouse-GUI.exe
```

### Step 4: Test the Executable

```bash
# Run smoke tests against the built executable
pytest tests/integration/test_exe_smoke.py -v
```

## PyInstaller Configuration

The build configuration is stored in `build/gui.spec`. Key settings:

- **Entry Point**: `src/wareflow_analysis/gui/__main__.py`
- **Output**: `dist/Warehouse-GUI.exe`
- **Icon**: `build/icon.ico`
- **Console**: Disabled (windowed mode)
- **UPX Compression**: Enabled

### Modifying the Build

To customize the build:

1. Edit `build/gui.spec`
2. Add/remove hidden imports if needed
3. Update version info in `build/version_info.txt`
4. Rebuild with `pyinstaller build/gui.spec --clean --noconfirm`

## Building on Other Platforms

### macOS

PyInstaller can create macOS bundles, but this has not been tested:

```bash
pyinstaller build/gui.spec --windowed
```

### Linux

For Linux, you can create an AppImage:

```bash
# Install pyinstaller
pip install pyinstaller

# Build
pyinstaller build/gui.spec --onefile

# The binary will be in dist/
```

Note: CustomTkinter may have platform-specific limitations on Linux.

## Running Tests

### All Tests

```bash
pytest
```

### Unit Tests Only

```bash
pytest tests/unit/
```

### Integration Tests

```bash
pytest tests/integration/
```

### GUI Tests

```bash
pytest tests/gui/
```

### With Coverage

```bash
pytest --cov=wareflow_analysis --cov-report=html
```

## Automated Builds

GitHub Actions automatically builds the Windows executable on:

- Every push to `main`, `develop`, and `feature/**` branches
- Every pull request
- Every version tag (creates a release)

### Downloading Build Artifacts

1. Go to the [Actions](https://github.com/wareflowx/was/actions) page
2. Select a workflow run
3. Scroll to "Artifacts" section
4. Download `wareflow-gui-windows`

### Creating a Release

To create a new release:

```bash
# Update version in pyproject.toml
vim pyproject.toml

# Commit the version bump
git add pyproject.toml
git commit -m "chore: bump version to x.y.z"

# Create and push tag
git tag vx.y.z
git push origin main --tags
```

GitHub Actions will automatically:
1. Build the executable
2. Run tests
3. Create a GitHub release
4. Upload the executable and checksum

## Troubleshooting

### Build Fails with Missing Module

If PyInstaller reports a missing module:

1. Add it to `hiddenimports` in `build/gui.spec`
2. Rebuild with `--clean` flag

Example:
```python
hiddenimports=[
    'your_missing_module',
    # ... other imports
]
```

### Executable is Too Large

If the executable is larger than expected:

1. Check if UPX compression is enabled: `upx=True`
2. Add unnecessary packages to `excludes` in `build/gui.spec`
3. Use `--exclude-module` when building

### Import Errors in Executable

If the executable fails with import errors:

1. Test the imports in a normal Python environment first
2. Check if the module is in `hiddenimports`
3. Verify data files are included in `datas` section
4. Check PyInstaller hooks for problematic packages

### GUI Doesn't Display Properly

If the GUI has rendering issues:

1. Ensure customtkinter and pillow are in `hiddenimports`
2. Check that `console=False` for windowed mode
3. Verify high DPI scaling is handled by CustomTkinter

### Antivirus False Positives

Some antivirus software may flag PyInstaller executables:

1. This is a known issue with PyInstaller
2. The executable is safe (you can verify the checksum)
3. In production, consider code signing the executable

## Performance Optimization

### Reducing File Size

Current optimization strategies in `build/gui.spec`:

- Exclude test frameworks (pytest, unittest, mock)
- Exclude development tools (ruff, black, mypy)
- Exclude unused standard library modules
- Enable UPX compression

Target file size: **50-80 MB**

### Improving Startup Time

To improve startup time:

1. Lazy load non-critical modules
2. Optimize imports in `__main__.py`
3. Profile the startup process

Target startup time: **< 3 seconds**

## Resources

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [CustomTkinter Documentation](https://customtkinter.tomschimansky.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Support

If you encounter build issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Search [existing issues](https://github.com/wareflowx/was/issues)
3. Create a new issue with:
   - Your platform and Python version
   - Full error message
   - Steps to reproduce
