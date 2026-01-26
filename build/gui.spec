# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller configuration for Wareflow Analysis GUI.

This spec file creates a standalone Windows executable that includes
all dependencies and can run without Python installation.
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all data files from excel_to_sql
excel_to_sql_datas = collect_data_files('excel_to_sql')

a = Analysis(
    ['src/wareflow_analysis/gui/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Source code
        ('src/wareflow_analysis', 'wareflow_analysis'),

        # Templates
        ('src/wareflow_analysis/templates', 'wareflow_analysis/templates'),

        # Excel-to-SQL data files
        *excel_to_sql_datas,
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
        'excel_to_sql.core',
        'excel_to_sql.importer',
        'excel_to_sql.validator',
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
        'urllib',
        'urllib.parse',
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
    [],  # Exclude a.binaries and a.zipfiles for one-file build
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
    icon='build/icon.ico',
)
