"""
Quality Control Router
======================

POST /api/qc/summary — Diagnóstico de profundidade de sequenciamento por amostra
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
import pandas as pd

router = APIRouter(prefix="/api/qc", tags=["qc"])


class QCRequest(BaseModel):
    project_id: str


def _find_column(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    normalized = {str(col).strip().lower(): col for col in df.columns}
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]

    for col in df.columns:
        lower = str(col).strip().lower()
        if any(candidate in lower for candidate in candidates):
            return col
    return None


@router.post("/summary")
async def qc_summary(request: QCRequest) -> Dict[str, Any]:
    """
    Busca arquivos de QC exportados do QIIME 2 e resume reads por amostra.
    """
    from utils.project_manager import ProjectManager

    project_dir = ProjectManager.get_project_dir(request.project_id)
    if not project_dir.exists():
        return {"error": "Arquivos do projeto ainda não sincronizados.", "plotly_spec": None}

    read_candidates = [
        "forward sequence count",
        "reverse sequence count",
        "sequence count",
        "read count",
        "reads",
        "sequences",
    ]
    sample_candidates = ["sample-id", "sample id", "sampleid", "#sampleid", "id", "sample"]

    qc_df = None
    sample_col = None
    reads_col = None

    for file_path in sorted(project_dir.glob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in {".tsv", ".txt"}:
            continue

        try:
            df = pd.read_csv(file_path, sep="\t", comment="#")
        except Exception:
            continue

        candidate_reads_col = _find_column(df, read_candidates)
        candidate_sample_col = _find_column(df, sample_candidates)
        if candidate_reads_col:
            qc_df = df.copy()
            reads_col = candidate_reads_col
            sample_col = candidate_sample_col
            break

    source = "Arquivo de QC"
    if qc_df is None or reads_col is None:
        try:
            rarefaction_df = ProjectManager.get_project_data(request.project_id, "rarefaction")
            if "sample-id" in rarefaction_df.columns:
                rarefaction_df = rarefaction_df.set_index("sample-id")

            depth_cols = [col for col in rarefaction_df.columns if str(col).isdigit()]
            if not depth_cols:
                raise ValueError("Arquivo de rarefação sem colunas de profundidade.")

            depth_cols = sorted(depth_cols, key=lambda col: int(col))
            inferred_rows = []
            for sample_id, row in rarefaction_df[depth_cols].iterrows():
                available_depths = [int(col) for col in depth_cols if pd.notna(row[col])]
                if available_depths:
                    inferred_rows.append({
                        "sample_id": str(sample_id),
                        "reads": max(available_depths),
                    })

            if not inferred_rows:
                raise ValueError("Não foi possível inferir profundidade por amostra.")

            df = pd.DataFrame(inferred_rows)
            source = "Inferido das curvas de rarefação"
        except Exception:
            return {
                "error": "Nenhum arquivo de QC com contagem de reads por amostra foi encontrado.",
                "plotly_spec": None,
            }
    else:
        df = qc_df.rename(columns={reads_col: "reads"})
        if sample_col:
            df = df.rename(columns={sample_col: "sample_id"})
        else:
            df["sample_id"] = [f"Amostra {idx + 1}" for idx in range(len(df))]

    df["reads"] = pd.to_numeric(df["reads"], errors="coerce")
    df = df.dropna(subset=["reads"])
    if df.empty:
        return {"error": "A coluna de reads encontrada não possui valores numéricos válidos.", "plotly_spec": None}

    mean_reads = float(df["reads"].mean())
    std_reads = float(df["reads"].std()) if len(df) > 1 else 0.0
    df["zscore"] = (df["reads"] - mean_reads) / std_reads if std_reads > 0 else 0.0
    df["is_outlier"] = df["zscore"].abs() > 2.0

    low_threshold = max(0, mean_reads - (2 * std_reads))
    samples = df["sample_id"].astype(str).tolist()
    reads = [int(value) for value in df["reads"].tolist()]
    outlier_names = df[df["is_outlier"]]["sample_id"].astype(str).tolist()

    stats = {
        "total_samples": int(len(df)),
        "total_reads": int(df["reads"].sum()),
        "mean_reads_per_sample": mean_reads,
        "median_reads_per_sample": float(df["reads"].median()),
        "min_reads": int(df["reads"].min()),
        "max_reads": int(df["reads"].max()),
        "std_reads": std_reads,
        "low_coverage_threshold": int(low_threshold),
        "outlier_samples": int(df["is_outlier"].sum()),
        "outlier_names": outlier_names,
        "source": source,
        "per_sample": [
            {
                "sample_id": str(row["sample_id"]),
                "reads": int(row["reads"]),
                "zscore": float(row["zscore"]),
                "is_outlier": bool(row["is_outlier"]),
            }
            for _, row in df.iterrows()
        ],
    }

    colors = ["#ef4444" if is_outlier else "#7C3AED" for is_outlier in df["is_outlier"].tolist()]
    plotly_spec = {
        "data": [
            {
                "type": "bar",
                "x": samples,
                "y": reads,
                "marker": {"color": colors},
                "name": "Reads por amostra",
                "hovertemplate": "<b>%{x}</b><br>Reads: %{y:,}<extra></extra>",
            }
        ],
        "layout": {
            "title": "QC — Reads por Amostra" if source == "Arquivo de QC" else "QC — Profundidade Inferida por Amostra",
            "xaxis": {"title": "Amostra", "tickangle": -45},
            "yaxis": {"title": "Número de reads"},
            "template": "plotly_white",
            "shapes": [
                {
                    "type": "line",
                    "x0": -0.5,
                    "x1": len(df) - 0.5,
                    "y0": low_threshold,
                    "y1": low_threshold,
                    "line": {"color": "#ef4444", "dash": "dash", "width": 1.5},
                }
            ],
            "annotations": [
                {
                    "x": len(df) - 1,
                    "y": low_threshold,
                    "text": "Limiar mínimo",
                    "showarrow": False,
                    "yshift": 10,
                    "font": {"color": "#ef4444", "size": 11},
                }
            ],
        },
    }

    return {"data": stats, "plotly_spec": plotly_spec}
