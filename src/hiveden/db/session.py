import os
from hiveden.db.manager import DatabaseManager

_db_manager = None

def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        db_url = os.getenv("HIVEDEN_DB_URL")
        if not db_url:
            # Fallback to constructing URL from individual vars
            db_host = os.getenv("DB_HOST", "localhost")
            db_user = os.getenv("DB_USER", "postgres")
            db_pass = os.getenv("DB_PASS", "postgres")
            db_name = os.getenv("DB_NAME", "hiveden")
            db_url = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
            
        _db_manager = DatabaseManager(db_url)
    return _db_manager
