import asyncio
from unittest.mock import MagicMock, patch
import sys

import pytest

pytest.importorskip("fastapi")

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

from hiveden.api.routers.storage import router


def _client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@patch("hiveden.storage.devices.get_mounts", return_value=[])
@patch("hiveden.storage.devices.get_raw_disks")
def test_list_devices_smoke_includes_loop_excludes_ram(
    mock_get_raw,
    _mock_get_mounts,
):
    mock_get_raw.return_value = [
        {
            "name": "sdb",
            "path": "/dev/sdb",
            "size": "4000787030016",
            "model": "WD Red",
            "serial": "WD-WCC4E1234567",
            "rota": True,
            "type": "disk",
            "fstype": None,
            "children": [],
        },
        {
            "name": "loop0",
            "path": "/dev/loop0",
            "size": "1073741824",
            "model": None,
            "serial": None,
            "rota": False,
            "type": "loop",
            "fstype": None,
            "children": [],
        },
        {
            "name": "ram0",
            "path": "/dev/ram0",
            "size": "67108864",
            "model": None,
            "serial": None,
            "rota": False,
            "type": "disk",
            "fstype": None,
            "children": [],
        },
    ]

    response = _client().get("/storage/devices")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"

    names = [disk["name"] for disk in body["data"]]
    assert "loop0" in names
    assert "ram0" not in names


def test_add_disk_endpoint_runs_in_async_context():
    def _loop_asserting_add_disk(*_args, **_kwargs):
        asyncio.get_running_loop()
        return "job-123"

    with patch(
        "hiveden.api.routers.storage.manager.add_disk_to_raid",
        _loop_asserting_add_disk,
    ):
        response = _client().post(
            "/storage/raid/md0/add-disk",
            json={"device_path": "/dev/loop0", "target_raid_level": "raid1"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["job_id"] == "job-123"
