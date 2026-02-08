import pytest
from unittest.mock import patch, MagicMock
import sys

# Mock yoyo
sys.modules["yoyo"] = MagicMock()

def test_backup_validation_failure(mock_docker_module):
    from hiveden.backups.manager import BackupManager
    
    # Mock config to have no backup directory
    with patch("hiveden.config.settings.config.backup_directory", None):
        manager = BackupManager()
        # Should raise ValueError because config is missing and no arg provided
        with pytest.raises(ValueError, match="Backup configuration missing"):
            manager.validate_config()

def test_backup_validation_success(tmp_path, mock_docker_module):
    from hiveden.backups.manager import BackupManager
    
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    
    with patch("hiveden.config.settings.config.backup_directory", str(backup_dir)):
        manager = BackupManager()
        # Should pass
        manager.validate_config()
        assert manager.get_backup_directory() == str(backup_dir)

def test_backup_creation_uses_config(tmp_path, mock_docker_module):
    from hiveden.backups.manager import BackupManager
    
    backup_dir = tmp_path / "default_backups"
    
    with patch("hiveden.config.settings.config.backup_directory", str(backup_dir)):
        with patch("hiveden.backups.manager.get_db_manager") as mock_get_db, \
             patch("hiveden.backups.manager.os.path.getsize", return_value=1024):
            
            manager = BackupManager()
            # Call without explicit output_dir
            manager.create_postgres_backup("mydb")
            
            # Verify it used the config directory (by checking the filepath passed to DB Manager)
            # The filepath logic is in BackupManager, which then passes it to db_manager.backup_database
            args = mock_get_db.return_value.backup_database.call_args
            assert str(backup_dir) in args[0][1]