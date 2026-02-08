import subprocess
import os
import tarfile
import glob
from datetime import datetime
from typing import List, Optional, Dict, Any
from hiveden.config.settings import config
from hiveden.docker.containers import DockerManager
from hiveden.services.logs import LogService
from hiveden.db.session import get_db_manager

class BackupManager:
    def __init__(self):
        self.log_service = LogService()
        self.log_module = "backups"

    def _get_db_config(self, key: str) -> Optional[str]:
        """Helper to fetch config from DB 'core' module."""
        try:
            from hiveden.db.session import get_db_manager
            from hiveden.db.repositories.core import ConfigRepository, ModuleRepository
            
            db_manager = get_db_manager()
            module_repo = ModuleRepository(db_manager)
            config_repo = ConfigRepository(db_manager)
            
            core_module = module_repo.get_by_short_name('core')
            if core_module:
                cfg = config_repo.get_by_module_and_key(core_module.id, key)
                if cfg:
                    return cfg['value']
        except Exception as e:
            # print(f"Error fetching DB config for {key}: {e}")
            pass
        return None

    def get_backup_directory(self, override_dir: Optional[str] = None) -> str:
        """Resolves the backup directory."""
        if override_dir:
            return override_dir
            
        # Try DB first
        db_dir = self._get_db_config('backups.directory')
        if db_dir:
            return db_dir
            
        # Fallback to settings
        path = config.backup_directory
        if not path:
            raise ValueError("Backup configuration missing: No backup directory set.")
        return path

    def validate_config(self, override_dir: Optional[str] = None) -> None:
        """Validates that the backup configuration is valid."""
        path = self.get_backup_directory(override_dir)
        if not path:
             raise ValueError("Backup configuration missing: No backup directory set.")

    def get_retention_count(self) -> int:
        """Returns the number of backups to keep."""
        # Try DB first
        val = self._get_db_config('backups.retention_count')
        if val:
            try:
                return int(val)
            except ValueError:
                pass
                
        # Default to settings or 5
        return getattr(config, 'backup_retention_count', 5)

    def list_backups(self, backup_type: Optional[str] = None, target: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lists available backups filtered by type and target.
        
        Args:
            backup_type: 'database' or 'application'
            target: The name of the database or application
            
        Returns:
            List of dicts with backup info.
        """
        backup_dir = self.get_backup_directory()
        if not os.path.exists(backup_dir):
            return []
            
        files = glob.glob(os.path.join(backup_dir, "*"))
        backups = []
        
        for f in files:
            if not os.path.isfile(f):
                continue
                
            name = os.path.basename(f)
            # Parse filename: name_timestamp.ext
            # Timestamps are YYYYMMDD_HHMMSS (15 chars)
            # Extension is .sql or .tar.gz
            
            b_type = "unknown"
            b_target = "unknown"
            timestamp = "unknown"
            
            if f.endswith(".sql"):
                b_type = "database"
                # Remove extension
                base = name[:-4]
                # Check for timestamp suffix
                parts = base.rsplit("_", 2) # split at last 2 underscores
                if len(parts) >= 3:
                    # name_YYYYMMDD_HHMMSS
                    ts_str = f"{parts[-2]}_{parts[-1]}"
                    try:
                        dt = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                        timestamp = dt.isoformat()
                    except ValueError:
                        timestamp = ts_str
                    b_target = "_".join(parts[:-2])
                else:
                    b_target = base
            elif f.endswith(".tar.gz"):
                b_type = "application"
                base = name[:-7]
                parts = base.rsplit("_", 2)
                if len(parts) >= 3:
                    ts_str = f"{parts[-2]}_{parts[-1]}"
                    try:
                        dt = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                        timestamp = dt.isoformat()
                    except ValueError:
                        timestamp = ts_str
                    b_target = "_".join(parts[:-2])
                else:
                    b_target = base
            
            if backup_type and b_type != backup_type:
                continue
            if target and b_target != target:
                continue
                
            backups.append({
                "path": f,
                "filename": name,
                "type": b_type,
                "target": b_target,
                "timestamp": timestamp,
                "size": os.path.getsize(f),
                "mtime": os.path.getmtime(f)
            })
            
        # Sort by mtime descending (newest first)
        backups.sort(key=lambda x: x["mtime"], reverse=True)
        return backups

    def enforce_retention_policy(self, target: str, backup_type: str, max_backups: int, actor: str = "system") -> None:
        """
        Deletes old backups for a specific target exceeding max_backups.
        """
        backups = self.list_backups(backup_type=backup_type, target=target)
        
        if len(backups) > max_backups:
            to_delete = backups[max_backups:]
            deleted_count = 0
            for b in to_delete:
                try:
                    os.remove(b["path"])
                    deleted_count += 1
                except OSError as e:
                    self.log_service.error(
                        actor=actor,
                        action="delete_backup",
                        message=f"Failed to delete old backup {b['path']}",
                        error_details=str(e),
                        module=self.log_module
                    )
            
            if deleted_count > 0:
                self.log_service.info(
                    actor=actor,
                    action="enforce_retention",
                    message=f"Deleted {deleted_count} old backups for {target} (policy: keep {max_backups})",
                    module=self.log_module
                )

    def create_postgres_backup(self, db_name: str, output_dir: Optional[str] = None, actor: str = "system") -> str:
        """Creates a backup of the specified PostgreSQL database."""
        self.log_service.info(
            actor=actor,
            action="backup_database",
            message=f"Starting PostgreSQL backup for database: {db_name}",
            module=self.log_module
        )

        filepath = None

        try:
            self.validate_config(output_dir)
            target_dir = self.get_backup_directory(output_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{db_name}_{timestamp}.sql"
            filepath = os.path.join(target_dir, filename)
            
            os.makedirs(target_dir, exist_ok=True)
        
            # Delegate to DatabaseManager
            db_manager = get_db_manager()
            db_manager.backup_database(db_name, filepath)
            
            self.log_service.info(
                actor=actor,
                action="backup_database",
                message=f"Backup completed successfully for {db_name}",
                metadata={"file": filepath, "size": os.path.getsize(filepath)},
                module=self.log_module
            )

            self.enforce_retention_policy(target=db_name, backup_type="database", max_backups=self.get_retention_count(), actor=actor)
            
            return filepath
        except Exception as e:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
            
            self.log_service.error(
                actor=actor,
                action="backup_database",
                message=f"PostgreSQL backup failed for {db_name}",
                error_details=str(e),
                module=self.log_module
            )
            raise

    def create_app_data_backup(self, source_dirs: List[str], output_dir: Optional[str] = None, container_name: Optional[str] = None, actor: str = "system") -> str:
        """Creates a compressed archive of the specified source directories."""
        self.log_service.info(
            actor=actor,
            action="backup_application",
            message=f"Starting application data backup. Source dirs: {source_dirs}",
            metadata={"container": container_name} if container_name else {},
            module=self.log_module
        )

        try:
            self.validate_config(output_dir)
            target_dir = self.get_backup_directory(output_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_name = "hiveden_app_data" # Default target name if not inferable? 
            # Ideally we should pass a 'name' for this backup job, but the current sig doesn't have it.
            # Using hiveden_app_data as per original code.
            
            filename = f"{target_name}_{timestamp}.tar.gz"
            filepath = os.path.join(target_dir, filename)
            
            os.makedirs(target_dir, exist_ok=True)
            
            docker_manager = None
            if container_name:
                docker_manager = DockerManager()
                try:
                    self.log_service.info(actor=actor, action="stop_container", message=f"Stopping container {container_name} for backup", module=self.log_module)
                    docker_manager.stop_container(container_name)
                except Exception as e:
                    self.log_service.warning(actor=actor, action="stop_container", message=f"Failed to stop container {container_name}", error_details=str(e), module=self.log_module)

            with tarfile.open(filepath, "w:gz") as tar:
                for source_dir in source_dirs:
                    if os.path.exists(source_dir):
                        tar.add(source_dir, arcname=os.path.basename(source_dir))
            
            self.log_service.info(
                actor=actor,
                action="backup_application",
                message=f"Application backup completed successfully.",
                metadata={"file": filepath, "size": os.path.getsize(filepath)},
                module=self.log_module
            )

            self.enforce_retention_policy(target=target_name, backup_type="application", max_backups=self.get_retention_count(), actor=actor)
            
            return filepath
        except Exception as e:
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
            self.log_service.error(
                actor=actor,
                action="backup_application",
                message="Application backup failed",
                error_details=str(e),
                module=self.log_module
            )
            raise Exception(f"App data backup failed: {e}") from e
        finally:
            if docker_manager and container_name:
                try:
                    self.log_service.info(actor=actor, action="start_container", message=f"Restarting container {container_name}", module=self.log_module)
                    docker_manager.start_container(container_name)
                except Exception as e:
                    self.log_service.error(actor=actor, action="start_container", message=f"Failed to restart container {container_name}", error_details=str(e), module=self.log_module)
                    print(f"Failed to restart container {container_name}: {e}")

    def restore_postgres_backup(self, backup_file: str, db_name: str, actor: str = "system") -> None:
        """Restores a PostgreSQL database from a backup file."""
        self.log_service.info(
            actor=actor,
            action="restore_database",
            message=f"Starting database restore for {db_name} from {backup_file}",
            module=self.log_module
        )

        if not os.path.exists(backup_file):
             self.log_service.error(actor=actor, action="restore_database", message=f"Backup file not found: {backup_file}", module=self.log_module)
             raise FileNotFoundError(f"Backup file not found: {backup_file}")

        try:
             # Delegate to DatabaseManager
             db_manager = get_db_manager()
             db_manager.restore_database(db_name, backup_file)

             self.log_service.info(
                actor=actor,
                action="restore_database",
                message=f"Database restore completed successfully for {db_name}",
                module=self.log_module
             )
        except Exception as e:
             self.log_service.error(
                actor=actor,
                action="restore_database",
                message=f"Database restore failed for {db_name}",
                error_details=str(e),
                module=self.log_module
             )
             raise
             
    def restore_app_data_backup(self, backup_file: str, dest_dir: str, actor: str = "system") -> None:
        """Restores application data from a backup archive."""
        self.log_service.info(
            actor=actor,
            action="restore_application",
            message=f"Starting application data restore from {backup_file} to {dest_dir}",
            module=self.log_module
        )

        if not os.path.exists(backup_file):
            self.log_service.error(actor=actor, action="restore_application", message=f"Backup file not found: {backup_file}", module=self.log_module)
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
        os.makedirs(dest_dir, exist_ok=True)
        
        try:
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(path=dest_dir)
            
            self.log_service.info(
                actor=actor,
                action="restore_application",
                message=f"Application restore completed successfully",
                module=self.log_module
            )
        except Exception as e:
            self.log_service.error(
                actor=actor,
                action="restore_application",
                message="Application restore failed",
                error_details=str(e),
                module=self.log_module
            )
            raise Exception(f"App data restore failed: {e}") from e

    def delete_backup(self, filename: str, actor: str = "system") -> None:
        """Deletes a specific backup file."""
        self.log_service.info(
            actor=actor,
            action="delete_backup",
            message=f"Request to delete backup: {filename}",
            module=self.log_module
        )

        backup_dir = self.get_backup_directory()
        filepath = os.path.join(backup_dir, filename)
        
        # Security check: prevent path traversal
        # resolve absolute paths
        abs_backup_dir = os.path.abspath(backup_dir)
        abs_filepath = os.path.abspath(filepath)
        
        if not abs_filepath.startswith(abs_backup_dir):
            msg = f"Security violation: Invalid backup filename {filename}"
            self.log_service.warning(
                actor=actor,
                action="delete_backup",
                message=msg,
                module=self.log_module
            )
            raise ValueError("Invalid filename")

        if not os.path.exists(filepath):
            msg = f"Backup file not found: {filename}"
            self.log_service.warning(
                actor=actor,
                action="delete_backup",
                message=msg,
                module=self.log_module
            )
            raise FileNotFoundError(msg)

        try:
            os.remove(filepath)
            self.log_service.info(
                actor=actor,
                action="delete_backup",
                message=f"Backup deleted successfully: {filename}",
                module=self.log_module
            )
        except Exception as e:
            self.log_service.error(
                actor=actor,
                action="delete_backup",
                message=f"Failed to delete backup {filename}",
                error_details=str(e),
                module=self.log_module
            )
            raise