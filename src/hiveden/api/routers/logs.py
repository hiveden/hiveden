from typing import Optional
from fastapi import APIRouter, Query

from hiveden.api.dtos import LogListResponse
from hiveden.db.session import get_db_manager
from hiveden.db.repositories.logs import LogRepository

router = APIRouter(prefix="/logs", tags=["Logs"])

@router.get("", response_model=LogListResponse)
def get_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    level: Optional[str] = None,
    module: Optional[str] = None
):
    """
    Retrieve system logs with optional filtering.
    """
    db_manager = get_db_manager()
    repo = LogRepository(db_manager)
    
    logs = repo.get_logs(limit=limit, offset=offset, level=level, module=module)
    return LogListResponse(data=logs)
