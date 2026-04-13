"""
Statistics Router
==================

POST /api/statistics/compare — Kruskal-Wallis ou Mann-Whitney entre grupos
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import pandas as pd

from analysis.statistics import calculate_kruskal_wallis, calculate_mann_whitney, get_group_stats

router = APIRouter(prefix="/api/statistics", tags=["statistics"])


class StatisticsRequest(BaseModel):
    data: Optional[List[Dict[str, Any]]] = None
    project_id: Optional[str] = None
    group_col: Optional[str] = None
    metric_col: Optional[str] = None
    test: str = "kruskal"  # "kruskal" ou "mann_whitney"
    group1: Optional[str] = None
    group2: Optional[str] = None


@router.post("/compare")
async def compare_groups(request: StatisticsRequest) -> Dict[str, Any]:
    """
    Executa teste estatístico (Kruskal-Wallis ou Mann-Whitney)
    e retorna resultado + boxplot Plotly.
    """
    if request.data:
        df = pd.DataFrame(request.data)
    elif request.project_id:
        from utils.project_manager import ProjectManager

        try:
            df = ProjectManager.get_project_data(request.project_id, 'alpha')
            meta = ProjectManager.get_project_metadata(request.project_id)
            if meta is not None and request.group_col in meta.columns:
                df = df.join(meta[[request.group_col]], how='left')
        except Exception as e:
            return {"data": {"success": False, "error": str(e)}, "plotly_spec": None}
    else:
        return {
            "data": {"success": False, "error": "Informe data ou project_id para executar a estatística."},
            "plotly_spec": None,
        }

    metric_col = request.metric_col
    if not metric_col:
        metric_col = next((col for col in ["shannon", "simpson", "chao1", "observed_features", "faith_pd"] if col in df.columns), None)
        if not metric_col:
            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            metric_col = numeric_cols[0] if numeric_cols else None

    group_col = request.group_col
    if not group_col:
        lower_to_col = {str(col).lower(): col for col in df.columns}
        group_col = next(
            (lower_to_col[name] for name in ["grupo", "group", "tratamento", "treatment", "condition"] if name in lower_to_col),
            None,
        )
        if not group_col:
            group_col = next((col for col in df.columns if col != metric_col and not pd.api.types.is_numeric_dtype(df[col])), None)

    if not group_col or group_col not in df.columns:
        return {
            "data": {"success": False, "error": "Coluna de grupos não encontrada. Informe group_col, por exemplo 'Grupo'."},
            "plotly_spec": None,
        }

    if not metric_col or metric_col not in df.columns:
        return {
            "data": {"success": False, "error": "Métrica não encontrada. Informe metric_col, por exemplo 'shannon'."},
            "plotly_spec": None,
        }

    if request.test == "mann_whitney" and request.group1 and request.group2:
        result = calculate_mann_whitney(
            df, group_col, request.group1, request.group2, metric_col
        )
    else:
        result = calculate_kruskal_wallis(df, group_col, metric_col)

    # Plotly boxplot por grupo
    groups = df[group_col].unique().tolist()
    traces = []
    for group in groups:
        values = df[df[group_col] == group][metric_col].dropna().tolist()
        traces.append({
            "type": "box",
            "y": [float(v) for v in values],
            "name": str(group),
            "boxmean": True,
        })

    # Anotar p-value no título
    p_text = ""
    if result.get("success") and "p_value" in result:
        p = result["p_value"]
        sig = "✅ Significativo" if result["significant"] else "❌ Não significativo"
        p_text = f" (p={p:.4f} — {sig})"

    plotly_spec = {
        "data": traces,
        "layout": {
            "title": f"{result.get('test', 'Teste')} — {metric_col}{p_text}",
            "yaxis": {"title": metric_col.capitalize()},
            "xaxis": {"title": group_col},
            "template": "plotly_white",
        },
    }

    return {"data": result, "plotly_spec": plotly_spec}
