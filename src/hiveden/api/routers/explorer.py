from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, status
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional
import os
from datetime import datetime
import logging

from hiveden.explorer.models import (
    DirectoryListingResponse,
    FileEntry,
    FilePropertyResponse,
    CreateDirectoryRequest,
    DeleteRequest,
    DeleteResponse,
    RenameRequest,
    GenericResponse,
    ClipboardCopyRequest,
    ClipboardPasteRequest,
    ClipboardStatusResponse,
    LocationCreateRequest,
    LocationUpdateRequest,
    FilesystemLocation,
    SearchRequest,
    OperationResponse,
    ExplorerOperation,
    ConfigUpdateRequest,
    ExplorerConfig,
    SortBy,
    SortOrder,
    OperationStatus,
    OperationType
)
from hiveden.explorer.manager import ExplorerManager
from hiveden.explorer.operations import ExplorerService
from hiveden.explorer.tasks import perform_search, perform_paste

router = APIRouter(
    prefix="/explorer",
    tags=["Explorer"]
)

logger = logging.getLogger(__name__)

# In-memory clipboard store
# { session_id: { operation: "copy"|"cut", paths: [], timestamp: datetime } }
clipboard_store = {}

def get_manager():
    return ExplorerManager()

def get_service():
    config = get_manager().get_config()
    root = config.get("root_directory", "/")
    return ExplorerService(root_directory=root)

# --- Navigation ---

