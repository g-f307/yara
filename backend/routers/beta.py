"""
Beta Diversity Router
======================

POST /api/beta/pcoa     — PCoA com Bray-Curtis ou Jaccard
POST /api/beta/distances — Matriz de distâncias
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import pandas as pd

from analysis.beta_diversity import BetaDiversityAnalyzer

router = APIRouter(prefix="/api/beta", tags=["beta"])


class BetaRequest(BaseModel):
    project_id: str
    group_col: Optional[str] = None


@router.post("/pcoa")
async def compute_pcoa(request: BetaRequest) -> Dict[str, Any]:
    """
    Calcula PCoA a partir de matriz de distâncias de um projeto.
    """
    from utils.project_manager import ProjectManager

    try:
        dm = ProjectManager.get_project_data(request.project_id, 'beta')
    except Exception as e:
        return {"error": str(e), "plotly_spec": None}

    try:
        analyzer = BetaDiversityAnalyzer(dm)
        coords = analyzer.calculate_pcoa(n_components=3)
        stats = analyzer.get_distance_stats()

        # Construir traces Plotly
        if request.group_col:
            meta_df = ProjectManager.get_project_metadata(request.project_id)
            if meta_df is not None and request.group_col in meta_df.columns:
                merged = coords.join(meta_df[[request.group_col]], how='left')
                groups = merged[request.group_col].unique().tolist()
        
                traces = []
                for group in groups:
                    subset = merged[merged[request.group_col] == group]
                    traces.append({
                        "type": "scatter",
                        "mode": "markers",
                        "x": subset['PC1'].tolist(),
                        "y": subset['PC2'].tolist(),
                        "name": str(group),
                        "text": subset.index.tolist(),
                        "marker": {"size": 10},
                    })
            else:
                traces = [{
                    "type": "scatter",
                    "mode": "markers+text",
                    "x": coords['PC1'].tolist(),
                    "y": coords['PC2'].tolist(),
                    "text": coords.index.tolist(),
                    "textposition": "top center",
                    "marker": {"size": 10},
                }]
        else:
            traces = [{
                "type": "scatter",
                "mode": "markers+text",
                "x": coords['PC1'].tolist(),
                "y": coords['PC2'].tolist(),
                "text": coords.index.tolist(),
                "textposition": "top center",
                "marker": {"size": 10},
            }]

        plotly_spec = {
            "data": traces,
            "layout": {
                "title": "PCoA — Diversidade Beta",
                "xaxis": {"title": "PC1"},
                "yaxis": {"title": "PC2"},
                "template": "plotly_white",
                "hovermode": "closest",
            },
        }

        return {
            "data": {
                "coordinates": coords.reset_index().to_dict(orient='records'),
                "distance_stats": stats,
            },
            "plotly_spec": plotly_spec,
        }
    except Exception as e:
        return {"error": str(e), "plotly_spec": None}


@router.post("/distances")
async def get_distances(request: BetaRequest) -> Dict[str, Any]:
    """
    Retorna estatísticas da matriz de distâncias de um projeto.
    """
    from utils.project_manager import ProjectManager

    try:
        dm = ProjectManager.get_project_data(request.project_id, 'beta')
    except Exception as e:
        return {"error": str(e), "plotly_spec": None}

    try:
        analyzer = BetaDiversityAnalyzer(dm)
        stats = analyzer.get_distance_stats()

        # Heatmap
        plotly_spec = {
            "data": [{
                "type": "heatmap",
                "z": dm.values.tolist(),
                "x": dm.index.tolist(),
                "y": dm.columns.tolist(),
                "colorscale": "Viridis",
            }],
            "layout": {
                "title": "Matriz de Distâncias",
                "template": "plotly_white",
            },
        }

        return {
            "data": {
                "stats": stats,
                "matrix": dm.values.tolist(),
                "sample_ids": dm.index.tolist(),
            },
            "plotly_spec": plotly_spec,
        }
    except Exception as e:
        return {"error": str(e), "plotly_spec": None}
