import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from hiveden.db.session import get_db_manager
from hiveden.explorer.models import (
    ExplorerConfig,
    ExplorerBookmark,
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
            cursor.execute("SELECT id FROM explorer_config WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE explorer_config SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?",
                    (value, key)
                )
            else:
                cursor.execute(
                    "INSERT INTO explorer_config (key, value) VALUES (?, ?)",
                    (key, value)
                )
            conn.commit()
        finally:
            conn.close()

    # --- Bookmarks ---

    def get_bookmarks(self) -> List[ExplorerBookmark]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, path, created_at FROM explorer_bookmarks ORDER BY name")
            rows = cursor.fetchall()
            bookmarks = []
            for row in rows:
                bookmarks.append(ExplorerBookmark(
                    id=row[0],
                    name=row[1],
                    path=row[2],
                    created_at=row[3] if isinstance(row[3], datetime) else datetime.fromisoformat(row[3]) if row[3] else None
                ))
            return bookmarks
        finally:
            conn.close()

    def create_bookmark(self, name: str, path: str) -> ExplorerBookmark:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO explorer_bookmarks (name, path) VALUES (?, ?)",
                (name, path)
            )
            conn.commit()
            bookmark_id = cursor.lastrowid
            
            # Fetch back
            cursor.execute("SELECT created_at FROM explorer_bookmarks WHERE id = ?", (bookmark_id,))
            row = cursor.fetchone()
            created_at = row[0] if row else datetime.utcnow()
            
            return ExplorerBookmark(
                id=bookmark_id,
                name=name,
                path=path,
                created_at=created_at if isinstance(created_at, datetime) else datetime.fromisoformat(created_at) if created_at else None
            )
        finally:
            conn.close()

    def update_bookmark(self, bookmark_id: int, name: Optional[str], path: Optional[str]) -> Optional[ExplorerBookmark]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            updates = []
            params = []
            if name:
                updates.append("name = ?")
                params.append(name)
            if path:
                updates.append("path = ?")
                params.append(path)
            
            if not updates:
                return self.get_bookmark(bookmark_id)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            query = f"UPDATE explorer_bookmarks SET {', '.join(updates)} WHERE id = ?"
            params.append(bookmark_id)
            
            cursor.execute(query, tuple(params))
            conn.commit()
            
            return self.get_bookmark(bookmark_id)
        finally:
            conn.close()

    def get_bookmark(self, bookmark_id: int) -> Optional[ExplorerBookmark]:
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, path, created_at, updated_at FROM explorer_bookmarks WHERE id = ?", (bookmark_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return ExplorerBookmark(
                id=row[0],
                name=row[1],
                path=row[2],
                created_at=row[3],
                updated_at=row[4]
            )
        finally:
            conn.close()

    def delete_bookmark(self, bookmark_id: int):
        conn = self.db.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM explorer_bookmarks WHERE id = ?", (bookmark_id,))
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
            
            source_paths_json = json.dumps(op.source_paths) if isinstance(op.source_paths, list) else op.source_paths
            result_json = json.dumps(op.result) if isinstance(op.result, (dict, list)) else op.result

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
