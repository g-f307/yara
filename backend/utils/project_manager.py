"""Gerenciamento seguro do cache de artefatos por projeto."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx

from security.artifact_pipeline import (
    ArtifactSecurityError,
    ArtifactStore,
    normalize_project_id,
    safe_project_dir,
)

CACHE_DIR = os.getenv("STORAGE_PATH", "./uploads")
_PROJECT_LOCKS: dict[str, tuple[asyncio.Lock, int]] = {}
_PROJECT_LOCKS_GUARD = asyncio.Lock()


@asynccontextmanager
async def _project_lock(project_id: str):
    async with _PROJECT_LOCKS_GUARD:
        lock, references = _PROJECT_LOCKS.get(
            project_id,
            (asyncio.Lock(), 0),
        )
        _PROJECT_LOCKS[project_id] = (lock, references + 1)
    try:
        async with lock:
            yield
    finally:
        async with _PROJECT_LOCKS_GUARD:
            current_lock, references = _PROJECT_LOCKS[project_id]
            if references == 1:
                del _PROJECT_LOCKS[project_id]
            else:
                _PROJECT_LOCKS[project_id] = (
                    current_lock,
                    references - 1,
                )


class ProjectManager:
    @staticmethod
    async def sync_files(
        project_id: str,
        files: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Baixa, valida e promove artefatos individualmente."""
        normalized_project_id = normalize_project_id(project_id)
        store = ArtifactStore(CACHE_DIR)
        timeout = httpx.Timeout(
            connect=store.limits.connect_timeout_seconds,
            read=store.limits.read_timeout_seconds,
            write=store.limits.read_timeout_seconds,
            pool=store.limits.connect_timeout_seconds,
        )
        results: list[dict[str, Any]] = []

        async with _project_lock(normalized_project_id):
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                for file_data in files:
                    name = file_data.get("name") or ""
                    url = file_data.get("url") or ""
                    if not name or not url:
                        results.append(
                            {
                                "name": name,
                                "status": "REJECTED",
                                "code": "MISSING_FILE_DATA",
                                "reason": "Nome e URL do arquivo são obrigatórios.",
                            }
                        )
                        continue
                    try:
                        record = await store.sync_one(
                            client,
                            normalized_project_id,
                            url,
                            name,
                        )
                        results.append(
                            {
                                "name": record.original_name,
                                "status": record.status,
                                "sha256": record.sha256,
                                "size": record.size,
                            }
                        )
                    except ArtifactSecurityError as exc:
                        results.append(
                            {
                                "name": name,
                                "status": "REJECTED",
                                "code": exc.code,
                                "reason": exc.public_message,
                            }
                        )
                    except (httpx.HTTPError, OSError):
                        results.append(
                            {
                                "name": name,
                                "status": "FAILED",
                                "code": "ARTIFACT_SYNC_FAILED",
                                "reason": "Não foi possível sincronizar o arquivo.",
                            }
                        )

        valid_count = sum(result["status"] == "VALID" for result in results)
        return {
            "status": "success" if valid_count == len(results) else "partial",
            "valid_files": valid_count,
            "details": results,
        }

    @staticmethod
    def get_project_dir(project_id: str) -> Path:
        return safe_project_dir(CACHE_DIR, project_id)

    @staticmethod
    def _valid_files(project_id: str, extensions: set[str]) -> list[Path]:
        project_dir = ProjectManager.get_project_dir(project_id)
        if not project_dir.exists():
            return []
        records = ArtifactStore(CACHE_DIR).valid_records(project_id)
        return [
            project_dir / record.physical_name
            for record in records
            if record.extension in extensions
            and (project_dir / record.physical_name).is_file()
        ]

    @staticmethod
    def has_valid_artifacts(project_id: str) -> bool:
        return bool(
            ProjectManager._valid_files(
                project_id,
                {".tsv", ".csv", ".qza", ".qzv", ".biom"},
            )
        )

    @staticmethod
    def artifact_display_name(project_id: str, physical_name: str) -> str:
        for record in ArtifactStore(CACHE_DIR).valid_records(project_id):
            if record.physical_name == physical_name:
                return record.original_name
        return "artefato"

    @staticmethod
    def get_project_data(project_id: str, data_type: str):
        from analysis.qiime_parser import load_qiime2_data

        files = ProjectManager._valid_files(project_id, {".tsv", ".qzv", ".qza"})
        if not files:
            raise FileNotFoundError(
                "Os arquivos válidos do projeto ainda não foram sincronizados."
            )

        def is_likely_type(df, requested_type: str) -> bool:
            if df is None or df.empty:
                return False
            lower_cols = [str(column).lower() for column in df.columns]
            if requested_type == "alpha":
                return any(
                    column
                    in {
                        "shannon",
                        "observed_features",
                        "faith_pd",
                        "chao1",
                        "pielou_e",
                        "simpson",
                    }
                    for column in lower_cols
                )
            if requested_type == "beta":
                return df.shape[0] == df.shape[1] and df.shape[0] > 1
            if requested_type == "taxonomy":
                return any("taxon" in column or "taxa" in column for column in lower_cols)
            if requested_type == "rarefaction":
                return any(column.isdigit() for column in lower_cols)
            return True

        for file_path in files:
            try:
                dataframe = load_qiime2_data(str(file_path), data_type=data_type)
                if is_likely_type(dataframe, data_type):
                    return dataframe
            except (ValueError, OSError):
                continue

        raise ValueError(
            f"Não foram encontrados dados válidos para a análise de {data_type}."
        )

    @staticmethod
    def get_project_metadata(project_id: str):
        import pandas as pd

        files = ProjectManager._valid_files(project_id, {".tsv"})
        for file_path in files:
            try:
                dataframe = pd.read_csv(file_path, sep="\t")
                sample_column = next(
                    (
                        column
                        for column in dataframe.columns
                        if column.lower()
                        in {"sample-id", "sampleid", "id", "#sampleid"}
                    ),
                    None,
                )
                if sample_column:
                    dataframe = dataframe.set_index(sample_column)
                return dataframe
            except (ValueError, OSError):
                continue
        return None
