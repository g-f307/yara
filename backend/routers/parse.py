"""
Parse Router
=============

POST /api/parse — Validação e parsing de arquivos QIIME 2
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any
import pandas as pd
import tempfile
import os
from pathlib import Path

from analysis.qiime_parser import QIIME2Parser, load_qiime2_data

router = APIRouter(prefix="/api/parse", tags=["parse"])

ALLOWED_EXTENSIONS = {'.tsv', '.csv', '.qzv', '.qza', '.biom'}


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
        os.unlink(tmp.name)
