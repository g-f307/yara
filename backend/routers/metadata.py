from dataclasses import asdict
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from metadata.service import MetadataError, MetadataService
from observability import ApiError
from security.artifact_pipeline import ArtifactSecurityError
from utils.project_manager import CACHE_DIR

router = APIRouter(prefix="/api/metadata", tags=["metadata"])


class ValidateRequest(BaseModel):
    project_id: str
    template_id: str
    columns: list[str] | None = None
    rows: list[dict[str, Any]] | None = None


class CreateVersionRequest(BaseModel):
    project_id: str
    artifact_id: str
    parent_version_id: str | None = None
    template_id: str
    columns: list[str] = Field(min_length=1)
    rows: list[dict[str, Any]]
    created_by_user_id: str | None = None
    confirmed: bool = False


class RestoreRequest(BaseModel):
    project_id: str
    created_by_user_id: str | None = None


def _public_error(error: MetadataError | ArtifactSecurityError) -> ApiError:
    status_code = {
        "AMBIGUOUS_ARTIFACT": 409,
        "METADATA_VERSION_CONFLICT": 409,
        "METADATA_CONFIRMATION_REQUIRED": 409,
        "METADATA_NOT_FOUND": 404,
        "METADATA_VERSION_NOT_FOUND": 404,
        "METADATA_TEMPLATE_NOT_FOUND": 404,
        "INVALID_PROJECT_ID": 400,
        "INVALID_METADATA": 422,
    }.get(error.code, 400)
    return ApiError(error.code, status_code, error.public_message)


@router.get("/versions")
async def versions(project_id: str):
    try:
        data = MetadataService(CACHE_DIR).workspace(project_id)
    except (MetadataError, ArtifactSecurityError) as error:
        raise _public_error(error) from error
    return {"data": data, "plotly_spec": None}


@router.post("/validate")
async def validate_metadata(request: ValidateRequest):
    try:
        data = MetadataService(CACHE_DIR).validate(
            request.project_id,
            template_id=request.template_id,
            columns=request.columns,
            rows=request.rows,
        )
    except (MetadataError, ArtifactSecurityError) as error:
        raise _public_error(error) from error
    return {"data": data, "plotly_spec": None}


@router.post("/versions")
async def create_version(request: CreateVersionRequest):
    try:
        service = MetadataService(CACHE_DIR)
        version = service.create_version(
            project_id=request.project_id,
            artifact_id=request.artifact_id,
            parent_version_id=request.parent_version_id,
            template_id=request.template_id,
            columns=request.columns,
            rows=request.rows,
            created_by_user_id=request.created_by_user_id,
            confirmed=request.confirmed,
        )
        data = {"version": asdict(version), "workspace": service.workspace(request.project_id)}
    except (MetadataError, ArtifactSecurityError) as error:
        raise _public_error(error) from error
    return {"data": data, "plotly_spec": None}


@router.post("/versions/{version_id}/restore")
async def restore_version(version_id: str, request: RestoreRequest):
    try:
        service = MetadataService(CACHE_DIR)
        version = service.restore(request.project_id, version_id, request.created_by_user_id)
        data = {"version": asdict(version), "workspace": service.workspace(request.project_id)}
    except (MetadataError, ArtifactSecurityError) as error:
        raise _public_error(error) from error
    return {"data": data, "plotly_spec": None}


@router.get("/readiness")
async def readiness(project_id: str):
    try:
        service = MetadataService(CACHE_DIR)
        active = service.ensure_initial_version(project_id)
        data = service.validate(project_id, template_id=active.template_id)
    except (MetadataError, ArtifactSecurityError) as error:
        raise _public_error(error) from error
    return {"data": data["readiness"] | {"diagnostics": data["diagnostics"]}, "plotly_spec": None}
