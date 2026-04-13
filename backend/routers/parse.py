"""
Parse Router
=============

POST /api/parse — Validação e parsing de arquivos QIIME 2
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import pandas as pd
import tempfile
import os
from pathlib import Path

from analysis.qiime_parser import QIIME2Parser, load_qiime2_data

router = APIRouter(prefix="/api/parse", tags=["parse"])

ALLOWED_EXTENSIONS = {'.tsv', '.csv', '.qzv', '.qza', '.biom'}
QIIME_ZIP_EXTENSIONS = {'.qzv', '.qza'}
MAX_FILE_SIZE_BYTES = int(os.getenv("MAX_FILE_SIZE_BYTES", str(500 * 1024 * 1024)))


class ProjectValidationRequest(BaseModel):
    project_id: str


def _detect_analysis_types(df: pd.DataFrame) -> List[str]:
    detected: List[str] = []
    lower_cols = [str(col).lower() for col in df.columns]

    if any(col in ["shannon", "observed_features", "faith_pd", "chao1", "pielou_e", "simpson"] for col in lower_cols):
        detected.append("alpha")

    if df.shape[0] == df.shape[1] and df.shape[0] > 1:
        detected.append("beta")

    if any("taxon" in col or "taxa" in col for col in lower_cols):
        detected.append("taxonomy")

    if any(col.isdigit() for col in lower_cols):
        detected.append("rarefaction")

    return detected


def _read_table_for_validation(path: Path) -> pd.DataFrame:
    if path.suffix == ".csv":
        return pd.read_csv(path, index_col=0)

    if path.suffix in [".qzv", ".qza"]:
        if not path.read_bytes().startswith(b'PK\x03\x04'):
            raise ValueError("arquivo QIIME 2 inválido: conteúdo não é ZIP.")
        df = load_qiime2_data(str(path), data_type="auto")
        if df is None:
            raise ValueError("não foi possível extrair uma tabela legível do artefato QIIME 2.")
        return df

    return pd.read_csv(path, sep="\t", index_col=0, comment="#")


@router.post("")
async def parse_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Valida e parseia arquivo enviado.
    Retorna preview dos dados e informações do arquivo.
    """
    # Validar extensão
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensão '{ext}' não suportada. Aceitas: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Salvar temporariamente
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo excede o limite de {MAX_FILE_SIZE_BYTES} bytes."
            )

        if ext in QIIME_ZIP_EXTENSIONS and not content.startswith(b'PK\x03\x04'):
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo {ext} inválido: o conteúdo não é um ZIP QIIME 2 válido."
            )

        tmp.write(content)
        tmp.close()

        # Detectar tipo e carregar
        df = load_qiime2_data(tmp.name, data_type='auto')

        if df is None:
            raise HTTPException(status_code=422, detail="Não foi possível parsear o arquivo.")

        # Preview
        preview = df.head(10).to_dict(orient='records')
        columns = list(df.columns)
        shape = {'rows': int(df.shape[0]), 'cols': int(df.shape[1])}

        return {
            "data": {
                "filename": file.filename,
                "extension": ext,
                "shape": shape,
                "columns": columns,
                "preview": preview,
            },
            "plotly_spec": None,
        }

    finally:
        tmp.close()
        os.unlink(tmp.name)


@router.post("/validate")
async def validate_project_data(request: ProjectValidationRequest) -> Dict[str, Any]:
    """
    Valida os arquivos sincronizados de um projeto e retorna um diagnóstico
    resumido para orientar o usuário antes das análises.
    """
    from utils.project_manager import ProjectManager

    project_dir = ProjectManager.get_project_dir(request.project_id)
    if not project_dir.exists():
        return {
            "data": {
                "valid": False,
                "detected_types": [],
                "warnings": [],
                "errors": ["Arquivos do projeto ainda não foram sincronizados no Python Core."],
                "sample_count": 0,
                "column_names": [],
                "files": [],
            },
            "plotly_spec": None,
        }

    detected_types = set()
    warnings: List[str] = []
    errors: List[str] = []
    column_names = set()
    sample_count = 0
    files_info: List[Dict[str, Any]] = []

    candidate_files = [
        path for path in project_dir.iterdir()
        if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS
    ]

    if not candidate_files:
        errors.append("Nenhum arquivo QIIME 2 ou tabela TSV/CSV reconhecida no projeto.")

    for path in candidate_files:
        try:
            if path.stat().st_size > MAX_FILE_SIZE_BYTES:
                warnings.append(f"{path.name}: arquivo acima do limite configurado e pode falhar no processamento.")
                continue

            df = _read_table_for_validation(path)
            file_types = _detect_analysis_types(df)
            detected_types.update(file_types)
            sample_count = max(sample_count, int(df.shape[0]))
            column_names.update(str(col) for col in df.columns)

            if df.shape[0] < 3:
                warnings.append(f"{path.name}: apenas {df.shape[0]} amostra(s); testes estatísticos podem não ser adequados.")

            if not file_types:
                warnings.append(f"{path.name}: tabela legível, mas o tipo de análise não foi reconhecido automaticamente.")

            files_info.append({
                "name": path.name,
                "rows": int(df.shape[0]),
                "columns": int(df.shape[1]),
                "detected_types": file_types,
            })
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")

    if not detected_types and not errors:
        warnings.append("Nenhum tipo de análise reconhecido. Verifique se os arquivos foram exportados corretamente do QIIME 2.")

    return {
        "data": {
            "valid": len(errors) == 0,
            "detected_types": sorted(detected_types),
            "warnings": warnings,
            "errors": errors,
            "sample_count": sample_count,
            "column_names": sorted(column_names),
            "files": files_info,
        },
        "plotly_spec": None,
    }
