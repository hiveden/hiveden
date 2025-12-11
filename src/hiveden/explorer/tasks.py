import os
import shutil
import re
import traceback
from datetime import datetime
from typing import List, Optional

from hiveden.explorer.manager import ExplorerManager
from hiveden.explorer.operations import ExplorerService
from hiveden.explorer.models import OperationStatus, ExplorerOperation, FileType, FileEntry

import logging

logger = logging.getLogger(__name__)

def perform_search(op_id: str, path: str, pattern: str, use_regex: bool, case_sensitive: bool, type_filter: str, show_hidden: bool):
    manager = ExplorerManager()
    service = ExplorerService()
    
    logger.info(f"Starting search operation {op_id} in {path} with pattern {pattern}")

    op = manager.get_operation(op_id)
    if not op:
        logger.error(f"Operation {op_id} not found")
        return

    op.status = OperationStatus.IN_PROGRESS
    manager.update_operation(op)

    matches = []
    total_scanned = 0
    start_time = datetime.now()

    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        if not use_regex:
            # Convert glob to regex: escape everything, then revert * and ? to regex equivalents
            pattern = re.escape(pattern).replace(r'\*', '.*').replace(r'\?', '.')
        
        logger.info(f"Compiled regex: {pattern}")
        regex = re.compile(pattern, flags)
        
        for root, dirs, files in os.walk(path):
            # Filtering hidden
            if not show_hidden:
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                files = [f for f in files if not f.startswith('.')]
            
            # Scan directories
            if type_filter in ['all', 'directory']:
                for d in dirs:
                    total_scanned += 1
                    if regex.search(d):
                        try:
                            full_path = os.path.join(root, d)
                            matches.append(service.get_file_entry(full_path).dict())
                        except Exception as e:
                            logger.warning(f"Error getting file entry for {d}: {e}")
            
            # Scan files
            if type_filter in ['all', 'file']:
                for f in files:
                    total_scanned += 1
                    if regex.search(f):
                        try:
                            full_path = os.path.join(root, f)
                            matches.append(service.get_file_entry(full_path).dict())
                        except Exception as e:
                            logger.warning(f"Error getting file entry for {f}: {e}")
            
            # Update progress periodically (every 100 items or so)
            if total_scanned % 100 == 0:
                op.processed_items = total_scanned
                manager.update_operation(op)

        search_time = (datetime.now() - start_time).total_seconds()
        
        op.result = {
            "matches": matches,
            "total_matches": len(matches),
            "search_time_seconds": search_time
        }
        op.status = OperationStatus.COMPLETED
        op.processed_items = total_scanned
        op.completed_at = datetime.utcnow()
        manager.update_operation(op)
        logger.info(f"Search operation {op_id} completed. Matches: {len(matches)}")

    except Exception as e:
        logger.error(f"Search operation {op_id} failed: {e}", exc_info=True)
        op.status = OperationStatus.FAILED
        op.error_message = str(e)
        op.completed_at = datetime.utcnow()
        manager.update_operation(op)

def perform_paste(op_id: str, source_paths: List[str], dest_path: str, conflict_resolution: str, rename_pattern: str):
    manager = ExplorerManager()
    service = ExplorerService()
    
    op = manager.get_operation(op_id)
    if not op:
        return

    op.status = OperationStatus.IN_PROGRESS
    # Estimate total items (shallow count at least)
    op.total_items = len(source_paths)
    manager.update_operation(op)

    processed = 0
    errors = []

    try:
        is_move = op.operation_type == "move" # Assuming logic sets this type
        
        for src in source_paths:
            if not os.path.exists(src):
                errors.append(f"Source not found: {src}")
                continue

            src_name = os.path.basename(src)
            final_dest = os.path.join(dest_path, src_name)

            # Conflict resolution
            if os.path.exists(final_dest):
                if conflict_resolution == 'skip':
                    continue
                elif conflict_resolution == 'overwrite':
                    if os.path.isdir(final_dest):
                        shutil.rmtree(final_dest)
                    else:
                        os.remove(final_dest)
                elif conflict_resolution == 'rename':
                    base, ext = os.path.splitext(src_name)
                    counter = 1
                    while os.path.exists(final_dest):
                        new_name = rename_pattern.format(name=base, n=counter) + ext
                        final_dest = os.path.join(dest_path, new_name)
                        counter += 1
                        if counter > 1000:
                            raise Exception("Too many name conflicts")

            # Perform copy/move
            if is_move:
                shutil.move(src, final_dest)
            else:
                if os.path.isdir(src):
                    shutil.copytree(src, final_dest)
                else:
                    shutil.copy2(src, final_dest)
            
            processed += 1
            op.processed_items = processed
            op.progress = int((processed / len(source_paths)) * 100)
            manager.update_operation(op)

        if errors:
            op.error_message = "; ".join(errors)
            if processed > 0:
                 # Partial success? requirements say 207 but this is internal status
                 # Let's mark completed if fully done, or failed if mostly failed?
                 # Or just COMPLETED with error message populated?
                 # Let's stick to COMPLETED if at least some worked, but maybe we need a PARTIAL status?
                 # Use FAILED if all failed.
                 if processed == 0:
                     op.status = OperationStatus.FAILED
                 else:
                     op.status = OperationStatus.COMPLETED
        else:
             op.status = OperationStatus.COMPLETED
             
        op.completed_at = datetime.utcnow()
        manager.update_operation(op)

    except Exception as e:
        op.status = OperationStatus.FAILED
        op.error_message = str(e) + "\n" + traceback.format_exc()
        op.completed_at = datetime.utcnow()
        manager.update_operation(op)
