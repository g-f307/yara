"""Classificação determinística de artefatos já aprovados pelo manifesto seguro."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import zipfile
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any

from security.artifact_pipeline import ArtifactRecord, ArtifactStore, safe_project_dir

CLASSIFIER_VERSION = "1.0.0"


class ArtifactKind(StrEnum):
    FEATURE_TABLE = "FEATURE_TABLE"
    TAXONOMY = "TAXONOMY"
    METADATA = "METADATA"
    PHYLOGENETIC_TREE = "PHYLOGENETIC_TREE"
    ALPHA_VECTOR = "ALPHA_VECTOR"
    DISTANCE_MATRIX = "DISTANCE_MATRIX"
    PCOA_ORDINATION = "PCOA_ORDINATION"
    RAREFACTION_CURVE = "RAREFACTION_CURVE"
    UNKNOWN = "UNKNOWN"


class CompatibilityStatus(StrEnum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"


class ArtifactCatalogError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.public_message = message


@dataclass(frozen=True)
class SemanticArtifact:
    id: str
    original_name: str
    physical_name: str
    extension: str
    sha256: str
    size: int
    status: str
    kind: str
    semantic_type: str | None
    format: str | None
    qiime_uuid: str | None
    qiime_version: str | None
    classifier_version: str
    confidence: float
    metadata: dict[str, Any]
    selected: bool


@dataclass(frozen=True)
class ArtifactCompatibility:
    source_artifact_id: str
    target_artifact_id: str
    status: str
    reason_code: str
    reason_message: str


def _stable_ids_hash(values: set[str]) -> str | None:
    if not values:
        return None
    normalized = "\n".join(sorted(values)).encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def _read_table(path: Path, extension: str) -> tuple[list[str], list[list[str]]]:
    delimiter = "," if extension == ".csv" else "\t"
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source, delimiter=delimiter)
        rows = [row for row in reader if row and not row[0].startswith("#")]
    if not rows:
        return [], []
    return [value.strip() for value in rows[0]], rows[1:]


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _classify_table(path: Path, record: ArtifactRecord) -> SemanticArtifact:
    columns, rows = _read_table(path, record.extension)
    lower = [column.casefold() for column in columns]
    first_column = lower[0] if lower else ""
    row_ids = {row[0].strip() for row in rows if row and row[0].strip()}
    column_ids = {column for column in columns[1:] if column}
    metadata: dict[str, Any] = {
        "columns": columns[:100],
        "row_count": len(rows),
        "row_ids_hash": _stable_ids_hash(row_ids),
        "column_ids_hash": _stable_ids_hash(column_ids),
    }
    alpha_names = {
        "shannon", "observed_features", "faith_pd", "chao1", "pielou_e", "simpson"
    }
    sample_names = {"sample-id", "sampleid", "#sampleid", "sample id"}

    if any("taxon" in column or "taxa" in column for column in lower):
        kind, confidence = ArtifactKind.TAXONOMY, 0.98
    elif any(column in alpha_names for column in lower):
        kind, confidence = ArtifactKind.ALPHA_VECTOR, 0.98
    elif any(column.isdigit() for column in lower):
        kind, confidence = ArtifactKind.RAREFACTION_CURVE, 0.96
    elif first_column in sample_names and any(
        not _is_number(value)
        for row in rows[:50]
        for value in row[1:]
        if value.strip()
    ):
        kind, confidence = ArtifactKind.METADATA, 0.95
    elif len(rows) > 1 and len(columns) - 1 == len(rows) and all(
        len(row) == len(columns) and all(_is_number(value) for value in row[1:])
        for row in rows[:50]
    ):
        kind, confidence = ArtifactKind.DISTANCE_MATRIX, 0.96
    elif rows and all(
        all(_is_number(value) for value in row[1:] if value.strip())
        for row in rows[:50]
    ):
        kind, confidence = ArtifactKind.FEATURE_TABLE, 0.8
    else:
        kind, confidence = ArtifactKind.UNKNOWN, 0.0
    return _semantic(record, kind, confidence, metadata=metadata)


def _qiime_metadata(path: Path) -> tuple[str | None, str | None, str | None, str | None]:
    try:
        with zipfile.ZipFile(path) as archive:
            names = [PurePosixPath(name) for name in archive.namelist()]
            roots = sorted({name.parts[0] for name in names if name.parts})
            if len(roots) != 1:
                return None, None, None, None
            root = roots[0]
            metadata_text = archive.read(f"{root}/metadata.yaml").decode("utf-8", "replace")
            version_text = archive.read(f"{root}/VERSION").decode("utf-8", "replace")
    except (KeyError, OSError, zipfile.BadZipFile):
        return None, None, None, None
    semantic_type = next(
        (line.split(":", 1)[1].strip() for line in metadata_text.splitlines() if line.startswith("type:")),
        None,
    )
    data_format = next(
        (line.split(":", 1)[1].strip() for line in metadata_text.splitlines() if line.startswith("format:")),
        None,
    )
    framework = next(
        (line.split(":", 1)[1].strip() for line in version_text.splitlines() if line.startswith("framework:")),
        None,
    )
    return root, semantic_type, data_format, framework


def _kind_from_semantic_type(value: str | None) -> ArtifactKind:
    lowered = (value or "").casefold()
    if "featuretable" in lowered or "table" in lowered:
        return ArtifactKind.FEATURE_TABLE
    if "taxonomy" in lowered or "featuredata[taxonomy]" in lowered:
        return ArtifactKind.TAXONOMY
    if "phylogeny" in lowered:
        return ArtifactKind.PHYLOGENETIC_TREE
    if "distance" in lowered:
        return ArtifactKind.DISTANCE_MATRIX
    if "pcoa" in lowered or "ordination" in lowered:
        return ArtifactKind.PCOA_ORDINATION
    if "alphadiversity" in lowered:
        return ArtifactKind.ALPHA_VECTOR
    return ArtifactKind.UNKNOWN


def _semantic(
    record: ArtifactRecord,
    kind: ArtifactKind,
    confidence: float,
    *,
    semantic_type: str | None = None,
    data_format: str | None = None,
    qiime_uuid: str | None = None,
    qiime_version: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> SemanticArtifact:
    return SemanticArtifact(
        **asdict(record),
        kind=kind,
        semantic_type=semantic_type,
        format=data_format,
        qiime_uuid=qiime_uuid,
        qiime_version=qiime_version,
        classifier_version=CLASSIFIER_VERSION,
        confidence=confidence,
        metadata=metadata or {},
        selected=False,
    )


def classify_artifact(path: Path, record: ArtifactRecord) -> SemanticArtifact:
    if record.extension in {".tsv", ".csv"}:
        return _classify_table(path, record)
    if record.extension == ".biom":
        return _semantic(record, ArtifactKind.FEATURE_TABLE, 0.95, data_format="BIOM")
    if record.extension in {".qza", ".qzv"}:
        qiime_uuid, semantic_type, data_format, version = _qiime_metadata(path)
        kind = _kind_from_semantic_type(semantic_type)
        return _semantic(
            record,
            kind,
            1.0 if kind != ArtifactKind.UNKNOWN else 0.4,
            semantic_type=semantic_type,
            data_format=data_format,
            qiime_uuid=qiime_uuid,
            qiime_version=version,
        )
    return _semantic(record, ArtifactKind.UNKNOWN, 0.0)


class SemanticCatalog:
    def __init__(self, storage_path: str | Path) -> None:
        self.storage_path = Path(storage_path)
        self.store = ArtifactStore(storage_path)

    def classify_project(self, project_id: str) -> list[SemanticArtifact]:
        project_dir = safe_project_dir(self.storage_path, project_id)
        artifacts = [
            classify_artifact(project_dir / record.physical_name, record)
            for record in self.store.valid_records(project_id)
            if (project_dir / record.physical_name).is_file()
        ]
        selections = self._load_selections(project_dir)
        artifacts = [
            replace(item, selected=selections.get(item.kind) == item.id)
            for item in artifacts
        ]
        self._save(project_dir, artifacts)
        return artifacts

    def _selection_path(self, project_dir: Path) -> Path:
        return project_dir / ".artifact-selections.json"

    def _load_selections(self, project_dir: Path) -> dict[str, str]:
        try:
            value = json.loads(self._selection_path(project_dir).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return {
            str(kind): str(artifact_id)
            for kind, artifact_id in value.items()
            if isinstance(kind, str) and isinstance(artifact_id, str)
        } if isinstance(value, dict) else {}

    def select_artifact(self, project_id: str, artifact_id: str) -> SemanticArtifact:
        project_dir = safe_project_dir(self.storage_path, project_id)
        artifacts = self.classify_project(project_id)
        selected = next((item for item in artifacts if item.id == artifact_id), None)
        if selected is None:
            raise ArtifactCatalogError(
                "ARTIFACT_NOT_FOUND",
                "O artefato informado não pertence ao projeto ou não está disponível.",
            )
        if selected.kind == ArtifactKind.UNKNOWN:
            raise ArtifactCatalogError(
                "INVALID_FILE",
                "Um artefato sem classificação não pode ser selecionado para análise.",
            )
        selections = self._load_selections(project_dir)
        selections[selected.kind] = selected.id
        target = self._selection_path(project_dir)
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(selections, indent=2), encoding="utf-8")
        os.replace(temporary, target)
        return replace(selected, selected=True)

    def _save(self, project_dir: Path, artifacts: list[SemanticArtifact]) -> None:
        target = project_dir / ".artifact-catalog.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(
            json.dumps([asdict(item) for item in artifacts], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary, target)

    def compatibility(self, project_id: str) -> list[ArtifactCompatibility]:
        artifacts = self.classify_project(project_id)
        result: list[ArtifactCompatibility] = []
        by_kind: dict[str, list[SemanticArtifact]] = {}
        for artifact in artifacts:
            by_kind.setdefault(artifact.kind, []).append(artifact)
        for candidates in by_kind.values():
            if (
                len(candidates) > 1
                and candidates[0].kind != ArtifactKind.UNKNOWN
                and not any(candidate.selected for candidate in candidates)
            ):
                for candidate in candidates:
                    for other in candidates:
                        if candidate.id < other.id:
                            result.append(ArtifactCompatibility(
                                candidate.id,
                                other.id,
                                CompatibilityStatus.AMBIGUOUS,
                                "MULTIPLE_ROLE_CANDIDATES",
                                "Existem múltiplos artefatos candidatos para o mesmo papel científico.",
                            ))
        feature_tables = by_kind.get(ArtifactKind.FEATURE_TABLE, [])
        for feature_table in feature_tables:
            for target_kind, source_hash_key, target_hash_key, reason_prefix in (
                (ArtifactKind.METADATA, "column_ids_hash", "row_ids_hash", "SAMPLE_IDS"),
                (ArtifactKind.TAXONOMY, "row_ids_hash", "row_ids_hash", "FEATURE_IDS"),
            ):
                for target in by_kind.get(target_kind, []):
                    source_hash = feature_table.metadata.get(source_hash_key)
                    target_hash = target.metadata.get(target_hash_key)
                    comparable = bool(source_hash and target_hash)
                    matches = comparable and source_hash == target_hash
                    status = (
                        CompatibilityStatus.COMPATIBLE
                        if matches
                        else CompatibilityStatus.INCOMPATIBLE
                        if comparable
                        else CompatibilityStatus.UNKNOWN
                    )
                    message = {
                        CompatibilityStatus.COMPATIBLE: "Os identificadores dos artefatos são compatíveis.",
                        CompatibilityStatus.INCOMPATIBLE: "Os identificadores dos artefatos não correspondem.",
                        CompatibilityStatus.UNKNOWN: "Não foi possível comparar os identificadores dos artefatos.",
                    }[status]
                    result.append(ArtifactCompatibility(
                        feature_table.id,
                        target.id,
                        status,
                        f"{reason_prefix}_{status}",
                        message,
                    ))
        return result

    def select_path(self, project_id: str, requested_type: str) -> Path:
        mapping = {
            "alpha": ArtifactKind.ALPHA_VECTOR,
            "beta": ArtifactKind.DISTANCE_MATRIX,
            "metadata": ArtifactKind.METADATA,
            "taxonomy": ArtifactKind.TAXONOMY,
            "rarefaction": ArtifactKind.RAREFACTION_CURVE,
        }
        expected = mapping.get(requested_type)
        candidates = [item for item in self.classify_project(project_id) if item.kind == expected]
        if not candidates:
            raise ArtifactCatalogError(
                "ARTIFACT_NOT_FOUND",
                f"Nenhum artefato compatível foi identificado para a análise de {requested_type}.",
            )
        if len(candidates) > 1:
            selected = [item for item in candidates if item.selected]
            if len(selected) == 1:
                return safe_project_dir(self.storage_path, project_id) / selected[0].physical_name
            raise ArtifactCatalogError(
                "AMBIGUOUS_ARTIFACT",
                "Existem múltiplos artefatos compatíveis. Selecione explicitamente o arquivo desejado.",
            )
        return safe_project_dir(self.storage_path, project_id) / candidates[0].physical_name
