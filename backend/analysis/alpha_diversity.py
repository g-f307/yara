"""
Alpha Diversity Analyzer
=========================

Analisador de diversidade alfa para dados metagenômicos.

Migrado de: actions/utils/qiime_parser_module.py (classe AlphaDiversityAnalyzer)
Autor: Projeto YARA - IFAM
"""

import pandas as pd
import numpy as np
from typing import Dict


class AlphaDiversityAnalyzer:
    """
    Analisador específico para diversidade alfa
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Args:
            data: DataFrame com métricas de diversidade alfa
        """
        self.data = data
    
    def get_summary_stats(self, metric: str = 'shannon') -> Dict:
        """
        Estatísticas resumidas para uma métrica
        
        Args:
            metric: Nome da métrica
            
        Returns:
            Dicionário com estatísticas
        """
        if metric not in self.data.columns:
            available = list(self.data.columns)
            raise ValueError(f"Métrica '{metric}' não encontrada. Disponíveis: {available}")
        
        serie = self.data[metric]
        
        return {
            'mean': float(serie.mean()),
            'median': float(serie.median()),
            'std': float(serie.std()),
            'min': float(serie.min()),
            'max': float(serie.max()),
            'q25': float(serie.quantile(0.25)),
            'q75': float(serie.quantile(0.75))
        }
    
    def interpret_value(self, value: float, metric: str = 'shannon') -> str:
        """
        Interpreta um valor de diversidade
        
        Args:
            value: Valor da métrica
            metric: Tipo de métrica
            
        Returns:
            String com interpretação
        """
        metric = metric.lower()
        
        if 'shannon' in metric:
            if value < 1.5:
                return "Baixa diversidade - comunidade dominada por poucas espécies"
            elif value < 2.5:
                return "Diversidade moderada - comunidade relativamente equilibrada"
            elif value < 3.5:
                return "Alta diversidade - comunidade bem equilibrada"
            else:
                return "Diversidade muito alta - comunidade muito complexa"
        
        elif 'simpson' in metric:
            if value < 0.5:
                return "Baixa diversidade - alta dominância de poucas espécies"
            elif value < 0.8:
                return "Diversidade moderada"
            else:
                return "Alta diversidade - baixa dominância"
        
        elif 'observed' in metric.lower() or 'richness' in metric.lower():
            if value < 100:
                return "Baixa riqueza - poucas espécies detectadas"
            elif value < 300:
                return "Riqueza moderada"
            else:
                return "Alta riqueza - muitas espécies detectadas"
        
        return "Interpretação não disponível para esta métrica"
    
    def compare_groups(self, group_column: str, metric: str = 'shannon') -> Dict:
        """
        Compara métrica entre grupos
        
        Args:
            group_column: Nome da coluna de grupos
            metric: Métrica a comparar
            
        Returns:
            Dicionário com comparação
        """
        from scipy.stats import mannwhitneyu
        
        if group_column not in self.data.columns:
            raise ValueError(f"Coluna '{group_column}' não encontrada")
        
        groups = self.data[group_column].unique()
        
        if len(groups) != 2:
            return {'error': 'Comparação suporta apenas 2 grupos'}
        
        group1_data = self.data[self.data[group_column] == groups[0]][metric]
        group2_data = self.data[self.data[group_column] == groups[1]][metric]
        
        stat, pvalue = mannwhitneyu(group1_data, group2_data)
        
        return {
            'groups': [str(g) for g in groups],
            'group1_mean': float(group1_data.mean()),
            'group2_mean': float(group2_data.mean()),
            'difference_pct': float(((group2_data.mean() - group1_data.mean()) / group1_data.mean()) * 100),
            'statistic': float(stat),
            'p_value': float(pvalue),
            'significant': bool(pvalue < 0.05)
        }
