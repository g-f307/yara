from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from artifacts.catalog import ArtifactKind, SemanticCatalog
from metadata.service import MetadataError, MetadataService
from security.artifact_pipeline import ArtifactStore


def _project(temporary: str) -> tuple[str, str]:
    project_id = str(uuid.uuid4())
    feature = Path(temporary) / "features.tsv"
    feature.write_text(
        "feature-id\ts1\ts2\ts3\nf1\t1\t2\t3\nf2\t3\t2\t1\n",
        encoding="utf-8",
    )
    metadata = Path(temporary) / "metadata.tsv"
    metadata.write_text(
        "sample-id\tgroup\tlatitude\tcollection_date\ns1\tA\t-3.1\t2026-01-01\ns2\tA\t-3.2\t2026-01-02\ns3\tB\t-3.3\t2026-01-03\n",
        encoding="utf-8",
    )
    store = ArtifactStore(temporary)
    store.import_local_validated(project_id, feature, feature.name)
    store.import_local_validated(project_id, metadata, metadata.name)
    artifact = next(
        item for item in SemanticCatalog(temporary).classify_project(project_id)
        if item.kind == ArtifactKind.METADATA
    )
    return project_id, artifact.id


def test_initial_metadata_version_is_immutable_and_identifiable() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        project_id, artifact_id = _project(temporary)
        service = MetadataService(temporary)
        original = service.ensure_initial_version(project_id)
        original_bytes = service.version_path(project_id, original).read_bytes()
        columns, rows = service.rows(project_id)
        rows[0]["group"] = "C"
        edited = service.create_version(
            project_id,
            artifact_id,
            original.id,
            "generic",
            columns,
            rows,
            "user-1",
            True,
        )

        assert original.id != edited.id
        assert original.sha256 != edited.sha256
        assert service.version_path(project_id, original).read_bytes() == original_bytes
        assert service.active_version(project_id).id == edited.id


def test_restore_creates_a_new_version_without_mutating_history() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        project_id, artifact_id = _project(temporary)
        service = MetadataService(temporary)
        original = service.ensure_initial_version(project_id)
        columns, rows = service.rows(project_id)
        rows[0]["group"] = "C"
        edited = service.create_version(project_id, artifact_id, original.id, "generic", columns, rows, "user-1", True)
        restored = service.restore(project_id, original.id, "user-1")
        versions, active_id = service.list_versions(project_id)

        assert len(versions) == 3
        assert restored.id not in {original.id, edited.id}
        assert restored.parent_version_id == edited.id
        assert restored.sha256 == original.sha256
        assert restored.source == f"RESTORE:{original.id}"
        assert active_id == restored.id


def test_validation_explains_duplicates_formats_groups_and_readiness() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        project_id, _ = _project(temporary)
        service = MetadataService(temporary)
        columns = ["sample-id", "group", "latitude", "collection_date"]
        rows = [
            {"sample-id": "s1", "group": "Control", "latitude": "-91", "collection_date": "2026-15-01"},
            {"sample-id": "s1", "group": "control", "latitude": "-3", "collection_date": "2026-01-02"},
            {"sample-id": "", "group": "Treatment", "latitude": "-3", "collection_date": ""},
        ]
        result = service.validate(project_id, template_id="soil", columns=columns, rows=rows)
        codes = {item["code"] for item in result["diagnostics"]}

        assert {"DUPLICATE_SAMPLE_IDS", "MISSING_SAMPLE_IDS", "INCOMPATIBLE_SAMPLE_IDS"} <= codes
        assert "INVALID_FIELD_VALUE" in codes
        assert "SMALL_GROUP" in codes
        assert result["readiness"]["ready"] is False
        assert sum(item["weight"] for item in result["readiness"]["items"]) == 100


def test_unknown_columns_are_preserved_in_new_version() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        project_id, artifact_id = _project(temporary)
        service = MetadataService(temporary)
        original = service.ensure_initial_version(project_id)
        columns, rows = service.rows(project_id)
        columns.append("custom_research_field")
        for row in rows:
            row["custom_research_field"] = "preserved"
        created = service.create_version(project_id, artifact_id, original.id, "generic", columns, rows, "user-1", True)
        saved_columns, saved_rows = service.rows(project_id, created.id)

        assert "custom_research_field" in saved_columns
        assert all(row["custom_research_field"] == "preserved" for row in saved_rows)


def test_signed_metadata_routes_return_workspace_and_restore(signed_request) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        project_id, _ = _project(temporary)
        with patch("routers.metadata.CACHE_DIR", temporary):
            response = signed_request("GET", f"/api/metadata/versions?project_id={project_id}")
            assert response.status_code == 200
            workspace = response.json()["data"]
            original_id = workspace["active_version_id"]
            restore = signed_request(
                "POST",
                f"/api/metadata/versions/{original_id}/restore",
                {"project_id": project_id, "created_by_user_id": "user-1"},
            )

        assert restore.status_code == 200
        restored = restore.json()["data"]["version"]
        assert restored["id"] != original_id
        assert restored["source"] == f"RESTORE:{original_id}"


def test_version_cannot_be_restored_through_another_project(signed_request) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        first_project, _ = _project(temporary)
        second_project, _ = _project(temporary)
        service = MetadataService(temporary)
        foreign_version = service.ensure_initial_version(first_project)
        service.ensure_initial_version(second_project)
        with patch("routers.metadata.CACHE_DIR", temporary):
            response = signed_request(
                "POST",
                f"/api/metadata/versions/{foreign_version.id}/restore",
                {"project_id": second_project, "created_by_user_id": "user-1"},
            )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "METADATA_VERSION_NOT_FOUND"


def test_creation_requires_confirmed_preview() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        project_id, artifact_id = _project(temporary)
        service = MetadataService(temporary)
        original = service.ensure_initial_version(project_id)
        columns, rows = service.rows(project_id)

        with pytest.raises(MetadataError) as raised:
            service.create_version(project_id, artifact_id, original.id, "generic", columns, rows, "user-1", False)
        assert raised.value.code == "METADATA_CONFIRMATION_REQUIRED"

        versions, _ = service.list_versions(project_id)
        assert len(versions) == 1
