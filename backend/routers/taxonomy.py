"""
Taxonomy Router
================

POST /api/taxonomy/summary — Composição taxonômica por nível
POST /api/taxonomy/barplot — Dados para stacked barplot
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from collections import Counter
import pandas as pd

from analysis.qiime_parser import QIIME2Parser

router = APIRouter(prefix="/api/taxonomy", tags=["taxonomy"])

# Níveis taxonômicos e prefixos QIIME 2
LEVEL_PREFIXES = {
    'Kingdom': 'k__',
    'Phylum': 'p__',
    'Class': 'c__',
    'Order': 'o__',
    'Family': 'f__',
    'Genus': 'g__',
    'Species': 's__',
}


class TaxonomyRequest(BaseModel):
    data: List[Dict[str, Any]]
    level: str = "Phylum"
    top_n: int = 10


def _extract_taxa_at_level(taxon_string: str, level: str) -> str:
    """Extrai nome do táxon no nível especificado."""
    prefix = LEVEL_PREFIXES.get(level, 'p__')
    if not isinstance(taxon_string, str):
        return "Unassigned"
    for part in taxon_string.split(';'):
        part = part.strip()
        if part.startswith(prefix):
            name = part.split('__', 1)[1].strip()
            return name if name else "Unassigned"
    return "Unassigned"


@router.post("/summary")
async def taxonomy_summary(request: TaxonomyRequest) -> Dict[str, Any]:
    """
    Resumo de composição taxonômica no nível solicitado.
    """
    df = pd.DataFrame(request.data)

    if 'Taxon' not in df.columns:
        return {
            "data": {"error": "Coluna 'Taxon' não encontrada nos dados."},
            "plotly_spec": None,
        }

    taxa = [_extract_taxa_at_level(t, request.level) for t in df['Taxon']]
    counts = Counter(taxa)
    top = counts.most_common(request.top_n)

    summary = [
        {"taxon": t, "count": c, "percentage": round(c / len(taxa) * 100, 1)}
        for t, c in top
    ]

    # Pie chart
    plotly_spec = {
        "data": [{
            "type": "pie",
            "labels": [s['taxon'] for s in summary],
            "values": [s['count'] for s in summary],
            "textinfo": "label+percent",
            "hole": 0.3,
        }],
        "layout": {
            "title": f"Composição Taxonômica — {request.level} (Top {request.top_n})",
            "template": "plotly_white",
        },
    }

    return {
        "data": {
            "level": request.level,
            "total_features": len(taxa),
            "top_taxa": summary,
        },
        "plotly_spec": plotly_spec,
    }


class BarplotRequest(BaseModel):
    data: List[Dict[str, Any]]
    level: str = "Phylum"
    top_n: int = 10
    sample_col: str = "sample-id"


@router.post("/barplot")
async def taxonomy_barplot(request: BarplotRequest) -> Dict[str, Any]:
    """
    Dados para stacked barplot de composição taxonômica por amostra.
    """
    df = pd.DataFrame(request.data)

    if 'Taxon' not in df.columns:
        return {
            "data": {"error": "Coluna 'Taxon' não encontrada nos dados."},
            "plotly_spec": None,
        }

    df['parsed_taxon'] = df['Taxon'].apply(lambda t: _extract_taxa_at_level(t, request.level))

    # Se tiver coluna de abundância, usar; senão, contar
    abundance_cols = [c for c in df.columns if c not in ['Taxon', 'parsed_taxon', 'Feature ID', 'Confidence']]

    if not abundance_cols:
        return {
            "data": {"error": "Colunas de abundância não encontradas."},
            "plotly_spec": None,
        }

    # Agrupar por táxon e somar abundâncias
    top_taxa_names = df['parsed_taxon'].value_counts().head(request.top_n).index.tolist()

    traces = []
    for taxon in top_taxa_names:
        subset = df[df['parsed_taxon'] == taxon]
        values = subset[abundance_cols].sum().tolist()
        traces.append({
            "type": "bar",
            "name": taxon,
            "x": abundance_cols,
            "y": [float(v) for v in values],
        })

    plotly_spec = {
        "data": traces,
        "layout": {
            "title": f"Composição Taxonômica por Amostra — {request.level}",
            "barmode": "stack",
            "xaxis": {"title": "Amostra"},
            "yaxis": {"title": "Abundância"},
            "template": "plotly_white",
        },
    }

    return {
        "data": {
            "level": request.level,
            "top_taxa": top_taxa_names,
            "samples": abundance_cols,
        },
        "plotly_spec": plotly_spec,
    }
