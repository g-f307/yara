"""Metadata imutável, templates MIxS/MIMARKS e prontidão explicável."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
import uuid
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from artifacts.catalog import ArtifactKind, SemanticCatalog
from security.artifact_pipeline import safe_project_dir

RULES_VERSION = "1.0.0"
TEMPLATE_VERSION = "MIxS-MIMARKS-guidance-1.0.0"
MAX_ROWS = 5_000
MAX_COLUMNS = 200
MAX_COLUMN_NAME_CHARS = 256
MAX_CELL_CHARS = 10_000
MAX_TOTAL_CHARS = 5_000_000


class MetadataError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.public_message = message


@dataclass(frozen=True)
class TemplateField:
    name: str
    description: str
    data_type: str
    unit: str | None
    requirement: str
    vocabulary: list[str]


@dataclass(frozen=True)
class MetadataTemplate:
    id: str
    name: str
    description: str
    version: str
    fields: list[TemplateField]


@dataclass(frozen=True)
class MetadataVersion:
    id: str
    project_id: str
    artifact_id: str
    parent_version_id: str | None
    sha256: str
    schema: dict[str, Any]
    source: str
    template_id: str
    template_version: str
    created_by_user_id: str | None
    created_at: str
    physical_name: str


@dataclass(frozen=True)
class MetadataDiagnostic:
    severity: str
    code: str
    column_name: str | None
    affected_samples: list[str]
    message: str
    suggestion: str


COMMON_FIELDS = [
    TemplateField("sample-id", "Identificador único da amostra.", "string", None, "MINIMUM", []),
    TemplateField("collection_date", "Data de coleta no padrão ISO 8601.", "date", None, "RECOMMENDED", []),
    TemplateField("latitude", "Latitude decimal entre -90 e 90.", "number", "degree", "RECOMMENDED", []),
    TemplateField("longitude", "Longitude decimal entre -180 e 180.", "number", "degree", "RECOMMENDED", []),
    TemplateField("env_biome", "Bioma ambiental segundo vocabulário controlado.", "category", None, "MINIMUM", []),
    TemplateField("env_feature", "Característica ambiental da amostra.", "category", None, "RECOMMENDED", []),
    TemplateField("env_material", "Material ambiental coletado.", "category", None, "RECOMMENDED", []),
]
SAMPLE_ID_FIELD = COMMON_FIELDS[0]


def _template(identifier: str, name: str, description: str, fields: list[TemplateField]) -> MetadataTemplate:
    return MetadataTemplate(identifier, name, description, TEMPLATE_VERSION, COMMON_FIELDS + fields)


TEMPLATES = {
    item.id: item
    for item in (
        MetadataTemplate(
            "generic",
            "Sem perfil ambiental",
            "Validação estrutural antes da seleção de um perfil MIxS/MIMARKS.",
            TEMPLATE_VERSION,
            [SAMPLE_ID_FIELD],
        ),
        _template("soil", "Solo", "Perfil orientativo MIxS para amostras de solo.", [
            TemplateField("ph", "Potencial hidrogeniônico do solo.", "number", None, "RECOMMENDED", []),
            TemplateField("soil_type", "Classificação do solo.", "category", None, "OPTIONAL", []),
            TemplateField("temperature", "Temperatura no momento da coleta.", "number", "°C", "OPTIONAL", []),
        ]),
        _template("rhizosphere", "Rizosfera", "Perfil orientativo MIxS para microbioma da rizosfera.", [
            TemplateField("host_taxid", "Identificador taxonômico do hospedeiro.", "string", None, "MINIMUM", []),
            TemplateField("plant_growth_stage", "Estágio de desenvolvimento vegetal.", "category", None, "RECOMMENDED", []),
            TemplateField("root_compartment", "Compartimento associado à raiz.", "category", None, "RECOMMENDED", ["rizosfera", "rizoplano", "endosfera"]),
        ]),
        _template("water", "Água", "Perfil orientativo MIxS para ambientes aquáticos.", [
            TemplateField("depth", "Profundidade da coleta.", "number", "m", "RECOMMENDED", []),
            TemplateField("salinity", "Salinidade da amostra.", "number", "PSU", "RECOMMENDED", []),
            TemplateField("temperature", "Temperatura da água.", "number", "°C", "RECOMMENDED", []),
        ]),
        _template("host", "Hospedeiro", "Perfil orientativo MIMARKS para amostras associadas a hospedeiros.", [
            TemplateField("host_taxid", "Identificador taxonômico do hospedeiro.", "string", None, "MINIMUM", []),
            TemplateField("host_subject_id", "Identificador pseudonimizado do indivíduo.", "string", None, "MINIMUM", []),
            TemplateField("body_site", "Local anatômico da coleta.", "category", None, "RECOMMENDED", []),
        ]),
        _template("gut", "Intestino", "Perfil orientativo MIMARKS para microbioma intestinal.", [
            TemplateField("host_taxid", "Identificador taxonômico do hospedeiro.", "string", None, "MINIMUM", []),
            TemplateField("host_subject_id", "Identificador pseudonimizado do indivíduo.", "string", None, "MINIMUM", []),
            TemplateField("diet", "Descrição ou categoria de dieta.", "category", None, "RECOMMENDED", []),
            TemplateField("antibiotic_use", "Uso recente de antibióticos.", "category", None, "RECOMMENDED", ["sim", "não", "desconhecido"]),
        ]),
    )
}


def _canonical_tsv(columns: list[str], rows: list[dict[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, delimiter="\t", lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({column: "" if row.get(column) is None else str(row.get(column)) for column in columns})
    return output.getvalue().encode("utf-8")


def _parse_table(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    delimiter = "," if path.suffix.casefold() == ".csv" else "\t"
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader((line for line in source if not line.startswith("#")), delimiter=delimiter)
        columns = [str(column).strip() for column in (reader.fieldnames or [])]
        rows = [
            {str(key).strip(): (value or "").strip() for key, value in row.items() if key is not None}
            for row in reader
        ]
    return columns, rows


def _sample_column(columns: list[str]) -> str | None:
    aliases = {"sample-id", "sampleid", "sample id", "#sampleid", "id"}
    return next((column for column in columns if column.casefold() in aliases), None)


def _infer_schema(columns: list[str], rows: list[dict[str, str]]) -> dict[str, Any]:
    inferred: dict[str, Any] = {"columns": [], "row_count": len(rows)}
    for column in columns:
        values = [row.get(column, "") for row in rows if row.get(column, "") != ""]
        data_type = "string"
        if values and all(_number_with_unit(value)[0] is not None for value in values):
            data_type = "number"
        elif values and all(_valid_date(value) for value in values):
            data_type = "date"
        elif values and len({value.casefold() for value in values}) <= max(20, math.ceil(len(values) * 0.25)):
            data_type = "category"
        inferred["columns"].append({"name": column, "type": data_type, "missing": len(rows) - len(values)})
    return inferred


def _number_with_unit(value: str) -> tuple[float | None, str | None]:
    match = re.fullmatch(r"\s*(-?(?:\d+(?:\.\d+)?|\.\d+))\s*([^\d\s].*)?\s*", value)
    if not match:
        return None, None
    return float(match.group(1)), match.group(2).strip() if match.group(2) else None


def _valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


class MetadataService:
    def __init__(self, storage_path: str | Path) -> None:
        self.storage_path = Path(storage_path)
        self.catalog = SemanticCatalog(storage_path)

    def templates(self) -> list[MetadataTemplate]:
        return list(TEMPLATES.values())

    def _root(self, project_id: str) -> Path:
        root = safe_project_dir(self.storage_path, project_id) / ".metadata"
        (root / "versions").mkdir(parents=True, exist_ok=True)
        return root

    def _index_path(self, project_id: str) -> Path:
        return self._root(project_id) / "index.json"

    def _load_index(self, project_id: str) -> dict[str, Any]:
        try:
            data = json.loads(self._index_path(project_id).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"active_version_id": None, "versions": []}
        return data if isinstance(data, dict) else {"active_version_id": None, "versions": []}

    def _save_index(self, project_id: str, index: dict[str, Any]) -> None:
        target = self._index_path(project_id)
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, target)

    def _metadata_artifact(self, project_id: str, artifact_id: str | None = None):
        artifacts = [item for item in self.catalog.classify_project(project_id) if item.kind == ArtifactKind.METADATA]
        if artifact_id:
            artifact = next((item for item in artifacts if item.id == artifact_id), None)
        else:
            selected = [item for item in artifacts if item.selected]
            artifact = selected[0] if len(selected) == 1 else artifacts[0] if len(artifacts) == 1 else None
        if artifact is None:
            code = "AMBIGUOUS_ARTIFACT" if len(artifacts) > 1 else "METADATA_NOT_FOUND"
            message = "Selecione explicitamente o arquivo de metadata." if len(artifacts) > 1 else "Nenhum arquivo de metadata válido foi encontrado."
            raise MetadataError(code, message)
        return artifact

    def ensure_initial_version(self, project_id: str, *, template_id: str = "generic") -> MetadataVersion:
        index = self._load_index(project_id)
        artifact = self._metadata_artifact(project_id)
        if index.get("versions"):
            active = self.active_version(project_id)
            if active.artifact_id == artifact.id:
                return active
            parent_version_id = active.id
        else:
            parent_version_id = None
        project_dir = safe_project_dir(self.storage_path, project_id)
        columns, rows = _parse_table(project_dir / artifact.physical_name)
        return self._create(
            project_id=project_id,
            artifact_id=artifact.id,
            parent_version_id=parent_version_id,
            template_id=template_id,
            columns=columns,
            rows=rows,
            source="ORIGINAL",
            created_by_user_id=None,
        )

    def list_versions(self, project_id: str) -> tuple[list[MetadataVersion], str | None]:
        index = self._load_index(project_id)
        return [MetadataVersion(**item) for item in index.get("versions", [])], index.get("active_version_id")

    def active_version(self, project_id: str) -> MetadataVersion:
        versions, active_id = self.list_versions(project_id)
        active = next((item for item in versions if item.id == active_id), None)
        if active is None:
            raise MetadataError("METADATA_VERSION_NOT_FOUND", "Nenhuma versão ativa de metadata foi encontrada.")
        return active

    def version_path(self, project_id: str, version: MetadataVersion | None = None) -> Path:
        current = version or self.ensure_initial_version(project_id)
        return self._root(project_id) / "versions" / current.physical_name

    def rows(self, project_id: str, version_id: str | None = None) -> tuple[list[str], list[dict[str, str]]]:
        versions, _ = self.list_versions(project_id)
        version = next((item for item in versions if item.id == version_id), None) if version_id else self.ensure_initial_version(project_id)
        if version is None:
            raise MetadataError("METADATA_VERSION_NOT_FOUND", "A versão de metadata informada não foi encontrada.")
        return _parse_table(self.version_path(project_id, version))

    def validate(
        self,
        project_id: str,
        *,
        template_id: str,
        columns: list[str] | None = None,
        rows: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        template = TEMPLATES.get(template_id)
        if template is None:
            raise MetadataError("METADATA_TEMPLATE_NOT_FOUND", "O template de metadata informado não existe.")
        if columns is None or rows is None:
            columns, rows = self.rows(project_id)
        columns = [str(value).strip() for value in columns]
        normalized_rows = [{column: str(row.get(column, "")).strip() for column in columns} for row in rows]
        self._validate_limits(columns, normalized_rows)
        diagnostics: list[MetadataDiagnostic] = []
        sample_column = _sample_column(columns)
        sample_ids = [row.get(sample_column, "") for row in normalized_rows] if sample_column else []

        if not sample_column:
            diagnostics.append(MetadataDiagnostic("BLOCKING", "MISSING_SAMPLE_ID_COLUMN", None, [], "A coluna de identificação das amostras não foi encontrada.", "Adicione uma coluna sample-id com valores únicos."))
        else:
            missing_ids = [f"linha {index + 2}" for index, value in enumerate(sample_ids) if not value]
            if missing_ids:
                diagnostics.append(MetadataDiagnostic("BLOCKING", "MISSING_SAMPLE_IDS", sample_column, missing_ids[:100], "Existem amostras sem identificador.", "Preencha todos os identificadores antes da análise."))
            counts = Counter(value for value in sample_ids if value)
            duplicates = sorted(value for value, count in counts.items() if count > 1)
            if duplicates:
                diagnostics.append(MetadataDiagnostic("BLOCKING", "DUPLICATE_SAMPLE_IDS", sample_column, duplicates[:100], "Existem identificadores de amostra duplicados.", "Use um identificador único para cada amostra."))
            diagnostics.extend(self._feature_compatibility(project_id, set(value for value in sample_ids if value), sample_column))

        field_by_name = {field.name.casefold(): field for field in template.fields}
        column_by_name = {column.casefold(): column for column in columns}
        for field in template.fields:
            actual = sample_column if field.name == "sample-id" else column_by_name.get(field.name.casefold())
            if actual is None and field.requirement in {"MINIMUM", "RECOMMENDED"}:
                severity = "BLOCKING" if field.requirement == "MINIMUM" else "WARNING"
                diagnostics.append(MetadataDiagnostic(severity, f"MISSING_{field.requirement}_FIELD", field.name, [], f"O campo {field.name} não está presente no template {template.name}.", f"Adicione a coluna {field.name} ou selecione outro template."))

        for column in columns:
            values = [(row.get(column, ""), row.get(sample_column, f"linha {index + 2}") if sample_column else f"linha {index + 2}") for index, row in enumerate(normalized_rows)]
            missing = [sample for value, sample in values if not value]
            if missing:
                diagnostics.append(MetadataDiagnostic("WARNING", "MISSING_VALUES", column, missing[:100], f"A coluna {column} possui {len(missing)} valor(es) ausente(s).", "Revise os valores ausentes e confirme se são aceitáveis para o método."))
            field = field_by_name.get(column.casefold())
            diagnostics.extend(self._validate_values(column, values, field))
            nonempty = [value for value, _ in values if value]
            category_count = len(set(value.casefold() for value in nonempty))
            if (
                column != sample_column
                and nonempty
                and 1 < category_count <= min(20, max(2, math.ceil(len(nonempty) * 0.5)))
            ):
                groups: dict[str, list[str]] = {}
                for value, sample in values:
                    if value:
                        groups.setdefault(value.casefold(), []).append(sample)
                small = [sample for samples in groups.values() if len(samples) < 3 for sample in samples]
                if len(groups) > 1 and small:
                    diagnostics.append(MetadataDiagnostic("WARNING", "SMALL_GROUP", column, small[:100], f"A coluna {column} possui grupo(s) com menos de três amostras.", "Avalie o poder estatístico antes de comparar os grupos."))
                variants: dict[str, set[str]] = {}
                for value in nonempty:
                    variants.setdefault(value.strip().casefold(), set()).add(value)
                inconsistent = sorted({variant for values_set in variants.values() if len(values_set) > 1 for variant in values_set})
                if inconsistent:
                    diagnostics.append(MetadataDiagnostic("WARNING", "INCONSISTENT_CATEGORIES", column, [], f"A coluna {column} contém categorias que diferem apenas em caixa ou espaços.", "Revise as categorias; nenhuma correção será aplicada automaticamente."))

        unknown = [column for column in columns if column.casefold() not in field_by_name and column != sample_column]
        for column in unknown:
            diagnostics.append(MetadataDiagnostic("INFO", "UNRECOGNIZED_FIELD", column, [], f"A coluna {column} não é reconhecida pelo template, mas será preservada.", "Confirme o significado da coluna na documentação do projeto."))
        readiness = self._readiness(diagnostics)
        return {
            "rules_version": RULES_VERSION,
            "template": asdict(template),
            "schema": _infer_schema(columns, normalized_rows),
            "diagnostics": [asdict(item) for item in diagnostics],
            "readiness": readiness,
        }

    def _validate_limits(self, columns: list[str], rows: list[dict[str, Any]]) -> None:
        if not columns or len(columns) > MAX_COLUMNS or len(rows) > MAX_ROWS:
            raise MetadataError("INVALID_METADATA", f"A metadata deve possuir de 1 a {MAX_COLUMNS} colunas e no máximo {MAX_ROWS} linhas.")
        if len(set(columns)) != len(columns) or any(not column or len(column) > MAX_COLUMN_NAME_CHARS for column in columns):
            raise MetadataError("INVALID_METADATA", "Os nomes das colunas devem ser preenchidos e únicos.")
        total_chars = 0
        for row in rows:
            for column in columns:
                value = str(row.get(column, ""))
                if len(value) > MAX_CELL_CHARS:
                    raise MetadataError("INVALID_METADATA", f"Cada célula deve possuir no máximo {MAX_CELL_CHARS} caracteres.")
                total_chars += len(value)
                if total_chars > MAX_TOTAL_CHARS:
                    raise MetadataError("INVALID_METADATA", "A metadata excede o limite total permitido para edição interativa.")

    def _feature_compatibility(self, project_id: str, sample_ids: set[str], sample_column: str) -> list[MetadataDiagnostic]:
        artifacts = self.catalog.classify_project(project_id)
        feature = next((item for item in artifacts if item.kind == ArtifactKind.FEATURE_TABLE and item.selected), None)
        if feature is None:
            candidates = [item for item in artifacts if item.kind == ArtifactKind.FEATURE_TABLE]
            feature = candidates[0] if len(candidates) == 1 else None
        if feature is None:
            return [MetadataDiagnostic("WARNING", "FEATURE_TABLE_NOT_SELECTED", sample_column, [], "Não foi possível comparar os IDs sem uma tabela de features selecionada.", "Selecione a tabela de features do projeto.")]
        expected_hash = feature.metadata.get("column_ids_hash")
        current_hash = hashlib.sha256("\n".join(sorted(sample_ids)).encode("utf-8")).hexdigest() if sample_ids else None
        if expected_hash and current_hash != expected_hash:
            return [MetadataDiagnostic("BLOCKING", "INCOMPATIBLE_SAMPLE_IDS", sample_column, sorted(sample_ids)[:100], "Os IDs da metadata não correspondem às amostras da tabela de features.", "Revise arquivos e identificadores antes de executar a análise.")]
        return []

    def _validate_values(self, column: str, values: list[tuple[str, str]], field: TemplateField | None) -> list[MetadataDiagnostic]:
        if field is None:
            return []
        invalid: list[str] = []
        invalid_units: list[str] = []
        for value, sample in values:
            if not value:
                continue
            if field.data_type == "date" and not _valid_date(value):
                invalid.append(sample)
            elif field.data_type == "number":
                number, unit = _number_with_unit(value)
                if number is None:
                    invalid.append(sample)
                elif field.name == "latitude" and not -90 <= number <= 90:
                    invalid.append(sample)
                elif field.name == "longitude" and not -180 <= number <= 180:
                    invalid.append(sample)
                elif unit and field.unit and unit.casefold() != field.unit.casefold():
                    invalid_units.append(sample)
            if field.vocabulary and value.casefold() not in {item.casefold() for item in field.vocabulary}:
                invalid.append(sample)
        result: list[MetadataDiagnostic] = []
        if invalid:
            result.append(MetadataDiagnostic("WARNING", "INVALID_FIELD_VALUE", column, sorted(set(invalid))[:100], f"A coluna {column} contém valor(es) incompatível(is) com o tipo ou vocabulário esperado.", f"Revise o campo conforme o template {field.data_type}."))
        if invalid_units:
            result.append(MetadataDiagnostic("WARNING", "INVALID_UNIT", column, sorted(set(invalid_units))[:100], f"A coluna {column} possui unidade diferente de {field.unit}.", "Converta os valores somente após revisar e confirmar a transformação."))
        return result

    def _readiness(self, diagnostics: list[MetadataDiagnostic]) -> dict[str, Any]:
        weights = {"identifiers": 30, "compatibility": 25, "minimum_fields": 25, "completeness": 10, "formats": 10}
        labels = {
            "identifiers": "Identificadores únicos e preenchidos",
            "compatibility": "Compatibilidade com a tabela de features",
            "minimum_fields": "Campos mínimos do template",
            "completeness": "Completude dos valores",
            "formats": "Tipos, unidades e categorias",
        }
        failed = {
            "identifiers": any(item.code in {"MISSING_SAMPLE_ID_COLUMN", "MISSING_SAMPLE_IDS", "DUPLICATE_SAMPLE_IDS"} for item in diagnostics),
            "compatibility": any(item.code in {"INCOMPATIBLE_SAMPLE_IDS", "FEATURE_TABLE_NOT_SELECTED"} for item in diagnostics),
            "minimum_fields": any(item.code == "MISSING_MINIMUM_FIELD" for item in diagnostics),
            "completeness": any(item.code == "MISSING_VALUES" for item in diagnostics),
            "formats": any(item.code in {"INVALID_FIELD_VALUE", "INVALID_UNIT", "INCONSISTENT_CATEGORIES"} for item in diagnostics),
        }
        items = [{"id": key, "label": labels[key], "weight": weight, "passed": not failed[key]} for key, weight in weights.items()]
        score = sum(item["weight"] for item in items if item["passed"])
        globally_ready = not any(item.severity == "BLOCKING" for item in diagnostics)
        codes = {item.code for item in diagnostics}
        return {
            "score": score,
            "ready": globally_ready,
            "rules_version": RULES_VERSION,
            "items": items,
            "method_rules": [
                {"method": "descriptive", "ready": globally_ready, "blocking_codes": sorted(code for code in codes if code in {"MISSING_SAMPLE_ID_COLUMN", "MISSING_SAMPLE_IDS", "DUPLICATE_SAMPLE_IDS", "INCOMPATIBLE_SAMPLE_IDS", "MISSING_MINIMUM_FIELD"})},
                {"method": "group_comparison", "ready": globally_ready and "SMALL_GROUP" not in codes, "blocking_codes": ["SMALL_GROUP"] if "SMALL_GROUP" in codes else []},
                {"method": "geospatial", "ready": globally_ready and "INVALID_FIELD_VALUE" not in codes, "blocking_codes": ["INVALID_FIELD_VALUE"] if "INVALID_FIELD_VALUE" in codes else []},
            ],
        }

    def create_version(self, project_id: str, artifact_id: str, parent_version_id: str | None, template_id: str, columns: list[str], rows: list[dict[str, Any]], created_by_user_id: str | None, confirmed: bool) -> MetadataVersion:
        if not confirmed:
            raise MetadataError("METADATA_CONFIRMATION_REQUIRED", "Visualize e confirme as mudanças antes de criar uma versão.")
        artifact = self._metadata_artifact(project_id, artifact_id)
        versions, active_id = self.list_versions(project_id)
        if versions and parent_version_id != active_id:
            raise MetadataError("METADATA_VERSION_CONFLICT", "A metadata foi alterada. Atualize o preview antes de confirmar.")
        return self._create(project_id, artifact.id, parent_version_id, template_id, columns, rows, "EDIT", created_by_user_id)

    def _create(self, project_id: str, artifact_id: str, parent_version_id: str | None, template_id: str, columns: list[str], rows: list[dict[str, Any]], source: str, created_by_user_id: str | None) -> MetadataVersion:
        if template_id not in TEMPLATES:
            raise MetadataError("METADATA_TEMPLATE_NOT_FOUND", "O template de metadata informado não existe.")
        self._validate_limits(columns, rows)
        payload = _canonical_tsv(columns, rows)
        version_id = str(uuid.uuid4())
        physical_name = f"{version_id}.tsv"
        target = self._root(project_id) / "versions" / physical_name
        temporary = target.with_suffix(".tmp")
        temporary.write_bytes(payload)
        os.replace(temporary, target)
        version = MetadataVersion(
            id=version_id,
            project_id=project_id,
            artifact_id=artifact_id,
            parent_version_id=parent_version_id,
            sha256=hashlib.sha256(payload).hexdigest(),
            schema=_infer_schema(columns, [{column: str(row.get(column, "")) for column in columns} for row in rows]),
            source=source,
            template_id=template_id,
            template_version=TEMPLATE_VERSION,
            created_by_user_id=created_by_user_id,
            created_at=datetime.now(UTC).isoformat(),
            physical_name=physical_name,
        )
        index = self._load_index(project_id)
        index.setdefault("versions", []).append(asdict(version))
        index["active_version_id"] = version.id
        self._save_index(project_id, index)
        return version

    def restore(self, project_id: str, version_id: str, created_by_user_id: str | None) -> MetadataVersion:
        versions, active_id = self.list_versions(project_id)
        source = next((item for item in versions if item.id == version_id), None)
        if source is None:
            raise MetadataError("METADATA_VERSION_NOT_FOUND", "A versão de metadata informada não foi encontrada.")
        columns, rows = self.rows(project_id, source.id)
        return self._create(project_id, source.artifact_id, active_id, source.template_id, columns, rows, f"RESTORE:{source.id}", created_by_user_id)

    def workspace(self, project_id: str) -> dict[str, Any]:
        active = self.ensure_initial_version(project_id)
        versions, active_id = self.list_versions(project_id)
        columns, rows = self.rows(project_id, active.id)
        validation = self.validate(project_id, template_id=active.template_id, columns=columns, rows=rows)
        return {
            "versions": [asdict(item) for item in versions],
            "active_version_id": active_id,
            "columns": columns,
            "rows": rows,
            "validation": validation,
            "templates": [asdict(item) for item in self.templates()],
        }
