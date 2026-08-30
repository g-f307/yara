from __future__ import annotations

import tempfile
import uuid
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from artifacts.catalog import (
    ArtifactCatalogError,
    ArtifactKind,
    SemanticCatalog,
)
from security.artifact_pipeline import ArtifactStore


def _write_qiime(path: Path, semantic_type: str) -> Path:
    artifact = path.with_suffix(".qza")
    root = "11111111-1111-4111-8111-111111111111"
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr(f"{root}/VERSION", "QIIME 2\narchive: 5\nframework: 2024.2.0\n")
        archive.writestr(f"{root}/metadata.yaml", f"type: {semantic_type}\nformat: BIOMV210DirFmt\n")
        archive.writestr(f"{root}/data/table.tsv", "id\ts1\nf1\t1\n")
    return artifact


def test_catalog_classifies_tables_by_content() -> None:
    project_id = str(uuid.uuid4())
    with tempfile.TemporaryDirectory() as temporary:
        source = Path(temporary) / "source"
        source.mkdir()
        alpha = source / "alpha.tsv"
        alpha.write_text("sample-id\tshannon\ns1\t2.4\ns2\t3.1\n", encoding="utf-8")
        taxonomy = source / "taxonomy.tsv"
        taxonomy.write_text("Feature ID\tTaxon\nf1\tk__Bacteria\n", encoding="utf-8")
        rarefaction = source / "rarefaction.tsv"
        rarefaction.write_text("sample-id\t100\t200\ns1\t4\t7\n", encoding="utf-8")
        store = ArtifactStore(temporary)
        store.import_local_validated(project_id, alpha, alpha.name)
        store.import_local_validated(project_id, taxonomy, taxonomy.name)
        store.import_local_validated(project_id, rarefaction, rarefaction.name)

        artifacts = SemanticCatalog(temporary).classify_project(project_id)

    assert {artifact.kind for artifact in artifacts} == {
        ArtifactKind.ALPHA_VECTOR,
        ArtifactKind.TAXONOMY,
        ArtifactKind.RAREFACTION_CURVE,
    }
    assert all(artifact.classifier_version == "1.0.0" for artifact in artifacts)


def test_catalog_extracts_qiime_metadata_without_modifying_artifact() -> None:
    project_id = str(uuid.uuid4())
    with tempfile.TemporaryDirectory() as temporary:
        archive = _write_qiime(Path(temporary) / "feature-table", "FeatureTable[Frequency]")
        store = ArtifactStore(temporary)
        record = store.import_local_validated(project_id, archive, archive.name)
        stored = store.storage_path / project_id / record.physical_name
        original_bytes = stored.read_bytes()

        artifact = SemanticCatalog(temporary).classify_project(project_id)[0]

        assert stored.read_bytes() == original_bytes
    assert artifact.kind == ArtifactKind.FEATURE_TABLE
    assert artifact.qiime_uuid == "11111111-1111-4111-8111-111111111111"
    assert artifact.qiime_version == "2024.2.0"
    assert artifact.semantic_type == "FeatureTable[Frequency]"


def test_catalog_keeps_unknown_qiime_semantic_type_as_unknown() -> None:
    project_id = str(uuid.uuid4())
    with tempfile.TemporaryDirectory() as temporary:
        source = Path(temporary) / "unknown.qza"
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr("artifact/VERSION", "QIIME 2\narchive: 5\nframework: 2024.2.0\n")
            archive.writestr("artifact/metadata.yaml", "type: NovelScientificResult\nformat: NovelDirFmt\n")
            archive.writestr("artifact/data/value.txt", "valid QIIME structure")
        store = ArtifactStore(temporary)
        store.import_local_validated(project_id, source, source.name)

        artifact = SemanticCatalog(temporary).classify_project(project_id)[0]

    assert artifact.kind == ArtifactKind.UNKNOWN
    assert artifact.confidence == 0.4


