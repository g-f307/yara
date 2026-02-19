"""
Alpha Diversity Router
=======================

POST /api/alpha/analyze — Análise de diversidade alfa com boxplot Plotly
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import pandas as pd

from analysis.alpha_diversity import AlphaDiversityAnalyzer

router = APIRouter(prefix="/api/alpha", tags=["alpha"])


class AlphaRequest(BaseModel):
    data: List[Dict[str, Any]]
    metric: str = "shannon"
    group_col: Optional[str] = None


@router.post("/analyze")
async def analyze_alpha(request: AlphaRequest) -> Dict[str, Any]:
    """
    Calcula diversidade alfa e retorna estatísticas + boxplot Plotly.
    """
    df = pd.DataFrame(request.data)
    analyzer = AlphaDiversityAnalyzer(df)

    # Estatísticas
    stats = analyzer.get_summary_stats(request.metric)
    interpretation = analyzer.interpret_value(stats['mean'], request.metric)

    result: Dict[str, Any] = {
        "stats": stats,
        "interpretation": interpretation,
        "metric": request.metric,
        "n_samples": len(df),
    }

    # Comparação entre grupos (se solicitada)
    if request.group_col and request.group_col in df.columns:
        try:
            comparison = analyzer.compare_groups(request.group_col, request.metric)
            result["comparison"] = comparison
        except Exception as e:
            result["comparison_error"] = str(e)

    # Plotly spec — boxplot por grupo ou geral
    if request.group_col and request.group_col in df.columns:
        groups = df[request.group_col].unique().tolist()
        traces = []
        for group in groups:
            group_values = df[df[request.group_col] == group][request.metric].dropna().tolist()
            traces.append({
                "type": "box",
                "y": [float(v) for v in group_values],
                "name": str(group),
                "boxmean": True,
            })
        plotly_spec = {
            "data": traces,
            "layout": {
                "title": f"Diversidade Alfa — {request.metric}",
                "yaxis": {"title": request.metric.capitalize()},
                "xaxis": {"title": request.group_col},
                "template": "plotly_white",
            },
        }
    else:
        values = df[request.metric].dropna().tolist()
        plotly_spec = {
            "data": [{
                "type": "box",
                "y": [float(v) for v in values],
                "name": request.metric,
                "boxmean": True,
            }],
            "layout": {
                "title": f"Diversidade Alfa — {request.metric}",
                "yaxis": {"title": request.metric.capitalize()},
                "template": "plotly_white",
            },
        }

    return {"data": result, "plotly_spec": plotly_spec}
