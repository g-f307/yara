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
    project_id: str
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
    from utils.project_manager import ProjectManager

    try:
        df = ProjectManager.get_project_data(request.project_id, 'taxonomy')
    except Exception as e:
        return {"error": str(e), "plotly_spec": None}

    try:
        # QIIME2 QZV taxa-bar-plots.qzv CSVs have an 'index' column of samples, and Taxon columns.
        # If the dataframe does not have 'Taxon', maybe it's the QZV output.
        if 'Taxon' not in df.columns:
            # Sum numeric columns ignoring string columns
            numeric_df = df.select_dtypes(include='number')
            if not numeric_df.empty:
                taxa_sums = numeric_df.sum().sort_values(ascending=False).to_dict()
                taxa = list(taxa_sums.keys())
                
                # Helper to map QZV columns to level strings.
                processed_taxa = []
                for t in taxa:
                    parts = t.split(';')
                    if len(parts) >= 2:
                        processed_taxa.append(parts[-1].strip() if parts[-1].strip() else parts[-2].strip())
                    else:
                        processed_taxa.append(t)
                
                top = list(zip(processed_taxa, taxa_sums.values()))[:request.top_n]
                total_sum = sum(taxa_sums.values())
                
                summary = [
                    {"taxon": str(t), "count": float(c), "percentage": round((c / total_sum) * 100, 1)}
                    for t, c in top
                ]
                
                plotly_spec = {
                    "data": [{
                        "type": "pie",
                        "labels": [s['taxon'] for s in summary],
                        "values": [s['count'] for s in summary],
                        "textinfo": "label+percent",
                        "hole": 0.3,
                    }],
                    "layout": {
                        "title": f"Composição Taxonômica — Top {request.top_n}",
                        "template": "plotly_white",
                    },
                }
                return {
                    "data": {"total_features": len(taxa), "top_taxa": summary},
                    "plotly_spec": plotly_spec,
                }
            return {
                "error": "Tabela de taxonomia não possui coluna 'Taxon' e não é um CSV de taxonomia.",
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
    except Exception as e:
        return {"error": str(e), "plotly_spec": None}


class BarplotRequest(BaseModel):
    project_id: str
    level: str = "Phylum"
    top_n: int = 10
    sample_col: str = "sample-id"


@router.post("/barplot")
async def taxonomy_barplot(request: BarplotRequest) -> Dict[str, Any]:
    """
    Dados para stacked barplot de composição taxonômica por amostra.
    """
    from utils.project_manager import ProjectManager

    try:
        df = ProjectManager.get_project_data(request.project_id, 'taxonomy')
    except Exception as e:
        return {"error": str(e), "plotly_spec": None}

    try:
        # Se exportado diretamente de taxa-bar-plots.qzv CSV, as colunas já são as taxas formatadas
        if 'Taxon' not in df.columns:
            numeric_df = df.select_dtypes(include='number')
            if numeric_df.empty:
                return {"error": "Colunas de abundância não encontradas.", "plotly_spec": None}
                
            taxa_sums = numeric_df.sum().sort_values(ascending=False)
            top_taxa_names = taxa_sums.head(request.top_n).index.tolist()
            
            samples = numeric_df.index.tolist()
            traces = []
            for taxon in top_taxa_names:
                values = numeric_df[taxon].tolist()
                # extract friendly name
                parts = taxon.split(';')
                friendly_name = parts[-1].strip() if len(parts) >= 2 else taxon
                if not friendly_name: friendly_name = taxon
                
                traces.append({
                    "type": "bar",
                    "name": friendly_name,
                    "x": samples,
                    "y": [float(v) for v in values],
                })
                
            plotly_spec = {
                "data": traces,
                "layout": {
                    "title": f"Composição Taxonômica por Amostra",
                    "barmode": "stack",
                    "xaxis": {"title": "Amostra"},
                    "yaxis": {"title": "Abundância"},
                    "template": "plotly_white",
                },
            }

            return {
                "data": {"top_taxa": [t.split(';')[-1] for t in top_taxa_names], "samples": samples},
                "plotly_spec": plotly_spec,
            }

        df['parsed_taxon'] = df['Taxon'].apply(lambda t: _extract_taxa_at_level(t, request.level))

        # Se tiver coluna de abundância, usar; senão, contar
        abundance_cols = [c for c in df.columns if c not in ['Taxon', 'parsed_taxon', 'Feature ID', 'Confidence', 'Taxonomy_Parsed']]

        if not abundance_cols:
            return {
                "error": "Colunas de abundância não encontradas.",
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
    except Exception as e:
        return {"error": str(e), "plotly_spec": None}
