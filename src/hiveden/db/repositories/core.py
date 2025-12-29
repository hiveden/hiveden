from typing import Optional, Dict, Any, Union
from hiveden.db.repositories.base import BaseRepository
from hiveden.db.models.module import Module

class ModuleRepository(BaseRepository):
    def __init__(self, manager):
        super().__init__(manager, 'modules', model_class=Module)

    def get_by_name(self, name: str) -> Optional[Module]:
        conn = self.manager.get_connection()
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM modules WHERE name = %s"
            cursor.execute(query, (name,))
            row = cursor.fetchone()
            return self._to_model(dict(row)) if row else None
        finally:
            conn.close()

    def get_by_short_name(self, short_name: str) -> Optional[Module]:
        conn = self.manager.get_connection()
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM modules WHERE short_name = %s"
            cursor.execute(query, (short_name,))
            row = cursor.fetchone()
            return self._to_model(dict(row)) if row else None
        finally:
            conn.close()

class ConfigRepository(BaseRepository):
    def __init__(self, manager):
        super().__init__(manager, 'configs')

    def get_by_module_and_key(self, module_id: int, key: str) -> Optional[Dict[str, Any]]:
        conn = self.manager.get_connection()
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM configs WHERE module_id = %s AND key = %s"
            cursor.execute(query, (module_id, key))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def set_value(self, module_short_name: str, key: str, value: str) -> Dict[str, Any]:
        """Set a configuration value, creating or updating as needed."""
        conn = self.manager.get_connection()
        try:
            cursor = conn.cursor()
            
            # 1. Get Module ID
            cursor.execute("SELECT id FROM modules WHERE short_name = %s", (module_short_name,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Module '{module_short_name}' not found")
            module_id = row['id'] # RealDictCursor usage

            # 2. Check existence
            cursor.execute(
                "SELECT id FROM configs WHERE module_id = %s AND key = %s", 
                (module_id, key)
            )
            existing = cursor.fetchone()
            
            if existing:
                query = """
                    UPDATE configs 
                    SET value = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s
                    RETURNING *
                """
                cursor.execute(query, (value, existing['id']))
            else:
                query = """
                    INSERT INTO configs (module_id, key, value) 
                    VALUES (%s, %s, %s)
                    RETURNING *
                """
                cursor.execute(query, (module_id, key, value))
            
            conn.commit()
            return dict(cursor.fetchone())
        finally:
            conn.close()

