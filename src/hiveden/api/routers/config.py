import yaml
from fastapi import APIRouter, Body, HTTPException

from hiveden.api.dtos import DataResponse
from hiveden.docker.actions import apply_configuration

router = APIRouter(prefix="/config", tags=["Config"])

@router.post("", response_model=DataResponse)
def submit_config(config: str = Body(...)):
    """Submit a YAML configuration."""
    try:
        data = yaml.safe_load(config)
        messages = apply_configuration(data['docker'])
        return DataResponse(data=messages)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