def test_catalog_blocks_ambiguous_automatic_selection() -> None:
    project_id = str(uuid.uuid4())
    with tempfile.TemporaryDirectory() as temporary:
        store = ArtifactStore(temporary)
        for index, name in enumerate(("alpha-a.tsv", "alpha-b.tsv"), start=1):
            source = Path(temporary) / name
            source.write_text(
                f"sample-id\tshannon\ns1\t{index}.4\ns2\t{index}.1\n",
                encoding="utf-8",
            )
            store.import_local_validated(project_id, source, name)

        catalog = SemanticCatalog(temporary)
        compatibility = catalog.compatibility(project_id)
        with pytest.raises(ArtifactCatalogError) as raised:
            catalog.select_path(project_id, "alpha")
        selected = catalog.select_artifact(project_id, catalog.classify_project(project_id)[0].id)
        selected_path = catalog.select_path(project_id, "alpha")

    assert raised.value.code == "AMBIGUOUS_ARTIFACT"
    assert compatibility[0].status == "AMBIGUOUS"
    assert selected.selected is True
    assert selected_path.name == selected.physical_name


def test_catalog_requires_explicit_metadata_selection_when_ambiguous() -> None:
    project_id = str(uuid.uuid4())
    with tempfile.TemporaryDirectory() as temporary:
        store = ArtifactStore(temporary)
        for index, name in enumerate(("metadata-a.tsv", "metadata-b.tsv"), start=1):
            source = Path(temporary) / name
            source.write_text(
                f"sample-id\tgroup\ns{index}\tgroup-{index}\n",
                encoding="utf-8",
            )
            store.import_local_validated(project_id, source, name)

        catalog = SemanticCatalog(temporary)
        with pytest.raises(ArtifactCatalogError) as raised:
            catalog.select_path(project_id, "metadata")

    assert raised.value.code == "AMBIGUOUS_ARTIFACT"


def test_only_valid_manifest_records_are_catalogued() -> None:
    project_id = str(uuid.uuid4())
    with tempfile.TemporaryDirectory() as temporary:
        project_dir = Path(temporary) / project_id
        project_dir.mkdir()
        unregistered = project_dir / "outside.tsv"
        unregistered.write_text("sample-id\tshannon\ns1\t2.4\n", encoding="utf-8")

        assert SemanticCatalog(temporary).classify_project(project_id) == []


def test_feature_table_compatibility_uses_hashed_identifiers() -> None:
    project_id = str(uuid.uuid4())
    with tempfile.TemporaryDirectory() as temporary:
        feature_table = Path(temporary) / "features.tsv"
        feature_table.write_text("feature-id\ts1\ts2\nf1\t1\t2\n", encoding="utf-8")
        metadata = Path(temporary) / "metadata.tsv"
        metadata.write_text("sample-id\tgroup\ns1\tA\ns2\tB\n", encoding="utf-8")
        store = ArtifactStore(temporary)
        store.import_local_validated(project_id, feature_table, feature_table.name)
        store.import_local_validated(project_id, metadata, metadata.name)

        relations = SemanticCatalog(temporary).compatibility(project_id)

    assert any(
        relation.status == "COMPATIBLE" and relation.reason_code == "SAMPLE_IDS_COMPATIBLE"
        for relation in relations
    )


def test_classification_route_returns_only_project_manifest(signed_request) -> None:
    project_id = str(uuid.uuid4())
    with tempfile.TemporaryDirectory() as temporary:
        alpha = Path(temporary) / "alpha.tsv"
        alpha.write_text("sample-id\tshannon\ns1\t2.4\n", encoding="utf-8")
        ArtifactStore(temporary).import_local_validated(project_id, alpha, alpha.name)
        with patch("routers.artifacts.CACHE_DIR", temporary):
            response = signed_request(
                "POST",
                "/api/artifacts/classify",
                {"project_id": project_id},
            )

    assert response.status_code == 200
    artifact = response.json()["data"]["artifacts"][0]
    assert artifact["kind"] == "ALPHA_VECTOR"
    assert artifact["original_name"] == "alpha.tsv"
    assert "path" not in artifact
