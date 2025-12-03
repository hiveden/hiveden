"""API router for packages."""

from fastapi import APIRouter, HTTPException
from typing import List

from hiveden.api.dtos import DataResponse
from hiveden.pkgs.manager import get_system_required_packages

router = APIRouter(prefix="/pkgs", tags=["Packages"])


@router.get("/required", response_model=DataResponse)
def list_required_packages():
    """List all required packages for the system and their installation status.
    
    Returns:
        List of required packages with status
    """
    try:
        packages = get_system_required_packages()
        return DataResponse(data=[pkg.dict() for pkg in packages])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
