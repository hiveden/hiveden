from typing import Optional, List, Dict, Any
import json
from psycopg2.extras import Json
from hiveden.db.repositories.base import BaseRepository
from hiveden.db.models.service import ManagedService, ServiceTemplate

class ServiceTemplateRepository(BaseRepository):
    def __init__(self, manager):
        super().__init__(manager, 'service_templates', model_class=ServiceTemplate)

    def get_by_slug(self, slug: str) -> Optional[ServiceTemplate]:
        conn = self.manager.get_connection()
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM service_templates WHERE slug = %s"
            cursor.execute(query, (slug,))
            row = cursor.fetchone()
            return self._to_model(dict(row)) if row else None
        finally:
            conn.close()

    def create(self, model: Optional[ServiceTemplate] = None, **kwargs) -> ServiceTemplate:
        # Override to handle JSON serialization if needed, though BaseRepository might need adjustment 
        # for JSON columns if it doesn't use psycopg2.extras.Json.
        # Ideally, we pass dicts directly and let psycopg2 handle it if configured, 
        # or wrapping in Json() adapter.
        
        data = kwargs
        if model:
            if isinstance(model, dict):
                model_data = model
            else:
                model_data = model.dict(exclude_unset=True)
            data.update(model_data)

        # Convert dict fields to Json objects for psycopg2
        if 'default_config' in data and isinstance(data['default_config'], dict):
            data['default_config'] = Json(data['default_config'])

        return super().create(**data)


class ManagedServiceRepository(BaseRepository):
    def __init__(self, manager):
        super().__init__(manager, 'managed_services', model_class=ManagedService)

    def get_by_identifier(self, identifier: str, type: str) -> Optional[ManagedService]:
        conn = self.manager.get_connection()
        try:
            cursor = conn.cursor()
            query = "SELECT * FROM managed_services WHERE identifier = %s AND type = %s AND deleted_at IS NULL"
            cursor.execute(query, (identifier, type))
            row = cursor.fetchone()
            return self._to_model(dict(row)) if row else None
        finally:
            conn.close()

    def create(self, model: Optional[ManagedService] = None, **kwargs) -> ManagedService:
        data = kwargs
        if model:
            if isinstance(model, dict):
                model_data = model
            else:
                model_data = model.dict(exclude_unset=True)
            data.update(model_data)

        if 'config' in data and isinstance(data['config'], dict):
            data['config'] = Json(data['config'])

        return super().create(**data)

    def update_config(self, id: int, config: Dict[str, Any]) -> Optional[ManagedService]:
        return self.update(id, config=Json(config))

    def soft_delete(self, id: int) -> bool:
        import datetime
        now = datetime.datetime.utcnow()
        return self.update(id, deleted_at=now) is not None
