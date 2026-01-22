"""Schema parser for extracting validation rules from schema.sql."""

from pathlib import Path
from typing import Any, Dict
import re


class TableSchema:
    """Represents schema requirements for a table."""

    def __init__(
        self,
        name: str,
        columns: list[str],
        primary_key: str | None,
        column_types: Dict[str, str],
        foreign_keys: list[Dict[str, str]],
    ):
        self.name = name
        self.columns = columns
        self.primary_key = primary_key
        self.column_types = column_types
        self.foreign_keys = foreign_keys

    def get_required_columns(self) -> list[str]:
        """Get list of required columns (currently all columns)."""
        return self.columns

    def __repr__(self) -> str:
        return f"TableSchema(name={self.name}, columns={len(self.columns)}, pk={self.primary_key})"


class SchemaParser:
    """Parse schema.sql to extract validation rules."""

    # Regex patterns for SQL parsing
    CREATE_TABLE_PATTERN = re.compile(
        r"CREATE\s+TABLE\s+(\w+)\s*\((.*?)\);", re.IGNORECASE | re.DOTALL
    )
    COLUMN_PATTERN = re.compile(r"(\w+)\s+(INTEGER|TEXT|REAL|DATETIME|NUMERIC)", re.IGNORECASE)
    # Pattern 1: PRIMARY KEY (column_name) at end of table definition
    PRIMARY_KEY_PATTERN = re.compile(r"PRIMARY\s+KEY\s*\((\w+)\)", re.IGNORECASE)
    # Pattern 2: inline PRIMARY KEY with column definition
    PRIMARY_KEY_INLINE_PATTERN = re.compile(r"(\w+)\s+(?:INTEGER|TEXT|REAL|DATETIME)\s+PRIMARY\s+KEY", re.IGNORECASE)
    FOREIGN_KEY_PATTERN = re.compile(
        r"FOREIGN\s+KEY\s*\((\w+)\)\s+REFERENCES\s+(\w+)\((\w+)\)", re.IGNORECASE
    )

    def parse(self, schema_path: Path) -> Dict[str, TableSchema]:
        """Parse schema.sql file and extract table definitions.

        Args:
            schema_path: Path to schema.sql file

        Returns:
            Dictionary mapping table names to TableSchema objects

        Raises:
            FileNotFoundError: If schema file doesn't exist
            ValueError: If schema file is invalid
        """
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        schema_sql = schema_path.read_text()

        # Extract all CREATE TABLE statements
        tables = {}

        for match in self.CREATE_TABLE_PATTERN.finditer(schema_sql):
            table_name = match.group(1)
            columns_def = match.group(2)

            # Parse columns
            columns = []
            column_types = {}

            for col_match in self.COLUMN_PATTERN.finditer(columns_def):
                col_name = col_match.group(1)
                col_type = col_match.group(2).upper()
                columns.append(col_name)
                column_types[col_name] = col_type

            # Find primary key
            pk_match = self.PRIMARY_KEY_PATTERN.search(columns_def)

            # If not found, try inline pattern (column_name TYPE PRIMARY KEY)
            if not pk_match:
                # Check each column definition for inline PRIMARY KEY
                for col_match in self.COLUMN_PATTERN.finditer(columns_def):
                    col_def = columns_def[col_match.start():col_match.end()]
                    if "PRIMARY KEY" in col_def.upper():
                        pk_match = col_match
                        break

            primary_key = pk_match.group(1) if pk_match else None
            if pk_match and isinstance(pk_match, str):
                primary_key = pk_match
            elif pk_match:
                # It's a Match object, get group(1)
                primary_key = pk_match.group(1) if hasattr(pk_match, 'group') else None

            # Find foreign keys
            foreign_keys = []
            for fk_match in self.FOREIGN_KEY_PATTERN.finditer(columns_def):
                foreign_keys.append(
                    {
                        "column": fk_match.group(1),
                        "ref_table": fk_match.group(2),
                        "ref_column": fk_match.group(3),
                    }
                )

            tables[table_name] = TableSchema(
                name=table_name,
                columns=columns,
                primary_key=primary_key,
                column_types=column_types,
                foreign_keys=foreign_keys,
            )

        if not tables:
            raise ValueError("No tables found in schema file")

        return tables

    def get_table_schema(self, schema_path: Path, table_name: str) -> TableSchema | None:
        """Get schema for a specific table.

        Args:
            schema_path: Path to schema.sql
            table_name: Name of table

        Returns:
            TableSchema or None if table not found
        """
        tables = self.parse(schema_path)
        return tables.get(table_name)
