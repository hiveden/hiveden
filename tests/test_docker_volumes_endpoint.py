from unittest.mock import MagicMock, patch
import sys

from docker.errors import APIError, NotFound
from fastapi import FastAPI
from fastapi.dependencies import utils as fastapi_dep_utils
from fastapi.testclient import TestClient

# Mock optional runtime dependencies imported transitively by router packages.
sys.modules["yoyo"] = MagicMock()
sys.modules["psutil"] = MagicMock()
sys.modules["apscheduler"] = MagicMock()
sys.modules["apscheduler.schedulers"] = MagicMock()
sys.modules["apscheduler.schedulers.asyncio"] = MagicMock()
sys.modules["apscheduler.triggers"] = MagicMock()
sys.modules["apscheduler.triggers.cron"] = MagicMock()
fastapi_dep_utils.ensure_multipart_is_installed = lambda: None

from hiveden.api.routers.docker.volumes import router


def _client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_list_volumes_endpoint_returns_data():
    client = _client()

    class FakeManager:
        def list_volumes(self, dangling=None):
            assert dangling is None
            return [
                {
                    "name": "pgdata",
                    "driver": "local",
                    "mountpoint": "/var/lib/docker/volumes/pgdata/_data",
                    "created_at": "2026-02-15T10:00:00Z",
                    "labels": None,
                    "scope": "local",
                    "options": None,
                }
            ]

    with patch("hiveden.api.routers.docker.volumes.DockerVolumeManager", lambda: FakeManager()):
        response = client.get("/volumes")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"][0]["name"] == "pgdata"


def test_list_volumes_endpoint_forwards_dangling_filter():
    client = _client()

    class FakeManager:
        def list_volumes(self, dangling=None):
            assert dangling is True
            return []

    with patch("hiveden.api.routers.docker.volumes.DockerVolumeManager", lambda: FakeManager()):
        response = client.get("/volumes?dangling=true")

    assert response.status_code == 200
    assert response.json()["data"] == []


def test_delete_volume_endpoint_success():
    client = _client()

    class FakeManager:
        def delete_volume(self, _volume_name):
            return None

    with patch("hiveden.api.routers.docker.volumes.DockerVolumeManager", lambda: FakeManager()):
        response = client.delete("/volumes/pgdata")

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_delete_volume_endpoint_returns_404():
    client = _client()

    class FakeManager:
        def delete_volume(self, _volume_name):
            raise NotFound("not found")

    with patch("hiveden.api.routers.docker.volumes.DockerVolumeManager", lambda: FakeManager()):
        response = client.delete("/volumes/missing")

    assert response.status_code == 404


def test_delete_volume_endpoint_returns_409_on_conflict():
    client = _client()

    class FakeManager:
        def delete_volume(self, _volume_name):
            fake_response = MagicMock(status_code=409)
            error = APIError("conflict", response=fake_response, explanation="volume is in use")
            raise error

    with patch("hiveden.api.routers.docker.volumes.DockerVolumeManager", lambda: FakeManager()):
        response = client.delete("/volumes/used")

    assert response.status_code == 409
    assert "in use" in response.json()["detail"]
