"""API router for packages."""

from fastapi import APIRouter, HTTPException
from fastapi.logger import logger
import traceback
from typing import List

from hiveden.api.dtos import DataResponse
from hiveden.pkgs.manager import get_system_required_packages

router = APIRouter(prefix="/pkgs", tags=["Packages"])


@router.get("/required", response_model=DataResponse)
def list_required_packages(tags: str = None):
    """List all required packages for the system and their installation status.
    
    Args:
        tags: Comma-separated list of tags to filter packages by (e.g. "storage,system")
    
    Returns:
        List of required packages with status
    """
    try:
        packages = get_system_required_packages(tags=tags)
        return DataResponse(data=[pkg.dict() for pkg in packages])
    except Exception as e:
        logger.error(f"Error listing required packages: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
