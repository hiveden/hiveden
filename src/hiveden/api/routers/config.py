import yaml
from fastapi import APIRouter, Body, HTTPException
from fastapi.logger import logger
import traceback

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
        logger.error(f"Invalid YAML: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")
    except Exception as e:
        logger.error(f"Error in submit_config: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
