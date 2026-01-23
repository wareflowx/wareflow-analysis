# Excel-to-Sql Auto-Pilot: Headers Not Detected Correctly

## Problem Description

When using `wareflow import-data --init`, the generated configuration does not correctly detect Excel headers, resulting in all columns being mapped as `Unnamed: 0`, `Unnamed: 1`, etc., instead of using the actual column names present in row 1.

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

## Expected Behavior

Auto-Pilot should:
1. Detect headers on row 1
2. Map column names to target table fields
3. Generate clean `column_mappings` configuration

## Actual Behavior

Auto-Pilot generates:
```yaml
column_mappings:
  'Unnamed: 0':
    target: 'Unnamed: 0'
    type: text
  'Unnamed: 1':
    target: 'Unnamed: 1'
    type: text
```

## Root Cause

The bug is in excel-to-sql Auto-Pilot feature. It likely uses `pd.read_excel(file_path, header=0)` which doesn't correctly detect headers, or the detection algorithm fails with:
- French headers with accents ("Nom du produit")
- Special characters ("No. du produit")
- Multi-word headers ("Catégorie de produit #1")

## Proposed Solution

Implement our own header detection in `wareflow-analysis`:

1. **Detect header row** - Scan first 5 rows for known warehouse column names
2. **Map French to English** - Convert "No. du produit" → "no_produit"
3. **Generate explicit config** - Add `header: X` parameter to configuration

## Expected Column Mapping

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
  'Classe Produit':
    target: classe_produit
    type: text
  'Catégorie de produit #1':
    target: categorie_1
    type: text
  'État':
    target: etat
    type: text
```

## Implementation Approach

```python
def detect_header_row(file_path: Path) -> int:
    """Detect which row contains headers."""
    import pandas as pd

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

    return None
```

## Success Criteria

- [ ] Headers are correctly detected on row 1
- [ ] French column names are mapped to English equivalents
- [ ] Configuration is generated with explicit `header` parameter
- [ ] No more `Unnamed: X` columns in generated config
- [ ] Users can run `wareflow import-data --init` without manual config

## References

- excel-to-sql GitHub: https://github.com/Azure-Source/excel-to-sql
- Auto-Pilot documentation
- Related: PR #31 (ABC Classification)

**Last Updated:** 2025-01-23
**Estimation:** 2-3 days to implement fix
