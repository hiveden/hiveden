import subprocess
import os
import tarfile
from datetime import datetime
from typing import List

class BackupManager:
    def create_postgres_backup(self, db_name: str, output_dir: str) -> str:
        """
        Creates a backup of the specified PostgreSQL database.
        
        Args:
            db_name: The name of the database to backup.
            output_dir: The directory where the backup file will be saved.
            
        Returns:
            The path to the created backup file.
            
        Raises:
            Exception: If pg_dump fails.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{db_name}_{timestamp}.sql"
        filepath = os.path.join(output_dir, filename)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            subprocess.run(
                ["pg_dump", "-f", filepath, db_name],
                check=True,
                capture_output=True,
                text=True
            )
            return filepath
        except subprocess.CalledProcessError as e:
            # Clean up partial file if exists
            if os.path.exists(filepath):
                os.remove(filepath)
            raise Exception(f"Backup failed: {e.stderr}") from e

    def create_app_data_backup(self, source_dirs: List[str], output_dir: str) -> str:
        """
        Creates a compressed archive of the specified source directories.
        
        Args:
            source_dirs: List of directories to include in the backup.
            output_dir: The directory where the backup file will be saved.
            
        Returns:
            The path to the created backup file.
            
        Raises:
            Exception: If archiving fails.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hiveden_app_data_{timestamp}.tar.gz"
        filepath = os.path.join(output_dir, filename)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            with tarfile.open(filepath, "w:gz") as tar:
                for source_dir in source_dirs:
                    if os.path.exists(source_dir):
                        tar.add(source_dir, arcname=os.path.basename(source_dir))
            return filepath
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise Exception(f"App data backup failed: {e}") from e

    def restore_postgres_backup(self, backup_file: str, db_name: str) -> None:
        """
        Restores a PostgreSQL database from a backup file.
        
        Args:
            backup_file: Path to the backup file (.sql).
            db_name: Name of the database to restore to.
            
        Raises:
            FileNotFoundError: If backup file doesn't exist.
            Exception: If restore fails.
        """
        if not os.path.exists(backup_file):
             raise FileNotFoundError(f"Backup file not found: {backup_file}")

        try:
             subprocess.run(
                ["psql", "-f", backup_file, db_name],
                check=True,
                capture_output=True,
                text=True
             )
        except subprocess.CalledProcessError as e:
             raise Exception(f"Restore failed: {e.stderr}") from e

    def restore_app_data_backup(self, backup_file: str, dest_dir: str) -> None:
        """
        Restores application data from a backup archive to the destination directory.
        
        Args:
            backup_file: Path to the backup archive.
            dest_dir: Directory to extract to.
            
        Raises:
            FileNotFoundError: If backup file doesn't exist.
            Exception: If restore fails.
        """
        if not os.path.exists(backup_file):
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
        os.makedirs(dest_dir, exist_ok=True)
        
        try:
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(path=dest_dir)
        except Exception as e:
            raise Exception(f"App data restore failed: {e}") from e