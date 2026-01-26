# Version Inconsistency Bug: `__init__.py` Hardcoded Version Mismatch

## 🐛 Bug Description

There is a critical version inconsistency in the `excel-to-sql` package where `__version__` is defined in two different places with different values, causing import-time confusion and breaking downstream packages.

## 🔍 Root Cause Analysis

### Current State (Broken)

**File: `excel_to_sql/__init__.py`**
```python
"""Excel to SQL - Import Excel files to SQL and export back."""

__version__ = "0.2.0"  # ← HARDCODED VERSION (WRONG!)
```

**File: `excel_to_sql/__version__.py`**
```python
"""Version information for excel-to-sql."""

__version__ = "0.4.0"  # ← CORRECT VERSION
```

### Version Mismatch Table

| Location | Version | Source |
|----------|---------|--------|
| `__init__.py` line 4 | `0.2.0` | Hardcoded ❌ |
| `__version__.py` | `0.4.0` | Dynamic ✅ |
| `pip show excel-to-sql` | `0.4.0` | Package metadata ✅ |
| `python -c "import excel_to_sql; print(excel_to_sql.__version__)"` | `0.2.0` | Runtime import ❌ |

### Why This Happens

When Python imports `excel_to_sql`, it executes `__init__.py` first, which defines `__version__ = "0.2.0"`. This **overwrites** the value from `__version__.py` if it's imported later, or simply never imports from `__version__.py` at all.

## 💥 Impact

### Downstream Impact: `wareflow-analysis`

The `wareflow-analysis` package depends on `excel-to-sql>=0.3.0` and has version-dependent logic:

```python
# src/wareflow_analysis/data_import/autopilot.py
try:
    from excel_to_sql.auto_pilot import PatternDetector
    from excel_to_sql import ExcelToSqlite
except ImportError:
    raise ImportError(
        "excel-to-sql>=0.3.0 is required. "
        "Install it with: pip install excel-to-sql>=0.3.0"
    )
```

When `wareflow-analysis` checks the version:
- **Expected**: `excel_to_sql.__version__ >= "0.3.0"`
- **Actual**: `excel_to_sql.__version__ == "0.2.0"`
- **Result**: Version check fails, misleading error message

### User Impact

1. **Confusing error messages**: Users see "excel-to-sql>=0.3.0 is required" even when 0.4.0 is installed
2. **Broken PyInstaller builds**: Compiled executables fail to load with version errors
3. **Development workflow issues**: Local development shows different version than CI/CD

## ✅ Proposed Solution

### Fix: Import `__version__` dynamically

**File: `excel_to_sql/__init__.py`**

```python
"""Excel to SQL - Import Excel files to SQL and export back."""

from excel_to_sql.__version__ import __version__  # ← Dynamic import

# OR keep both for backward compatibility
from excel_to_sql.__version__ import __version__ as __version__
__all__ = ["__version__"]
```

This ensures that:
1. `__version__` is sourced from a **single source of truth** (`__version__.py`)
2. Version updates only require changing one file
3. Import-time `__version__` matches package metadata

### Alternative Solution (if backward compatibility is critical)

```python
"""Excel to SQL - Import Excel files to SQL and export back."""

# Try to import from __version__.py, fallback to hardcoded
try:
    from excel_to_sql.__version__ import __version__
except ImportError:
    __version__ = "0.4.0"  # Fallback (keep in sync!)
```

## 🧪 Verification Steps

After applying the fix, verify with:

```bash
# 1. Install the package
pip install -e .

# 2. Check version matches
python -c "import excel_to_sql; print(f'Version: {excel_to_sql.__version__}')"
# Expected: Version: 0.4.0

# 3. Verify matches pip
pip show excel-to-sql | grep Version
# Expected: Version: 0.4.0

# 4. Test downstream package
cd ../wareflow-analysis
python -c "import excel_to_sql; assert excel_to_sql.__version__ >= '0.3.0', 'Version check failed'"
# Expected: No assertion error
```

## 📋 Acceptance Criteria

- [ ] `excel_to_sql.__version__` returns `"0.4.0"` when imported
- [ ] `python -c "import excel_to_sql; print(excel_to_sql.__version__)"` matches `pip show excel-to-sql`
- [ ] Downstream packages can successfully check `excel_to_sql.__version__ >= "0.3.0"`
- [ ] Version is defined in **only one place** (`__version__.py`)
- [ ] `__init__.py` imports from `__version__.py` (no hardcoded values)

## 🏷️ Labels

`bug` `critical` `version` `compatibility` `priority:high`

## 🔗 Related Issues

- wareflow-analysis Issue: Excel-to-sql version detection fails in PyInstaller builds
- wareflow-analysis PR: GUI and Windows executable implementation

## 📝 Additional Notes

- This is a **blocking issue** for releasing wareflow-analysis v0.7.x
- Affects all downstream packages that depend on excel-to-sql>=0.3.0
- Simple fix but **high impact** if not resolved
- Should be included in next excel-to-sql release (0.4.1 or 0.5.0)

## 🎯 Priority

**HIGH** - Blocking production releases of downstream packages and causing user-facing errors.
