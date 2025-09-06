"""
Database module compatibility layer
This module provides backward compatibility for imports
"""

# Import all database components from the core module
from app.core.database import (
    engine,
    SessionLocal,
    Base,
    get_db,
    create_tables,
    drop_tables
)

__all__ = [
    'engine',
    'SessionLocal', 
    'Base',
    'get_db',
    'create_tables',
    'drop_tables'
]