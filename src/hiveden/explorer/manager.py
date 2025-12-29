import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from hiveden.db.session import get_db_manager
from hiveden.explorer.models import (
    ExplorerConfig,
    FilesystemLocation,
    ExplorerOperation,
    OperationStatus
)

class ExplorerManager:
    def __init__(self):
        self.db = get_db_manager()

    # --- Config ---

    def get_config(self) -> Dict[str, str]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM explorer_config")
            rows = cursor.fetchall()
            config = {}
            # Defaults
            config["show_hidden_files"] = "false"
            config["usb_mount_path"] = "/media"
            config["root_directory"] = "/"
            
            for row in rows:
                config[row[0]] = row[1]
            return config
        finally:
            conn.close()

    def update_config(self, key: str, value: str):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            # Check if exists
            cursor.execute("SELECT id FROM explorer_config WHERE key = %s", (key,))
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE explorer_config SET value = %s, updated_at = CURRENT_TIMESTAMP WHERE key = %s",
                    (value, key)
                )
            else:
                cursor.execute(
                    "INSERT INTO explorer_config (key, value) VALUES (%s, %s)",
                    (key, value)
                )
            conn.commit()
        finally:
            conn.close()

    # --- Locations (Bookmarks) ---

    def get_locations(self) -> List[FilesystemLocation]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, key, label, path, type, description, is_editable, created_at, updated_at FROM filesystem_locations ORDER BY label"
            )
            rows = cursor.fetchall()
            locations = []
            for row in rows:
                locations.append(FilesystemLocation(
                    id=row[0],
                    key=row[1],
                    label=row[2],
                    name=row[2],
                    path=row[3],
                    type=row[4],
                    description=row[5],
                    is_editable=row[6],
                    created_at=row[7] if isinstance(row[7], datetime) else datetime.fromisoformat(row[7]) if row[7] else None,
                    updated_at=row[8] if isinstance(row[8], datetime) else datetime.fromisoformat(row[8]) if row[8] else None
                ))
            return locations
        finally:
            conn.close()

    def create_location(self, label: str, path: str, type: str = "user_bookmark", description: Optional[str] = None) -> FilesystemLocation:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO filesystem_locations (label, path, type, description) VALUES (%s, %s, %s, %s) RETURNING id",
                (label, path, type, description)
            )
            location_id = cursor.fetchone()[0]
            conn.commit()
            
            return self.get_location(location_id)
        finally:
            conn.close()

    def update_location(self, location_id: int, label: Optional[str] = None, path: Optional[str] = None, description: Optional[str] = None) -> Optional[FilesystemLocation]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            updates = []
            params = []
            if label:
                updates.append("label = %s")
                params.append(label)
            if path:
                updates.append("path = %s")
                params.append(path)
            if description is not None:
                updates.append("description = %s")
                params.append(description)
            
            if not updates:
                return self.get_location(location_id)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            query = f"UPDATE filesystem_locations SET {', '.join(updates)} WHERE id = %s"
            params.append(location_id)
            
            cursor.execute(query, tuple(params))
            conn.commit()
            
            return self.get_location(location_id)
        finally:
            conn.close()

    def get_location(self, location_id: int) -> Optional[FilesystemLocation]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, key, label, path, type, description, is_editable, created_at, updated_at FROM filesystem_locations WHERE id = %s",
                (location_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return FilesystemLocation(
                id=row[0],
                key=row[1],
                label=row[2],
                name=row[2],
                path=row[3],
                type=row[4],
                description=row[5],
                is_editable=row[6],
                created_at=row[7] if isinstance(row[7], datetime) else datetime.fromisoformat(row[7]) if row[7] else None,
                updated_at=row[8] if isinstance(row[8], datetime) else datetime.fromisoformat(row[8]) if row[8] else None
            )
        finally:
            conn.close()

    def delete_location(self, location_id: int):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            # Prevent deleting system locations if needed, but schema allows it if not enforced here.
            # Assuming strictly UI driven 'is_editable' check happens there, but good to check here.
            cursor.execute("SELECT is_editable FROM filesystem_locations WHERE id = %s", (location_id,))
            row = cursor.fetchone()
            if row and not row[0]:
                raise ValueError("Cannot delete a system location")

            cursor.execute("DELETE FROM filesystem_locations WHERE id = %s", (location_id,))
            conn.commit()
        finally:
            conn.close()

    # --- Operations ---

    def create_operation(self, op_type: str, status: str = OperationStatus.PENDING) -> ExplorerOperation:
        op_id = str(uuid.uuid4())
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO explorer_operations (id, operation_type, status) VALUES (?, ?, ?)",
                (op_id, op_type, status)
            )
            conn.commit()
            return ExplorerOperation(id=op_id, operation_type=op_type, status=status)
        finally:
            conn.close()

    def update_operation(self, op: ExplorerOperation):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            
            def json_serial(obj):
                """JSON serializer for objects not serializable by default json code"""
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")

            source_paths_json = json.dumps(op.source_paths, default=json_serial) if isinstance(op.source_paths, list) else op.source_paths
            result_json = json.dumps(op.result, default=json_serial) if isinstance(op.result, (dict, list)) else op.result

            cursor.execute(
                """
                UPDATE explorer_operations 
                SET status = ?, progress = ?, total_items = ?, processed_items = ?,
                    source_paths = ?, destination_path = ?, error_message = ?, result = ?,
                    updated_at = CURRENT_TIMESTAMP, completed_at = ?
                WHERE id = ?
                """,
                (
                    op.status, op.progress, op.total_items, op.processed_items,
                    source_paths_json, op.destination_path, op.error_message, result_json,
                    op.completed_at, op.id
                )
            )
            conn.commit()
        finally:
            conn.close()

    def get_operation(self, op_id: str) -> Optional[ExplorerOperation]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, operation_type, status, progress, total_items, processed_items, source_paths, destination_path, error_message, result, created_at, updated_at, completed_at FROM explorer_operations WHERE id = ?",
                (op_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            return ExplorerOperation(
                id=row[0],
                operation_type=row[1],
                status=row[2],
                progress=row[3],
                total_items=row[4],
                processed_items=row[5],
                source_paths=row[6], # Should parse JSON if needed, keeping as string for now if compatible with model
                destination_path=row[7],
                error_message=row[8],
                result=row[9],
                created_at=row[10],
                updated_at=row[11],
                completed_at=row[12]
            )
        finally:
            conn.close()

    def get_operations(self, limit: int = 50, offset: int = 0) -> List[ExplorerOperation]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, operation_type, status, progress, total_items, processed_items, source_paths, destination_path, error_message, result, created_at, updated_at, completed_at FROM explorer_operations ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = cursor.fetchall()
            ops = []
            for row in rows:
                ops.append(ExplorerOperation(
                    id=row[0],
                    operation_type=row[1],
                    status=row[2],
                    progress=row[3],
                    total_items=row[4],
                    processed_items=row[5],
                    source_paths=row[6],
                    destination_path=row[7],
                    error_message=row[8],
                    result=row[9],
                    created_at=row[10],
                    updated_at=row[11],
                    completed_at=row[12]
                ))
            return ops
        finally:
            conn.close()

    def delete_operation(self, op_id: str):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM explorer_operations WHERE id = ?", (op_id,))
            conn.commit()
        finally:
            conn.close()
