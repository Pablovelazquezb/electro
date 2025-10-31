# backend/utils/sanitizers.py
import re
from typing import Set

def sanitize_table_name(name: str) -> str:
    """
    Converts client name to a valid SQL table name
    Example: "Client 1" -> "client_1"
    """
    table = name.lower()
    table = re.sub(r'[^a-z0-9_]', '_', table)
    table = re.sub(r'_+', '_', table)
    table = table.strip('_')
    
    if table and table[0].isdigit():
        table = 'data_' + table
    
    return table or 'data_client'


def sanitize_column_name(name: str) -> str:
    """
    Converts column names to valid SQL format
    Example: "Andrea (Delta)" -> "andrea_delta"
    Example: "Inv 6-8+" -> "inv_6_8_plus"
    """
    column = name.lower()
    
    # Replace + with _plus before removing special chars
    column = column.replace('+', '_plus')
    
    # Replace - with underscore (before general replacement)
    column = column.replace('-', '_')
    
    # Remove other special characters
    column = re.sub(r'[^a-z0-9_]', '_', column)
    column = re.sub(r'_+', '_', column)
    column = column.strip('_')
    
    return column


def make_columns_unique(columns: list) -> list:
    """
    Ensure all column names are unique by appending numbers to duplicates
    """
    seen: Set[str] = set()
    unique_columns = []
    
    for col in columns:
        sanitized = sanitize_column_name(col)
        original = sanitized
        counter = 2
        
        # If duplicate, append number
        while sanitized in seen:
            sanitized = f"{original}_{counter}"
            counter += 1
        
        seen.add(sanitized)
        unique_columns.append(sanitized)
    
    return unique_columns
