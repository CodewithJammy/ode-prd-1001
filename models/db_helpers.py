# models/db_helpers.py

def row_to_dict(cursor, row):
    """Convert a pyodbc row tuple into a dictionary keyed by column names."""
    if not row:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))