@router.get("/list", response_model=DirectoryListingResponse)
def list_directory(
    path: str,
    show_hidden: bool = False,
    sort_by: SortBy = SortBy.NAME,
    sort_order: SortOrder = SortOrder.ASC
):
    service = get_service()
    try:
        entries, count, total_size = service.list_directory(path, show_hidden, sort_by, sort_order)
        return DirectoryListingResponse(
            current_path=path,
            parent_path=os.path.dirname(path),
            entries=entries,
            total_entries=count,
            total_size=total_size,
            total_size_human=service._human_readable_size(total_size)
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/navigate", response_model=DirectoryListingResponse)
def navigate(
    body: dict, # Hack to allow flexible body or define model. 
                # Req doc says {path, show_hidden}. Let's make a model or use param.
):
    path = body.get("path")
    if not path:
        raise HTTPException(status_code=400, detail="Path required")
    show_hidden = body.get("show_hidden", False)
    
    return list_directory(path, show_hidden=show_hidden)

@router.get("/properties", response_model=FilePropertyResponse)
def get_properties(path: str):
    service = get_service()
    try:
        entry = service.get_file_entry(path)
        return FilePropertyResponse(entry=entry)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Path not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cwd")
def get_cwd():
    # Stateless, returns root as per reqs
    service = get_service()
    return {"success": True, "current_path": service.root_directory, "is_root": True}

# --- File Operations ---

@router.post("/create-directory", status_code=201)
def create_directory(req: CreateDirectoryRequest):
    service = get_service()
    try:
        new_path = service.create_directory(req.path, req.parents)
        return {"success": True, "message": "Directory created successfully", "path": new_path}
    except FileExistsError:
        raise HTTPException(status_code=409, detail="Path already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete", response_model=DeleteResponse)
def delete_items(req: DeleteRequest):
    service = get_service()
    deleted = []
    failed = []
    
    for path in req.paths:
        try:
            service.delete_path(path, req.recursive)
            deleted.append(path)
        except Exception as e:
            failed.append({"path": path, "error": str(e)})
    
    if failed:
        return JSONResponse(
            status_code=207,
            content={
                "success": False,
                "message": f"Deleted {len(deleted)} of {len(req.paths)} items",
                "deleted": deleted,
                "failed": failed
            }
        )
        
    return DeleteResponse(
        success=True,
        message=f"Successfully deleted {len(deleted)} items",
        deleted=deleted,
        failed=[]
    )

@router.post("/rename")
def rename_item(req: RenameRequest):
    service = get_service()
    try:
        # Check if destination is just a name or full path
        dest = req.destination
        if os.path.sep not in dest:
            dest = os.path.join(os.path.dirname(req.source), dest)
            
        new_path = service.rename_path(req.source, dest, req.overwrite)
        return {
            "success": True, 
            "message": "Renamed successfully", 
            "old_path": req.source, 
            "new_path": new_path
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Source not found")
    except FileExistsError:
        raise HTTPException(status_code=409, detail="Destination exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download")
def download_file(path: str):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    if os.path.isdir(path):
        raise HTTPException(status_code=400, detail="Cannot download directory")
        
    filename = os.path.basename(path)
    return FileResponse(path, filename=filename, media_type='application/octet-stream')

# --- Clipboard ---

@router.post("/clipboard/copy")
def clipboard_copy(req: ClipboardCopyRequest):
    clipboard_store[req.session_id] = {
        "operation": "copy",
        "paths": req.paths,
        "timestamp": datetime.now()
    }
    return {
        "success": True,
        "message": f"{len(req.paths)} items copied to clipboard",
        "operation": "copy",
        "items_count": len(req.paths),
        "session_id": req.session_id
    }

@router.post("/clipboard/cut")
def clipboard_cut(req: ClipboardCopyRequest):
    clipboard_store[req.session_id] = {
        "operation": "cut",
        "paths": req.paths,
        "timestamp": datetime.now()
    }
    return {
        "success": True,
        "message": f"{len(req.paths)} items cut to clipboard",
        "operation": "cut",
        "items_count": len(req.paths),
        "session_id": req.session_id
    }

@router.post("/clipboard/paste", status_code=202)
def clipboard_paste(req: ClipboardPasteRequest, background_tasks: BackgroundTasks):
    session_data = clipboard_store.get(req.session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Clipboard session not found")
    
    paths = session_data["paths"]
    op_type = "move" if session_data["operation"] == "cut" else "copy"
    
    manager = get_manager()
    op = manager.create_operation(op_type, OperationStatus.PENDING)
    op.source_paths = paths
    op.destination_path = req.destination
    manager.update_operation(op)
    
    background_tasks.add_task(
        perform_paste,
        op.id,
        paths,
        req.destination,
        req.conflict_resolution,
        req.rename_pattern
    )
    
    # If cut, clear clipboard? Usually yes.
    if session_data["operation"] == "cut":
        del clipboard_store[req.session_id]

    return {
        "success": True,
        "message": "Paste operation started",
        "operation_id": op.id,
        "operation_type": op_type,
        "status": "pending",
        "total_items": len(paths)
    }

@router.get("/clipboard/status", response_model=ClipboardStatusResponse)
def clipboard_status(session_id: str):
    data = clipboard_store.get(session_id)
    if not data:
        return ClipboardStatusResponse(
            has_items=False,
            items_count=0,
            paths=[],
            total_size=0,
            total_size_human="0 B"
        )
    
    # Calculate size (optional, might be slow for many files)
    total_size = 0
    # For now skipping real size calc to avoid perf hit, just returning placeholder or calc if small list
    
    return ClipboardStatusResponse(
        has_items=True,
        operation=data["operation"],
        items_count=len(data["paths"]),
        paths=data["paths"],
        total_size=0, 
        total_size_human="N/A" # TODO: Implement size calc
    )

@router.delete("/clipboard/clear")
def clipboard_clear(session_id: str):
    if session_id in clipboard_store:
        del clipboard_store[session_id]
    return {"success": True, "message": "Clipboard cleared"}

# --- Bookmarks (Filesystem Locations) ---

@router.get("/bookmarks")
def list_bookmarks():
    manager = get_manager()
    locations = manager.get_locations()
    # Check existence
    result = []
    for loc in locations:
        loc.exists = os.path.exists(loc.path)
        result.append(loc)
    return {"success": True, "bookmarks": result, "total": len(result)}

@router.post("/bookmarks", status_code=201)
def create_bookmark(req: LocationCreateRequest):
    manager = get_manager()
    loc = manager.create_location(req.label, req.path, req.type, req.description)
    return {"success": True, "message": "Bookmark created successfully", "bookmark": loc}

@router.put("/bookmarks/{bookmark_id}")
def update_bookmark(bookmark_id: int, req: LocationUpdateRequest):
    manager = get_manager()
    loc = manager.update_location(bookmark_id, req.label, req.path, req.description)
    if not loc:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return {"success": True, "message": "Bookmark updated successfully", "bookmark": loc}

@router.delete("/bookmarks/{bookmark_id}")
def delete_bookmark(bookmark_id: int):
    manager = get_manager()
    try:
        manager.delete_location(bookmark_id)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return {"success": True, "message": "Bookmark deleted successfully"}

# --- USB ---

@router.get("/usb-devices")
def list_usb_devices():
    service = get_service()
    devices = service.get_usb_devices()
    return {"success": True, "devices": devices, "total_devices": len(devices)}

# --- Search ---

@router.post("/search", status_code=202)
def search_files(req: SearchRequest, background_tasks: BackgroundTasks):
    manager = get_manager()
    op = manager.create_operation(OperationType.SEARCH, OperationStatus.PENDING)
    op.source_paths = [req.path] # Store root as source
    manager.update_operation(op)
    
    background_tasks.add_task(
        perform_search,
        op.id,
        req.path,
        req.pattern,
        req.use_regex,
        req.case_sensitive,
        req.type_filter,
        req.show_hidden
    )
    
    return {
        "success": True,
        "message": "Search operation started",
        "operation_id": op.id,
        "operation_type": "search",
        "status": "pending"
    }

# --- Operations ---

@router.get("/operations/{operation_id}", response_model=OperationResponse)
def get_operation_status(operation_id: str):
    manager = get_manager()
    op = manager.get_operation(operation_id)
    if not op:
        raise HTTPException(status_code=404, detail="Operation not found")
    return OperationResponse(operation=op)

@router.get("/operations")
def list_operations(
    status: Optional[str] = None,
    operation_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    manager = get_manager()
    # Filter not implemented in manager yet, just pagination
    # Doing in-memory filter or assume manager update later
    ops = manager.get_operations(limit=1000, offset=0) # Fetch more then filter
    
    filtered = []
    for op in ops:
        if status and op.status != status:
            continue
        if operation_type and op.operation_type != operation_type:
            continue
        filtered.append(op)
    
    # paginate
    total = len(filtered)
    start = offset
    end = offset + limit
    sliced = filtered[start:end]
    
    return {"success": True, "operations": sliced, "total": total, "limit": limit, "offset": offset}

@router.delete("/operations/{operation_id}")
def delete_operation(operation_id: str):
    manager = get_manager()
    # If in progress, should cancel task? 
    # Cancelling background tasks in FastAPI/Python threads is hard without specific mechanism.
    # For now just deleting record.
    manager.delete_operation(operation_id)
    return {"success": True, "message": "Operation cancelled/deleted successfully"}

# --- Config ---

@router.get("/config")
def get_explorer_config():
    manager = get_manager()
    config = manager.get_config()
    return {"success": True, "config": config}

@router.put("/config")
def update_explorer_config(req: ConfigUpdateRequest):
    manager = get_manager()
    if req.show_hidden_files is not None:
        manager.update_config("show_hidden_files", str(req.show_hidden_files).lower())
    if req.usb_mount_path:
        manager.update_config("usb_mount_path", req.usb_mount_path)
    if req.root_directory:
        manager.update_config("root_directory", req.root_directory)
        
    return {"success": True, "message": "Configuration updated successfully", "config": manager.get_config()}
