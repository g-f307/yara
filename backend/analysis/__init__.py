"""
YARA Analysis Modules
=====================

Módulos científicos para análise de dados metagenômicos QIIME 2.
Migrados de actions/utils/ (legado Rasa) — lógica preservada.
"""

from analysis.qiime_parser import QIIME2Parser, load_qiime2_data
from analysis.alpha_diversity import AlphaDiversityAnalyzer
from analysis.beta_diversity import BetaDiversityAnalyzer
from analysis.rarefaction import RarefactionAnalyzer, load_rarefaction_data, analyze_rarefaction_file
from analysis.statistics import calculate_kruskal_wallis, calculate_mann_whitney, get_group_stats
from analysis.report_generator import ReportGenerator

__all__ = [
    "QIIME2Parser",
    "load_qiime2_data",
    "AlphaDiversityAnalyzer",
    "BetaDiversityAnalyzer",
    "RarefactionAnalyzer",
    "load_rarefaction_data",
    "analyze_rarefaction_file",
    "calculate_kruskal_wallis",
    "calculate_mann_whitney",
    "get_group_stats",
    "ReportGenerator",
]
