import traceback

from fastapi import APIRouter, HTTPException
from fastapi.logger import logger

from hiveden.api.dtos import (
    DatabaseCreateRequest,
    DatabaseListResponse,
    DatabaseUserListResponse,
    SuccessResponse,
)
from hiveden.db.session import get_db_manager
from hiveden.services.logs import LogService

router = APIRouter(prefix="/db", tags=["Database"])

@router.get("/databases", response_model=DatabaseListResponse)
def list_databases():
    """List all databases."""
    try:
        manager = get_db_manager()
        dbs = manager.list_databases()
        return DatabaseListResponse(data=dbs)
    except Exception as e:
        logger.error(f"Error listing databases: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/databases", response_model=SuccessResponse)
def create_database(req: DatabaseCreateRequest):
    """Create a new database."""
    try:
        manager = get_db_manager()
        manager.create_database(req.name, req.owner)
        
        LogService().info(
            actor="user",
            action="database.create",
            message=f"Created database {req.name}",
            module="database",
            metadata={"database": req.name, "owner": req.owner}
        )
        
        return SuccessResponse(message=f"Database '{req.name}' created successfully.")
    except Exception as e:
        logger.error(f"Error creating database {req.name}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/databases/{db_name}", response_model=SuccessResponse)
def delete_database(db_name: str):
    """Delete a database."""
    try:
        manager = get_db_manager()
        manager.delete_database(db_name)
        
        LogService().info(
            actor="user",
            action="database.delete",
            message=f"Deleted database {db_name}",
            module="database",
            metadata={"database": db_name}
        )
        
        return SuccessResponse(message=f"Database '{db_name}' deleted successfully.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting database {db_name}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users", response_model=DatabaseUserListResponse)
def list_users():
    """List all database users."""
    try:
        manager = get_db_manager()
        users = manager.list_users()
        return DatabaseUserListResponse(data=users)
    except Exception as e:
        logger.error(f"Error listing users: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
