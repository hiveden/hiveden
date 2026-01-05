import traceback
from fastapi import APIRouter, HTTPException
from fastapi.logger import logger

from hiveden.api.dtos import DataResponse, SuccessResponse
from hiveden.systemd.manager import SystemdManager
from hiveden.systemd.models import ServiceActionRequest

router = APIRouter(prefix="/systemd", tags=["Systemd"])

@router.get("/services", response_model=DataResponse)
def list_services():
    """List all managed systemd services."""
    try:
        manager = SystemdManager()
        return DataResponse(data=manager.list_services())
    except Exception as e:
        logger.error(f"Error listing services: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services/{service_name}", response_model=DataResponse)
def get_service(service_name: str):
    """Get status of a specific service."""
    try:
        manager = SystemdManager()
        status = manager.get_service_status(service_name)
        if not status:
            raise HTTPException(status_code=404, detail="Service not found")
        return DataResponse(data=status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service {service_name}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/services/{service_name}/{action}", response_model=DataResponse)
def manage_service(service_name: str, action: str):
    """
    Perform action on service (start, stop, restart, enable, disable).
    Note: action parameter in path is for convenience/REST style, 
    but we can also use body. Using path here as per request.
    """
    try:
        manager = SystemdManager()
        status = manager.manage_service(service_name, action)
        return DataResponse(data=status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error managing service {service_name}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

