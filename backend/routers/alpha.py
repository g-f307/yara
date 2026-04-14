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
    project_id: str
    metric: str = "shannon"
    group_col: Optional[str] = None


@router.post("/analyze")
async def analyze_alpha(request: AlphaRequest) -> Dict[str, Any]:
    """
    Calcula diversidade alfa e retorna estatísticas + boxplot Plotly.
    """
    from utils.project_manager import ProjectManager
    
    try:
        df = ProjectManager.get_project_data(request.project_id, 'alpha')
    except Exception as e:
        return {"error": str(e), "plotly_spec": None}
        
    # Join metadata if a group column is requested
    if request.group_col:
        meta = ProjectManager.get_project_metadata(request.project_id)
        if meta is not None and request.group_col in meta.columns:
            df = df.join(meta[[request.group_col]], how='left')

    try:
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

        outliers = analyzer.detect_outliers(request.metric)
        result["outliers"] = outliers

        # Comparação entre grupos (se solicitada)
        if request.group_col and request.group_col in df.columns:
            try:
                comparison = analyzer.compare_groups(request.group_col, request.metric)
                result["comparison"] = comparison
            except Exception as e:
                result["comparison_error"] = str(e)
    except Exception as e:
        return {"error": str(e), "plotly_spec": None}

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
        outlier_ids = {o["sample_id"] for o in result.get("outliers", {}).get("outliers", [])}
        if outlier_ids:
            outlier_df = df[df.index.astype(str).isin(outlier_ids)]
            traces.append({
                "type": "scatter",
                "mode": "markers",
                "x": outlier_df[request.group_col].astype(str).tolist(),
                "y": [float(v) for v in outlier_df[request.metric].dropna().tolist()],
                "name": "Outliers",
                "marker": {"color": "#ef4444", "size": 11, "symbol": "x"},
                "hovertemplate": "<b>%{text}</b><br>%{y:.4f}<extra></extra>",
                "text": outlier_df.index.astype(str).tolist(),
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
        traces = [{
                "type": "box",
                "y": [float(v) for v in values],
                "name": request.metric,
                "boxmean": True,
        }]
        outlier_ids = {o["sample_id"] for o in result.get("outliers", {}).get("outliers", [])}
        if outlier_ids:
            outlier_df = df[df.index.astype(str).isin(outlier_ids)]
            traces.append({
                "type": "scatter",
                "mode": "markers",
                "x": [request.metric] * len(outlier_df),
                "y": [float(v) for v in outlier_df[request.metric].dropna().tolist()],
                "name": "Outliers",
                "marker": {"color": "#ef4444", "size": 11, "symbol": "x"},
                "hovertemplate": "<b>%{text}</b><br>%{y:.4f}<extra></extra>",
                "text": outlier_df.index.astype(str).tolist(),
            })
        plotly_spec = {
            "data": traces,
            "layout": {
                "title": f"Diversidade Alfa — {request.metric}",
                "yaxis": {"title": request.metric.capitalize()},
                "template": "plotly_white",
            },
        }

    return {"data": result, "plotly_spec": plotly_spec}
