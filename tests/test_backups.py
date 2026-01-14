import pytest

def test_backup_module_exists():
    import hiveden.backups

def test_backup_manager_exists():
    from hiveden.backups.manager import BackupManager

from unittest.mock import patch, MagicMock
import os

def test_create_postgres_backup_success(tmp_path):
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

def test_create_postgres_backup_failure(tmp_path):
    from hiveden.backups.manager import BackupManager
    manager = BackupManager()
    output_dir = tmp_path / "backups"
    output_dir.mkdir()
    
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = Exception("pg_dump failed")
        
        with pytest.raises(Exception):
            manager.create_postgres_backup("my_db", str(output_dir))
