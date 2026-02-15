from typing import Any, Dict, List, Optional

import docker
from docker import errors

from hiveden.docker.volume_rules import normalize_volume_attrs

client = docker.from_env()


class DockerVolumeManager:
    def __init__(self):
        self.client = client

    def list_volumes(self, dangling: Optional[bool] = None) -> List[Dict[str, Any]]:
        """List Docker volumes, optionally filtering by dangling state."""
        kwargs = {}
        if dangling is not None:
            kwargs["filters"] = {"dangling": str(dangling).lower()}

        volumes = self.client.volumes.list(**kwargs)
        return [normalize_volume_attrs(v.attrs or {}) for v in volumes]

    def delete_volume(self, volume_name: str):
        """Delete a Docker volume by name."""
        volume = self.client.volumes.get(volume_name)
        volume.remove()


def list_volumes(dangling: Optional[bool] = None):
    return DockerVolumeManager().list_volumes(dangling=dangling)


def delete_volume(volume_name: str):
    try:
        DockerVolumeManager().delete_volume(volume_name)
    except errors.NotFound:
        raise
    except errors.APIError:
        raise
