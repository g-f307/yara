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
    data: List[Dict[str, Any]]
    group_col: str
    metric_col: str
    test: str = "kruskal"  # "kruskal" ou "mann_whitney"
    group1: Optional[str] = None
    group2: Optional[str] = None


@router.post("/compare")
async def compare_groups(request: StatisticsRequest) -> Dict[str, Any]:
    """
    Executa teste estatístico (Kruskal-Wallis ou Mann-Whitney)
    e retorna resultado + boxplot Plotly.
    """
    df = pd.DataFrame(request.data)

    if request.test == "mann_whitney" and request.group1 and request.group2:
        result = calculate_mann_whitney(
            df, request.group_col, request.group1, request.group2, request.metric_col
        )
    else:
        result = calculate_kruskal_wallis(df, request.group_col, request.metric_col)

    # Plotly boxplot por grupo
    groups = df[request.group_col].unique().tolist()
    traces = []
    for group in groups:
        values = df[df[request.group_col] == group][request.metric_col].dropna().tolist()
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
            "title": f"{result.get('test', 'Teste')} — {request.metric_col}{p_text}",
            "yaxis": {"title": request.metric_col.capitalize()},
            "xaxis": {"title": request.group_col},
            "template": "plotly_white",
        },
    }

    return {"data": result, "plotly_spec": plotly_spec}
