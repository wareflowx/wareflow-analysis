# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller configuration for Wareflow Analysis GUI.

This spec file creates a standalone Windows executable that includes
all dependencies and can run without Python installation.
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# PyInstaller executes this from the repository root
# Use os.getcwd() to get the current working directory
REPO_ROOT = os.getcwd()
SPEC_DIR = os.path.join(REPO_ROOT, 'build')

# Collect all data files from excel_to_sql
excel_to_sql_datas = collect_data_files('excel_to_sql')

a = Analysis(
    [os.path.join(REPO_ROOT, 'src', 'wareflow_analysis', 'gui', '__main__.py')],
    pathex=[REPO_ROOT],
    binaries=[],
    datas=[
        # Source code
        (os.path.join(REPO_ROOT, 'src', 'wareflow_analysis'), 'wareflow_analysis'),

        # Templates
        (os.path.join(REPO_ROOT, 'src', 'wareflow_analysis', 'templates'), 'wareflow_analysis/templates'),

        # Excel-to-SQL data files
        *[(os.path.join(REPO_ROOT, src), dst) for src, dst in excel_to_sql_datas],
    ],
    hiddenimports=[
        # GUI framework
        'customtkinter',
        'tkinter',
        '_tkinter',

        # Data processing
        'pandas',
        'pandas._libs.tslibs.base',
        'pandas._libs.tslibs.dtypes',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.nattype',
        'pandas._libs.tslibs.timestamps',
        'pandas._libs.tslibs.period',
        'pandas._libs.tslibs.vectorized',

        # Excel handling
        'openpyxl',
        'openpyxl.cell._writer',
        'openpyxl.styles',
        'openpyxl.utils',

        # Configuration
        'yaml',
        'yaml.constructor',

        # Database
        'sqlite3',
        '_sqlite3',

        # Image handling
        'PIL',
        'PIL._tkinter_finder',
        'PIL.Image',

        # Theme detection
        'darkdetect',

        # Excel-to-SQL
        'excel_to_sql',
        'excel_to_sql.auto_pilot',  # Used by autopilot.py for PatternDetector

        # Wareflow Analysis modules (for CLI integration via CliRunner)
        'wareflow_analysis',
        'wareflow_analysis.cli',
        'wareflow_analysis.init',
        'wareflow_analysis.data_import',
        'wareflow_analysis.data_import.autopilot',
        'wareflow_analysis.data_import.importer',
        'wareflow_analysis.data_import.header_detector',
        'wareflow_analysis.validation',
        'wareflow_analysis.validation.validator',
        'wareflow_analysis.validation.reporters',
        'wareflow_analysis.analyze',
        'wareflow_analysis.analyze.abc',
        'wareflow_analysis.analyze.inventory',
        'wareflow_analysis.export',
        'wareflow_analysis.export.reports',
        'wareflow_analysis.export.reports.abc_report',
        'wareflow_analysis.export.reports.inventory_report',
        'wareflow_analysis.export.excel_builder',
        'wareflow_analysis.export.excel_formatters',
        'wareflow_analysis.database',
        'wareflow_analysis.database.manager',
        'wareflow_analysis.common',
        'wareflow_analysis.common.output_handler',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Testing frameworks
        'pytest',
        'tests',
        'unittest',
        'mock',
        'coverage',
        'pytest_cov',

        # Development tools
        'ruff',
        'black',
        'mypy',
        'flake8',
        'pylint',
        'isort',

        # Unused standard library
        'email',
        'smtplib',
        'email.mime',
        'html',
        'html.parser',
        'http',
        'http.server',
        'urllib3',
        # Note: urllib and urllib.parse cannot be excluded - pathlib needs them
        'xml',
        'xmlrpc',

        # Unused databases
        'psycopg2',
        'pymysql',
        'cx_oracle',
        'redis',
        'pymongo',

        # Web frameworks
        'django',
        'flask',
        'fastapi',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove __pycache__ from datas
for src in list(a.datas):
    if '__pycache__' in src[0] or '.pyc' in src[0]:
        a.datas.remove(src)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Warehouse-GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed mode (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(SPEC_DIR, 'icon.ico'),
)
