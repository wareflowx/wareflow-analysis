# Build Directory

This directory contains configuration files and assets for building the standalone Windows executable.

## Files

- **gui.spec** - PyInstaller configuration for building the executable
- **icon.ico** - Application icon (multi-resolution Windows icon)
- **create_icon.py** - Script to regenerate the application icon
- **version_info.txt** - Windows version information resource

## Building the Executable

### Local Build

To build the executable locally:

```bash
# Install PyInstaller
pip install pyinstaller

# Build the executable
pyinstaller build/gui.spec --clean --noconfirm

# The executable will be in: dist/Warehouse-GUI.exe
```

### Automated Build

The executable is automatically built by GitHub Actions on:
- Every push to `main`, `develop`, or `feature/*` branches
- Pull requests to `main` or `develop`
- Manual trigger via GitHub Actions UI

Artifacts are available for download from the Actions page.

## Icon

The application icon was generated using `create_icon.py`. To regenerate:

```bash
cd build
python create_icon.py
```

This will create a new `icon.ico` with multiple resolutions (16x16 to 256x256).

## Version Information

Version information is stored in `version_info.txt` and embedded in the executable.
To update the version, edit `version_info.txt` and rebuild.
