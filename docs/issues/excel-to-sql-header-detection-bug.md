# Issue: Excel-to-Sql Auto-Pilot Not Detecting Headers Correctly

**Status:** Open
**Priority:** HIGH
**Type:** Bug / Enhancement
**Component:** Data Import
**Related:** excel-to-sql Auto-Pilot integration

---

## Problem Description

When using `wareflow import-data --init`, the generated configuration does not correctly detect Excel headers, resulting in:
- All columns being mapped as `Unnamed: 0`, `Unnamed: 1`, etc.
- Headers being completely ignored
- User having to manually configure column mappings

### Expected Behavior

Auto-Pilot should:
1. Detect headers on row 1 (when they exist)
2. Map column names to target table fields
3. Generate clean `column_mappings` configuration

### Actual Behavior

Auto-Pilot generates:
```yaml
column_mappings:
  'Unnamed: 0':
    target: 'Unnamed: 0'
    type: text
  'Unnamed: 1':
    target: 'Unnamed: 1'
    type: text
  # ... all columns unnamed
```

---

## Sample Data

### Excel File: produits.xlsx

**Row 1 (Headers):**
```
"No. du produit","Nom du produit","Description","Classe Produit","Catégorie de produit #1","Catégorie de produit #2","Catégorie de produit #3","État","Configuration","EAN Alternatif"
```

**Row 2-3 (Data):**
```
"2725","SHOEI MENTONNIERE UNIV","SHOEI MENTONNIERE UNIV","FG","Pilote","CASQUES","DIVERS ACCESS.CASQUES-LUN","Actif","Configuration",""
"7353","SHOEI CACHENEZ XR1000GMSUP","SHOEI CACHENEZ XR1000GMSUP","FG","Pilote","CASQUES","DIVERS ACCESS.CASQUES-LUN","Actif","Configuration",""
```

### Expected Column Mapping

```yaml
column_mappings:
  'No. du produit':
    target: no_produit
    type: text
  'Nom du produit':
    target: nom_produit
    type: text
  'Description':
    target: description
    type: text
  # ... etc
```

---

## Root Cause Analysis

### Issue Location

The bug is in **excel-to-sql Auto-Pilot** feature.

### Technical Details

Auto-Pilot likely uses:
```python
pd.read_excel(file_path, header=0)  # Incorrect for files with headers on row 1
```

Or the header detection algorithm fails to recognize:
- French headers with accents ("Nom du produit")
- Special characters ("No. du produit")
- Multi-word headers ("Catégorie de produit #1")

### Why This is a Bug

1. **Headers are present** in the Excel file (Row 1)
2. **Headers are valid** and clearly identifiable
3. **Pandas can read them correctly** when using `header=0` or `header=1`
4. **Auto-Pilot should detect** them but doesn't

---

## Impact

### User Impact

- Users cannot use `wareflow import-data --init` as intended
- Manual configuration is required for every Excel file
- Tool's main value proposition (zero-config import) is broken

### Severity

**HIGH** - Blocks the primary workflow for the application:
- Users expect automatic configuration
- Current behavior requires manual intervention
- Defeats the purpose of Auto-Pilot integration

---

## Proposed Solution

### Approach: Implement Our Own Header Detection

Since excel-to-sql Auto-Pilot is not detecting headers correctly, we should implement our own detection in `wareflow-analysis`.

### Implementation Plan

#### 1. Add Header Detection to `config_refiner.py`

```python
def detect_header_row(file_path: Path) -> int:
    """
    Detect which row contains headers.

    Reads the file and identifies which row contains column headers
    by looking for expected warehouse column names.

    Returns:
        int: Row number containing headers (0-indexed), or None if no headers found
    """
    import pandas as pd

    # Read first few rows
    df = pd.read_excel(file_path, nrows=5, header=None)

    # Known warehouse column names (with French variations)
    header_keywords = [
        "no_produit", "no. du produit", "produit",
        "nom_produit", "nom du produit", "description",
        "classe", "catégorie", "état", "configuration"
    ]

    # Check each row for header-like content
    for row_idx in range(min(5, len(df))):
        row_values = df.iloc[row_idx].astype(str).str.lower().str.strip()
        row_text = ' '.join(row_values)

        # Count matching keywords
        matches = sum(1 for keyword in header_keywords if keyword.lower() in row_text)

        # If row contains multiple header keywords, it's likely the header row
        if matches >= 3:
            return row_idx

    # Default: no headers detected
    return None
```

