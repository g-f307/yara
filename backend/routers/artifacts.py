from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel

from artifacts.catalog import ArtifactCatalogError, SemanticCatalog
from observability import ApiError
from security.artifact_pipeline import ArtifactSecurityError
from utils.project_manager import CACHE_DIR

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


class ClassificationRequest(BaseModel):
    project_id: str


class SelectionRequest(BaseModel):
    project_id: str
    artifact_id: str


def _public_catalog_error(error: ArtifactCatalogError | ArtifactSecurityError) -> ApiError:
    status_code = {
        "AMBIGUOUS_ARTIFACT": 409,
        "ARTIFACT_NOT_FOUND": 404,
        "INVALID_PROJECT_ID": 400,
    }.get(error.code, 400)
    return ApiError(error.code, status_code, error.public_message)


@router.get("")
async def list_artifacts(project_id: str):
    try:
        artifacts = SemanticCatalog(CACHE_DIR).classify_project(project_id)
    except (ArtifactCatalogError, ArtifactSecurityError) as error:
        raise _public_catalog_error(error) from error
    return {"data": {"artifacts": [asdict(item) for item in artifacts]}, "plotly_spec": None}


@router.post("/classify")
async def classify_artifacts(request: ClassificationRequest):
    try:
        artifacts = SemanticCatalog(CACHE_DIR).classify_project(request.project_id)
    except (ArtifactCatalogError, ArtifactSecurityError) as error:
        raise _public_catalog_error(error) from error
    return {"data": {"artifacts": [asdict(item) for item in artifacts]}, "plotly_spec": None}


@router.post("/select")
async def select_artifact(request: SelectionRequest):
    try:
        artifact = SemanticCatalog(CACHE_DIR).select_artifact(
            request.project_id,
            request.artifact_id,
        )
    except (ArtifactCatalogError, ArtifactSecurityError) as error:
        raise _public_catalog_error(error) from error
    return {"data": {"artifact": asdict(artifact)}, "plotly_spec": None}


@router.get("/compatibility")
async def artifact_compatibility(project_id: str):
    try:
        compatibility = SemanticCatalog(CACHE_DIR).compatibility(project_id)
    except (ArtifactCatalogError, ArtifactSecurityError) as error:
        raise _public_catalog_error(error) from error
    return {"data": {"compatibility": [asdict(item) for item in compatibility]}, "plotly_spec": None}
