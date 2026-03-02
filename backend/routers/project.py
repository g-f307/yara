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
