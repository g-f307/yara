from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from pathlib import Path
from utils.project_manager import ProjectManager
from security.artifact_pipeline import ArtifactSecurityError, ArtifactStore

router = APIRouter(prefix="/api/project", tags=["project"])

class SyncRequest(BaseModel):
    project_id: str
    files: List[Dict[str, str]]

@router.post("/sync")
async def sync_project(request: SyncRequest) -> Dict[str, Any]:
    """
    Sincroniza os arquivos do projeto baixando as URLs enviadas.
    """
    try:
        return await ProjectManager.sync_files(request.project_id, request.files)
    except ArtifactSecurityError as exc:
        raise HTTPException(status_code=400, detail=exc.public_message) from exc

@router.get("/status/{project_id}")
async def project_status(project_id: str) -> Dict[str, Any]:
    """
    Check if the project directory exists and has files, 
    avoiding redundant redundant file syncs from node.js backend.
    """
    try:
        project_dir = ProjectManager.get_project_dir(project_id)
    except ArtifactSecurityError as exc:
        raise HTTPException(status_code=400, detail=exc.public_message) from exc
    return {"synced": ProjectManager.has_valid_artifacts(project_id)}

@router.post("/use-demo")
async def use_demo_data(request: SyncRequest) -> Dict[str, Any]:
    """
    Copia os arquivos mock do backend para o diretório de cache do projeto.
    """
    try:
        project_dir = ProjectManager.get_project_dir(request.project_id)
    except ArtifactSecurityError as exc:
        raise HTTPException(status_code=400, detail=exc.public_message) from exc
    mock_dir = Path(__file__).resolve().parent.parent / "data" / "mock"
    store = ArtifactStore(project_dir.parent)
    copied_files = []

    for mock_file in mock_dir.iterdir():
        if not mock_file.is_file():
            continue
        try:
            record = store.import_local_validated(
                request.project_id,
                mock_file,
                mock_file.name,
            )
            copied_files.append(record.original_name)
        except ArtifactSecurityError:
            continue

    return {
        "status": "success",
        "files_copied": len(copied_files),
        "files": copied_files,
    }
