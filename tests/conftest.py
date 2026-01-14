import pytest
from unittest.mock import MagicMock, patch
import sys

@pytest.fixture
def mock_docker_module():
    """
    Mocks hiveden.docker.containers in sys.modules and forces reload of hiveden.backups.manager.
    Returns the mock module.
    """
    mock_docker = MagicMock()
    modules_patch = {"hiveden.docker.containers": mock_docker}
    
    # Force reload of manager to pick up the mock
    if "hiveden.backups.manager" in sys.modules:
        del sys.modules["hiveden.backups.manager"]
        
    with patch.dict(sys.modules, modules_patch):
        yield mock_docker
