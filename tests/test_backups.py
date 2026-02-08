import pytest
from unittest.mock import patch, MagicMock
import sys

# Mock yoyo to avoid dependency issues during import
sys.modules["yoyo"] = MagicMock()

def test_backup_module_exists(mock_docker_module):
    import hiveden.backups

def test_backup_manager_exists(mock_docker_module):
    from hiveden.backups.manager import BackupManager

def test_create_postgres_backup_success(tmp_path, mock_docker_module):
    from hiveden.backups.manager import BackupManager
    
    manager = BackupManager()
    output_dir = tmp_path / "backups"
    output_dir.mkdir()
    
    # Mock get_db_manager
    with patch("hiveden.backups.manager.get_db_manager") as mock_get_db, \
         patch("hiveden.backups.manager.os.path.getsize", return_value=1024):
        
        mock_db_instance = mock_get_db.return_value
        
        backup_file = manager.create_postgres_backup("my_db", str(output_dir))
        
        assert backup_file.startswith(str(output_dir))
        assert "my_db" in backup_file
        
        # Verify it delegated to DatabaseManager
        mock_db_instance.backup_database.assert_called_once()
        args = mock_db_instance.backup_database.call_args
        assert args[0][0] == "my_db"
        assert args[0][1] == backup_file

def test_create_postgres_backup_failure(tmp_path, mock_docker_module):
    from hiveden.backups.manager import BackupManager
    manager = BackupManager()
    output_dir = tmp_path / "backups"
    output_dir.mkdir()
    
    with patch("hiveden.backups.manager.get_db_manager") as mock_get_db:
        mock_db_instance = mock_get_db.return_value
        mock_db_instance.backup_database.side_effect = Exception("Backup failed")
        
        with pytest.raises(Exception):
            manager.create_postgres_backup("my_db", str(output_dir))

def test_create_app_data_backup_success(tmp_path, mock_docker_module):
    from hiveden.backups.manager import BackupManager
    import tarfile
    
    manager = BackupManager()
    output_dir = tmp_path / "backups"
    
    # Create dummy source data
    source_dir = tmp_path / "app_data"
    source_dir.mkdir()
    (source_dir / "config.yaml").write_text("config")
    
    # Mock tarfile.open
    with patch("tarfile.open") as mock_tar, \
         patch("hiveden.backups.manager.os.path.getsize", return_value=1024):
        mock_context = MagicMock()
        mock_tar.return_value.__enter__.return_value = mock_context
        
        backup_file = manager.create_app_data_backup([str(source_dir)], str(output_dir))
        
        assert backup_file.startswith(str(output_dir))
        assert backup_file.endswith(".tar.gz")
        
        # Verify tarfile was opened for writing
        assert mock_tar.call_count == 1
        
        # Verify files were added
        mock_context.add.assert_called()

def test_create_app_data_backup_failure(tmp_path, mock_docker_module):
    from hiveden.backups.manager import BackupManager
    manager = BackupManager()
    output_dir = tmp_path / "backups"
    source_dir = tmp_path / "app_data"
    
    with patch("tarfile.open") as mock_tar:
        mock_tar.side_effect = Exception("Tar failed")
        
        with pytest.raises(Exception):
            manager.create_app_data_backup([str(source_dir)], str(output_dir))

def test_restore_postgres_backup_success(tmp_path, mock_docker_module):
    from hiveden.backups.manager import BackupManager
    manager = BackupManager()
    backup_file = tmp_path / "backup.sql"
    backup_file.touch()
    
    with patch("hiveden.backups.manager.get_db_manager") as mock_get_db:
        mock_db_instance = mock_get_db.return_value
        
        manager.restore_postgres_backup(str(backup_file), "my_db")
        
        mock_db_instance.restore_database.assert_called_once_with("my_db", str(backup_file))

def test_restore_app_data_backup_success(tmp_path, mock_docker_module):
    from hiveden.backups.manager import BackupManager
    import tarfile
    
    manager = BackupManager()
    backup_file = tmp_path / "backup.tar.gz"
    backup_file.touch()
    dest_dir = tmp_path / "restore"
    
    with patch("tarfile.open") as mock_tar:
        mock_context = MagicMock()
        mock_tar.return_value.__enter__.return_value = mock_context
        
        manager.restore_app_data_backup(str(backup_file), str(dest_dir))
        
        mock_context.extractall.assert_called_with(path=str(dest_dir))

def test_restore_failure(tmp_path, mock_docker_module):
    from hiveden.backups.manager import BackupManager
    manager = BackupManager()
    
    # Test DB restore failure
    with patch("hiveden.backups.manager.get_db_manager") as mock_get_db:
        mock_db_instance = mock_get_db.return_value
        mock_db_instance.restore_database.side_effect = Exception("Restore failed")
        
        with pytest.raises(Exception):
            manager.restore_postgres_backup("file", "db")

    # Test tar failure
    with patch("tarfile.open") as mock_tar:
        mock_tar.side_effect = Exception("tar failed")
        with pytest.raises(Exception):
            manager.restore_app_data_backup("file", "dir")

def test_delete_backup_success(tmp_path, mock_docker_module):
    from hiveden.backups.manager import BackupManager
    manager = BackupManager()
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    
    file = backup_dir / "test.sql"
    file.touch()
    
    with patch("hiveden.config.settings.config.backup_directory", str(backup_dir)):
        manager.delete_backup("test.sql")
        assert not file.exists()

def test_delete_backup_not_found(tmp_path, mock_docker_module):
    from hiveden.backups.manager import BackupManager
    manager = BackupManager()
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    
    with patch("hiveden.config.settings.config.backup_directory", str(backup_dir)):
        with pytest.raises(FileNotFoundError):
            manager.delete_backup("nonexistent.sql")

def test_delete_backup_security(tmp_path, mock_docker_module):
    from hiveden.backups.manager import BackupManager
    manager = BackupManager()
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    
    with patch("hiveden.config.settings.config.backup_directory", str(backup_dir)):
        with pytest.raises(ValueError):
            manager.delete_backup("../../../etc/passwd")
