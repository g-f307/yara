"""
Rarefaction Router
===================

POST /api/rarefaction/analyze — Curvas de rarefação + profundidade recomendada
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import pandas as pd

from analysis.rarefaction import RarefactionAnalyzer

router = APIRouter(prefix="/api/rarefaction", tags=["rarefaction"])


class RarefactionRequest(BaseModel):
    data: List[Dict[str, Any]]
    max_samples: int = 20


@router.post("/analyze")
async def analyze_rarefaction(request: RarefactionRequest) -> Dict[str, Any]:
    """
    Analisa curvas de rarefação e retorna estatísticas, recomendação e gráfico Plotly.
    """
    df = pd.DataFrame(request.data)

    if 'sample-id' in df.columns:
        df = df.set_index('sample-id')

    analyzer = RarefactionAnalyzer(df)

    stats = analyzer.get_summary_stats()
    recommendation = analyzer.recommend_sampling_depth()
    interpretation = analyzer.interpret_rarefaction()
    curve_data = analyzer.get_curve_data(max_samples=request.max_samples)

    # Plotly — curvas de rarefação
    traces = []
    for curve in curve_data['curves']:
        traces.append({
            "type": "scatter",
            "mode": "lines+markers",
            "x": curve['depths'],
            "y": curve['values'],
            "name": curve['sample_id'],
            "marker": {"size": 4},
            "line": {"width": 1.5},
        })

    # Linha de corte recomendada
    if recommendation.get('recommended_depth'):
        traces.append({
            "type": "scatter",
            "mode": "lines",
            "x": [recommendation['recommended_depth'], recommendation['recommended_depth']],
            "y": [0, max(max(c['values']) for c in curve_data['curves']) if curve_data['curves'] else 100],
            "name": f"Profundidade recomendada ({recommendation['recommended_depth']})",
            "line": {"dash": "dash", "color": "red", "width": 2},
            "showlegend": True,
        })

    plotly_spec = {
        "data": traces,
        "layout": {
            "title": "Curvas de Rarefação",
            "xaxis": {"title": "Profundidade de Sequenciamento"},
            "yaxis": {"title": "Features Observadas"},
            "template": "plotly_white",
            "hovermode": "x unified",
            "showlegend": len(traces) <= 15,
        },
    }

    return {
        "data": {
            "stats": stats,
            "recommendation": recommendation,
            "interpretation": interpretation,
        },
        "plotly_spec": plotly_spec,
    }
