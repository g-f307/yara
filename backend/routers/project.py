from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from utils.project_manager import ProjectManager

router = APIRouter(prefix="/api/project", tags=["project"])

class SyncRequest(BaseModel):
    project_id: str
    files: List[Dict[str, str]]

@router.post("/sync")
async def sync_project(request: SyncRequest) -> Dict[str, Any]:
    """
    Sincroniza os arquivos do projeto baixando as URLs enviadas.
    """
    result = await ProjectManager.sync_files(request.project_id, request.files)
    return result

@router.get("/status/{project_id}")
async def project_status(project_id: str) -> Dict[str, Any]:
    """
    Check if the project directory exists and has files, 
    avoiding redundant redundant file syncs from node.js backend.
    """
    project_dir = ProjectManager.get_project_dir(project_id)
    files = list(project_dir.glob("*")) if project_dir.exists() else []
    return {"synced": len(files) > 0}
