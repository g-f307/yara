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
    distance_matrix: List[List[float]]
    sample_ids: List[str]
    metadata: Optional[List[Dict[str, Any]]] = None
    group_col: Optional[str] = None


@router.post("/pcoa")
async def compute_pcoa(request: BetaRequest) -> Dict[str, Any]:
    """
    Calcula PCoA a partir de matriz de distâncias.
    """
    dm = pd.DataFrame(
        request.distance_matrix,
        index=request.sample_ids,
        columns=request.sample_ids,
    )
    analyzer = BetaDiversityAnalyzer(dm)

    coords = analyzer.calculate_pcoa(n_components=3)
    stats = analyzer.get_distance_stats()

    # Construir traces Plotly
    if request.metadata and request.group_col:
        meta_df = pd.DataFrame(request.metadata)
        if 'sample-id' in meta_df.columns:
            meta_df = meta_df.set_index('sample-id')
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


@router.post("/distances")
async def get_distances(request: BetaRequest) -> Dict[str, Any]:
    """
    Retorna estatísticas da matriz de distâncias.
    """
    dm = pd.DataFrame(
        request.distance_matrix,
        index=request.sample_ids,
        columns=request.sample_ids,
    )
    analyzer = BetaDiversityAnalyzer(dm)
    stats = analyzer.get_distance_stats()

    # Heatmap
    plotly_spec = {
        "data": [{
            "type": "heatmap",
            "z": request.distance_matrix,
            "x": request.sample_ids,
            "y": request.sample_ids,
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
            "matrix": request.distance_matrix,
            "sample_ids": request.sample_ids,
        },
        "plotly_spec": plotly_spec,
    }
