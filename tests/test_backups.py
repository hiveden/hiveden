import pytest
from unittest.mock import patch, MagicMock

def test_backup_module_exists(mock_docker_module):
    import hiveden.backups

def test_backup_manager_exists(mock_docker_module):
    from hiveden.backups.manager import BackupManager

def test_create_postgres_backup_success(tmp_path, mock_docker_module):
    from hiveden.backups.manager import BackupManager
    
    manager = BackupManager()
    output_dir = tmp_path / "backups"
    output_dir.mkdir()
    
    # Mock datetime to get predictable filename if needed, but for now just check content
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        
        backup_file = manager.create_postgres_backup("my_db", str(output_dir))
        
        assert backup_file.startswith(str(output_dir))
        assert "my_db" in backup_file
        
        # Verify command
        # subprocess.run(['pg_dump', ...], check=True)
        # We expect it to write to a file, so maybe we pass a file handle or use -f
        # Let's verify arguments
        args = mock_run.call_args[0][0]
        assert "pg_dump" in args
        assert "my_db" in args

def test_create_postgres_backup_failure(tmp_path, mock_docker_module):
    from hiveden.backups.manager import BackupManager
    manager = BackupManager()
    output_dir = tmp_path / "backups"
    output_dir.mkdir()
    
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("pg_dump failed")
        
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
    with patch("tarfile.open") as mock_tar:
        mock_context = MagicMock()
        mock_tar.return_value.__enter__.return_value = mock_context
        
        backup_file = manager.create_app_data_backup([str(source_dir)], str(output_dir))
        
        assert backup_file.startswith(str(output_dir))
        assert backup_file.endswith(".tar.gz")
        
        # Verify tarfile was opened for writing
        # We need to ensure the arguments match what implementation will use
        # Just checking call count is often safer if exact path is dynamic
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
    
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        
        manager.restore_postgres_backup(str(backup_file), "my_db")
        
        # Verify psql command
        args = mock_run.call_args[0][0]
        assert "psql" in args
        assert "-f" in args
        assert str(backup_file) in args
        assert "my_db" in args

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
    
    # Test psql failure
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("psql failed")
        with pytest.raises(Exception):
            manager.restore_postgres_backup("file", "db")

    # Test tar failure
    with patch("tarfile.open") as mock_tar:
        mock_tar.side_effect = Exception("tar failed")
        with pytest.raises(Exception):
            manager.restore_app_data_backup("file", "dir")
