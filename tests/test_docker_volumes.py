from types import SimpleNamespace

from hiveden.docker.volumes import DockerVolumeManager


def test_list_volumes_returns_normalized_shape():
    manager = DockerVolumeManager()

    fake_volume = SimpleNamespace(
        attrs={
            "Name": "pgdata",
            "Driver": "local",
            "Mountpoint": "/var/lib/docker/volumes/pgdata/_data",
            "CreatedAt": "2026-02-15T10:00:00Z",
            "Labels": {"managed-by": "hiveden"},
            "Scope": "local",
            "Options": {"o": "bind"},
        }
    )

    manager.client = SimpleNamespace(
        volumes=SimpleNamespace(
            list=lambda **kwargs: [fake_volume],
        )
    )

    volumes = manager.list_volumes()
    assert len(volumes) == 1
    assert volumes[0]["name"] == "pgdata"
    assert volumes[0]["driver"] == "local"
    assert volumes[0]["scope"] == "local"


def test_list_volumes_applies_dangling_filter():
    manager = DockerVolumeManager()

    called = {}

    def fake_list(**kwargs):
        called.update(kwargs)
        return []

    manager.client = SimpleNamespace(
        volumes=SimpleNamespace(list=fake_list),
    )

    manager.list_volumes(dangling=True)
    assert called["filters"] == {"dangling": "true"}


def test_delete_volume_removes_target_volume():
    removed = {"called": False}

    class FakeVolume:
        def remove(self):
            removed["called"] = True

    manager = DockerVolumeManager()
    manager.client = SimpleNamespace(
        volumes=SimpleNamespace(get=lambda _name: FakeVolume()),
    )

    manager.delete_volume("pgdata")
    assert removed["called"] is True
