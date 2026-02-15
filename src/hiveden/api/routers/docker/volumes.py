import traceback
from typing import Optional

from docker.errors import APIError, NotFound
from fastapi import APIRouter, HTTPException, Query
from fastapi.logger import logger

from hiveden.api.dtos import BaseResponse, VolumeListResponse
from hiveden.docker.volumes import DockerVolumeManager

router = APIRouter(tags=["Docker Volumes"])


@router.get("/volumes", response_model=VolumeListResponse)
def list_docker_volumes(
    dangling: Optional[bool] = Query(
        None,
        description="Filter by dangling volumes when provided.",
    )
):
    """List Docker volumes."""
    try:
        data = DockerVolumeManager().list_volumes(dangling=dangling)
        return VolumeListResponse(data=data)
    except Exception as e:
        logger.error(f"Error listing docker volumes: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/volumes/{volume_name}", response_model=BaseResponse)
def delete_docker_volume(volume_name: str):
    """Delete Docker volume by name."""
    try:
        DockerVolumeManager().delete_volume(volume_name)
        return BaseResponse(message=f"Volume {volume_name} deleted successfully.")
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Volume '{volume_name}' not found.")
    except APIError as e:
        if e.status_code == 409:
            raise HTTPException(status_code=409, detail=e.explanation or str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting docker volume {volume_name}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
