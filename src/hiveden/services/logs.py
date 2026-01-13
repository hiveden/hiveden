import traceback
from typing import Optional, Dict, Any
from hiveden.db.session import get_db_manager
from hiveden.db.repositories.logs import LogRepository

class LogService:
    def __init__(self):
        self.db_manager = get_db_manager()
        self.repo = LogRepository(self.db_manager)

    def info(self, actor: str, action: str, message: str, metadata: Optional[Dict[str, Any]] = None, module: Optional[str] = None):
        """Record an info log."""
        self._log("info", actor, action, message, metadata, module)

    def error(self, actor: str, action: str, message: str, error_details: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None, module: Optional[str] = None):
        """Record an error log."""
        if metadata is None:
            metadata = {}
        if error_details:
            metadata['error'] = error_details
            
        self._log("error", actor, action, message, metadata, module)

    def warning(self, actor: str, action: str, message: str, metadata: Optional[Dict[str, Any]] = None, module: Optional[str] = None):
        """Record a warning log."""
        self._log("warning", actor, action, message, metadata, module)

    def _log(self, level: str, actor: str, action: str, message: str, metadata: Optional[Dict[str, Any]], module: Optional[str]):
        try:
            self.repo.create_log(
                message=message,
                level=level,
                actor=actor,
                action=action,
                module=module,
                metadata=metadata
            )
        except Exception as e:
            # Fallback logging to stdout if DB fails
            traceback.print_exc()

            print(f"FAILED TO WRITE LOG TO DB: {e} - Message: {message}")
