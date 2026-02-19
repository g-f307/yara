"""
Statistical Analysis Module
===========================

Módulo para análise estatística de dados metagenômicos
Implementa testes não-paramétricos (Kruskal-Wallis, Mann-Whitney)

Migrado de: actions/utils/statistics.py
Autor: Projeto YARA - IFAM
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Optional, Tuple, Any

def calculate_kruskal_wallis(df: pd.DataFrame, group_col: str, metric_col: str) -> Dict[str, Any]:
    """
    Calcula teste de Kruskal-Wallis para k grupos independentes
    
    Args:
        df: DataFrame contendo dados e metadados
        group_col: Coluna com grupos
        metric_col: Coluna com métrica a comparar (ex: Shannon)
        
    Returns:
        Dicionário com estatísticas e interpretação
    """
    groups = df[group_col].unique()
    
    # Coletar valores para cada grupo
    group_values = []
    valid_groups = []
    
    for group in groups:
        values = df[df[group_col] == group][metric_col].dropna().values
        if len(values) >= 5:  # Mínimo de amostras recomendado
            group_values.append(values)
            valid_groups.append(str(group))
            
    if len(valid_groups) < 2:
        return {
            "success": False,
            "message": f"Grupos insuficientes para análise. Necessário pelo menos 2 grupos com 5+ amostras."
        }
        
    # Executar teste
    try:
        statistic, p_value = stats.kruskal(*group_values)
        
        result = {
            "success": True,
            "test": "Kruskal-Wallis",
            "statistic": float(statistic),
            "p_value": float(p_value),
            "groups": valid_groups,
            "metric": metric_col,
            "significant": bool(p_value < 0.05)
        }
        
        # Gerar interpretação
        if result["significant"]:
            result["interpretation"] = (
                f"✅ **Diferença Significativa Detectada** (p={p_value:.4f})\n"
                f"A métrica '{metric_col}' varia significativamente entre os grupos {', '.join(valid_groups)}."
            )
        else:
            result["interpretation"] = (
                f"❌ **Nenhuma Diferença Significativa** (p={p_value:.4f})\n"
                f"Não há evidências de que '{metric_col}' varie entre os grupos."
            )
            
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao executar Kruskal-Wallis: {str(e)}"
        }

def calculate_mann_whitney(df: pd.DataFrame, group_col: str, group1: str, group2: str, metric_col: str) -> Dict[str, Any]:
    """
    Calcula teste de Mann-Whitney U para 2 grupos independentes
    
    Args:
        df: DataFrame
        group_col: Coluna de grupos
        group1: Nome do primeiro grupo
        group2: Nome do segundo grupo
        metric_col: Métrica a comparar
        
    Returns:
        Dicionário com resultados
    """
    # Validar grupos
    if group1 not in df[group_col].values or group2 not in df[group_col].values:
         return {
            "success": False,
            "message": f"Grupos '{group1}' ou '{group2}' não encontrados na coluna '{group_col}'."
        }
        
    values1 = df[df[group_col] == group1][metric_col].dropna().values
    values2 = df[df[group_col] == group2][metric_col].dropna().values
    
    if len(values1) < 3 or len(values2) < 3:
        return {
            "success": False,
            "message": "Amostras insuficientes (mínimo 3 por grupo)."
        }
        
    try:
        statistic, p_value = stats.mannwhitneyu(values1, values2, alternative='two-sided')
        
        result = {
            "success": True,
            "test": "Mann-Whitney U",
            "statistic": float(statistic),
            "p_value": float(p_value),
            "groups": [group1, group2],
            "significant": bool(p_value < 0.05)
        }
        
        if result["significant"]:
            # Verificar qual é maior (pela mediana)
            med1 = float(np.median(values1))
            med2 = float(np.median(values2))
            direction = f"{group1} ({med1:.2f}) > {group2} ({med2:.2f})" if med1 > med2 else f"{group2} ({med2:.2f}) > {group1} ({med1:.2f})"
            
            result["interpretation"] = (
                f"✅ **Diferença Significativa** (p={p_value:.4f})\n"
                f"Há diferença real entre os grupos.\n"
                f"Tendência: **{direction}**"
            )
        else:
            result["interpretation"] = (
                f"❌ **Sem Diferença Significativa** (p={p_value:.4f})\n"
                f"Os grupos {group1} e {group2} são estatisticamente similares para '{metric_col}'."
            )
            
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro no teste Mann-Whitney: {str(e)}"
        }

def get_group_stats(df: pd.DataFrame, group_col: str, metric_col: str) -> str:
    """Retorna estatísticas descritivas por grupo"""
    stats_df = df.groupby(group_col)[metric_col].describe()
    
    output = f"📊 **Estatísticas por {group_col}:**\n\n"
    output += "| Grupo | N | Média | Mediana | Desvio Padrão |\n"
    output += "|-------|---|-------|---------|---------------|\n"
    
    for group in stats_df.index:
        row = stats_df.loc[group]
        output += f"| {group} | {int(row['count'])} | {row['mean']:.2f} | {row['50%']:.2f} | {row['std']:.2f} |\n"
        
    return output