#### 2. Update Configuration Generation

```python
def generate_config_with_headers(file_path: Path, project_dir: Path):
    """Generate configuration with automatic header detection."""
    header_row = detect_header_row(file_path)

    if header_row is not None:
        header_param = header_row + 1  # pandas is 0-indexed, configs often 1-indexed
    else:
        header_param = 0  # No headers found

    # Generate excel-to-sql config with explicit header parameter
    config = {
        "imports": {
            "produits": {
                "source": "data/produits.xlsx",
                "table": "produits",
                "header": header_param,  # ← Explicit header row
                "primary_key": "no_produit"
            }
        }
    }

    # Additional logic to map French column names to SQL names
    column_mapping = map_french_to_english_columns(file_path, header_row)
    config["imports"]["produits"]["columns"] = column_mapping

    return config
```

#### 3. Column Name Mapping

```python
FRENCH_TO_ENGLISH_MAP = {
    "No. du produit": "no_produit",
    "Nom du produit": "nom_produit",
    "Description": "description",
    "Classe Produit": "classe_produit",
    "Catégorie de produit #1": "categorie_1",
    "Catégorie de produit #2": "categorie_2",
    "Catégorie de produit #3": "categorie_3",
    "État": "etat",
    "Configuration": "configuration",
    "EAN Alternatif": "ean_alternatif",
}

def map_french_to_english_columns(file_path: Path, header_row: int) -> dict:
    """Map French column names to SQL-friendly English names."""
    import pandas as pd

    # Read the header row
    df = pd.read_excel(file_path, header=header_row)
    columns = df.columns.tolist()

    # Map each French name to English
    column_mappings = {}
    for col in columns:
        if col in FRENCH_TO_ENGLISH_MAP:
            target_name = FRENCH_TO_ENGLISH_MAP[col]
        else:
            # Convert to snake_case if needed
            target_name = col.lower().replace(" ", "_").replace(".", "")

        column_mappings[col] = {
            "target": target_name,
            "type": infer_column_type(col)
        }

    return column_mappings
```

---

## Alternative Approaches

### Option A: Report Bug to excel-to-sql

**Pros:**
- Fixes the issue at source
- All users benefit from the fix

**Cons:**
- Depends on external project timeline
- May not be prioritized
- Wait time uncertain

### Option B: Implement Workaround in wareflow-analysis (RECOMMENDED)

**Pros:**
- Immediate fix for our users
- Control over solution
- Can customize for our specific needs

**Cons:**
- Maintenance overhead
- Duplicates functionality (in theory)

---

## Workaround for Users (Current)

Until this is fixed, users must manually configure:

```yaml
imports:
  produits:
    source: data/produits.xlsx
    table: produits
    primary_key: no_produit
    header: 1
    columns:
      "No. du produit":
        target: no_produit
      "Nom du produit":
        target: nom_produit
      # ... etc
```

---

## Testing Requirements

### Test Cases

1. **French headers with accents** - Should be detected correctly
2. **Multi-word headers** - Should be mapped to snake_case
3. **Special characters** - Should handle "No. du produit", "Catégorie #1"
4. **Mixed naming** - Handle both French and English column names
5. **No headers** - Gracefully handle files without headers

### Test Data

Create test Excel files with:
- Standard French headers
- Edge cases (accents, special chars, multi-word)
- Files without headers (should default to Unnamed)

---

## Success Criteria

- [ ] Headers are correctly detected on row 1
- [ ] French column names are mapped to English equivalents
- [ ] Configuration is generated with explicit `header` parameter
- [ ] No more `Unnamed: X` columns in generated config
- [ ] Users can run `wareflow import-data --init` without manual config

---

## References

- excel-to-sql GitHub: https://github.com/Azure-Source/excel-to-sql
- excel-to-sql documentation: Auto-Pilot feature
- Related Issue: #10 (CORE-002 - Implement analyze command)
- Related PR: #31 (ABC Classification)

---

**Last Updated:** 2025-01-23
**Priority:** HIGH
**Complexity:** Medium
**Estimation:** 2-3 days to implement fix
