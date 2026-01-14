import subprocess
import os
from datetime import datetime

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