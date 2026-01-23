"""Header Detection Module for wareflow-analysis.

This module provides automatic detection of header rows in Excel files,
especially for files with French headers or special characters.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


class HeaderDetector:
    """
    Automatically detects the header row in Excel files.

    This class analyzes pandas DataFrames and identifies which row contains
    the actual column headers, particularly for French WMS (Warehouse Management System)
    exports with special characters, accents, and multi-word column names.
    """

    # Known warehouse column names (with French variations)
    HEADER_KEYWORDS = {
        "product": ["product", "produit", "prod", "warehouse"],
        "no": ["no", "no.", "numéro", "numero", "number", "id", "code"],
        "name": ["nom", "name", "nom du", "description"],
        "class": ["classe", "class", "category", "catégorie", "type"],
        "state": ["état", "etat", "state", "status", "configuration"],
        "ean": ["ean", "upc", "sku", "barcode"],
        "category": ["catégorie", "categorie", "category"],
        "date": ["date", "date_heure", "datetime"],
        "quantity": ["quantité", "quantite", "quantity", "qty"],
        "movement": ["mouvement", "movement", "type"],
        "order": ["commande", "order", "client"],
    }

    def detect_header_row(
        self,
        file_path: Path,
        sheet_name: str | int = 0,
        max_scan_rows: int = 10,
        min_matches: int = 2,
    ) -> int:
        """
        Detect which row contains the column headers.

        Scans the first N rows of an Excel file and identifies which row
        contains header-like content based on known column name patterns.

        Args:
            file_path: Path to the Excel file
            sheet_name: Sheet name or index to analyze (default: 0)
            max_scan_rows: Maximum number of rows to scan (default: 10)
            min_matches: Minimum keyword matches to consider a row as header (default: 2)

        Returns:
            Row index (0-based) that contains headers, or 0 if detection fails
        """
        try:
            # Read first N rows without headers to analyze content
            df = pd.read_excel(
                file_path, sheet_name=sheet_name, header=None, nrows=max_scan_rows, engine="openpyxl"
            )
        except Exception:
            # If reading fails, default to header=0
            return 0

        # Check each row for header-like content
        for row_idx in range(min(max_scan_rows, len(df))):
            if self._is_header_row(df, row_idx, min_matches):
                return row_idx

        # Default to header=0 if no clear header found
        return 0

    def _is_header_row(self, df: pd.DataFrame, row_idx: int, min_matches: int) -> bool:
        """
        Check if a specific row looks like a header row.

        Args:
            df: DataFrame to analyze
            row_idx: Row index to check
            min_matches: Minimum keyword matches required

        Returns:
            True if the row appears to be a header row
        """
        # Get row values and convert to lowercase strings
        try:
            row_values = df.iloc[row_idx].astype(str).str.lower().str.strip()
        except Exception:
            return False

        # Join all values in the row into a single text string
        row_text = " ".join(row_values)

        # Count how many header keywords appear in this row
        matches = 0

        for category, keywords in self.HEADER_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in row_text:
                    matches += 1
                    break  # Count each category only once per row

        # Row is considered a header if it matches enough categories
        return matches >= min_matches

    def normalize_column_name(self, col_name: str) -> str:
        """
        Normalize a column name to a database-friendly format.

        Converts French headers with special characters to English-style
        snake_case column names suitable for database tables.

        Args:
            col_name: Original column name (potentially with French accents/special chars)

        Returns:
            Normalized column name in snake_case

        Example:
            >>> detector = HeaderDetector()
            >>> detector.normalize_column_name("No. du produit")
            'no_produit'
            >>> detector.normalize_column_name("Catégorie de produit #1")
            'categorie_produit_1'
        """
        import re

        # Convert to lowercase and strip whitespace
        normalized = str(col_name).lower().strip()

        # Replace common French characters
        french_chars = {
            "à": "a",
            "â": "a",
            "ä": "a",
            "é": "e",
            "è": "e",
            "ê": "e",
            "ë": "e",
            "î": "i",
            "ï": "i",
            "ô": "o",
            "ö": "o",
            "ù": "u",
            "û": "u",
            "ü": "u",
            "ç": "c",
        }

        for french, english in french_chars.items():
            normalized = normalized.replace(french, english)

        # Replace special characters and punctuation with underscore
        normalized = re.sub(r"[^\w\s]+", " ", normalized)

        # Replace multiple spaces with single underscore
        normalized = re.sub(r"\s+", "_", normalized)

        # Remove leading/trailing underscores
        normalized = normalized.strip("_")

        # Remove common French words/stop words
        stop_words = ["le", "la", "les", "de", "du", "des", "et", "ou", "en", "à", "au", "aux"]
        parts = normalized.split("_")
        filtered_parts = [p for p in parts if p not in stop_words and len(p) > 0]

        if not filtered_parts:
            # If all words were filtered, return a simplified version
            return col_name.lower().replace(" ", "_").replace(".", "")

        return "_".join(filtered_parts)

    def read_excel_with_header_detection(
        self, file_path: Path, sheet_name: str | int = 0, normalize_columns: bool = False
    ) -> pd.DataFrame:
        """
        Read an Excel file with automatic header detection.

        Convenience method that combines header detection with DataFrame reading.

        Args:
            file_path: Path to the Excel file
            sheet_name: Sheet name or index to read (default: 0)
            normalize_columns: If True, normalize French column names to English (default: False)

        Returns:
            DataFrame with proper headers set
        """
        # Detect header row
        header_row = self.detect_header_row(file_path, sheet_name)

        # Read Excel with detected header
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row, engine="openpyxl")

        # Normalize column names if requested
        if normalize_columns:
            new_columns = {col: self.normalize_column_name(col) for col in df.columns}
            df = df.rename(columns=new_columns)

        return df
