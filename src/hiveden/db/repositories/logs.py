from typing import List, Dict, Any, Optional
from psycopg2.extras import Json
from hiveden.db.repositories.base import BaseRepository
from hiveden.api.dtos import LogEntry

class LogRepository(BaseRepository):
    def __init__(self, manager):
        super().__init__(manager, 'logs', LogEntry)

    def create_log(self, 
                   message: str, 
                   level: str = "info", 
                   actor: str = "system", 
                   action: Optional[str] = None, 
                   module: Optional[str] = None, 
                   metadata: Optional[Dict[str, Any]] = None):
        
        data = {
            "message": message,
            "level": level,
            "actor": actor,
            "action": action,
            "module": module,
            "metadata": Json(metadata) if metadata else Json({})
        }
        return self.create(**data)

    def get_logs(self, limit: int = 100, offset: int = 0, level: Optional[str] = None, module: Optional[str] = None) -> List[LogEntry]:
        conn = self.manager.get_connection()
        try:
            cursor = conn.cursor()
            
            query = "SELECT * FROM logs"
            conditions = []
            params = []
            
            if level:
                conditions.append("level = %s")
                params.append(level)
            
            if module:
                conditions.append("module = %s")
                params.append(module)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [self._to_model(dict(row)) for row in rows]
        finally:
            conn.close()