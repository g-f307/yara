from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any
from pathlib import Path
import shutil
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

@router.post("/use-demo")
async def use_demo_data(request: SyncRequest) -> Dict[str, Any]:
    """
    Copia os arquivos mock do backend para o diretório de cache do projeto.
    """
    project_dir = ProjectManager.get_project_dir(request.project_id)
    project_dir.mkdir(parents=True, exist_ok=True)

    mock_dir = Path(__file__).resolve().parent.parent / "data" / "mock"
    copied_files = []

    for mock_file in mock_dir.iterdir():
        if not mock_file.is_file():
            continue
        shutil.copy2(mock_file, project_dir / mock_file.name)
        copied_files.append(mock_file.name)

    return {
        "status": "success",
        "files_copied": len(copied_files),
        "files": copied_files,
    }
