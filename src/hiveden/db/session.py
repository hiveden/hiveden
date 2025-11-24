import os
from hiveden.db.manager import DatabaseManager

_db_manager = None

def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        db_url = os.getenv("HIVEDEN_DB_URL", "sqlite:///hiveden.db")
        _db_manager = DatabaseManager(db_url)
    return _db_manager
