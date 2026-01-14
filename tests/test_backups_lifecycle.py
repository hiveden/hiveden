import pytest
from unittest.mock import patch, MagicMock

def test_app_backup_with_lifecycle_success(tmp_path, mock_docker_module):
    from hiveden.backups.manager import BackupManager
    
    manager = BackupManager()
    output_dir = tmp_path / "backups"
    output_dir.mkdir()
    source_dir = tmp_path / "app_data"
    source_dir.mkdir()
    
    # The DockerManager class used by BackupManager is our mock
    MockDockerManagerClass = mock_docker_module.DockerManager
    mock_docker_instance = MockDockerManagerClass.return_value
    
    with patch("tarfile.open"):
        with patch("hiveden.config.settings.config.backup_directory", str(output_dir)):
            manager.create_app_data_backup(
                source_dirs=[str(source_dir)],
                output_dir=str(output_dir),
                container_name="my_container"
            )
    
    # Verify container was stopped and started
    mock_docker_instance.stop_container.assert_called_with("my_container")
    mock_docker_instance.start_container.assert_called_with("my_container")

def test_app_backup_restarts_container_on_failure(tmp_path, mock_docker_module):
    from hiveden.backups.manager import BackupManager
    
    manager = BackupManager()
    output_dir = tmp_path / "backups"
    output_dir.mkdir()
    source_dir = tmp_path / "app_data"
    
    MockDockerManagerClass = mock_docker_module.DockerManager
    mock_docker_instance = MockDockerManagerClass.return_value
    
    # Simulate backup failure
    with patch("tarfile.open", side_effect=Exception("Backup failed")):
        with patch("hiveden.config.settings.config.backup_directory", str(output_dir)):
            with pytest.raises(Exception, match="Backup failed"):
                manager.create_app_data_backup(
                    source_dirs=[str(source_dir)],
                    output_dir=str(output_dir),
                    container_name="my_container"
                )
    
    # Verify container was stopped and THEN started despite failure
    mock_docker_instance.stop_container.assert_called_with("my_container")
    mock_docker_instance.start_container.assert_called_with("my_container")