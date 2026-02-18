"""
Rarefaction Analysis Module
============================

Módulo para análise de curvas de rarefação do QIIME 2

Autor: Projeto YARA - IFAM
Data: Outubro 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

warnings.filterwarnings('ignore')


class RarefactionAnalyzer:
    """
    Analisador de curvas de rarefação
    """
    
    def __init__(self, rarefaction_data: pd.DataFrame):
        """
        Inicializa analisador
        
        Args:
            rarefaction_data: DataFrame com dados de rarefação
                             Formato esperado: colunas = profundidades, linhas = amostras
        """
        self.data = rarefaction_data
        self.sample_ids = list(rarefaction_data.index)
        self.depths = [col for col in rarefaction_data.columns if col != 'sample-id']
        
    def get_plateau_depth(self, sample_id: str, threshold: float = 0.95) -> Optional[int]:
        """
        Identifica profundidade onde a curva atinge plateau
        
        Args:
            sample_id: ID da amostra
            threshold: Percentual do máximo para considerar plateau (0-1)
            
        Returns:
            Profundidade do plateau ou None
        """
        if sample_id not in self.sample_ids:
            return None
        
        sample_data = self.data.loc[sample_id]
        max_value = sample_data.max()
        plateau_value = max_value * threshold
        
        # Encontrar primeira profundidade que atinge o threshold
        for depth in self.depths:
            if sample_data[depth] >= plateau_value:
                return int(depth)
        
        return None
    
    def calculate_saturation(self, sample_id: str) -> float:
        """
        Calcula saturação da amostra (quão próxima do plateau)
        
        Args:
            sample_id: ID da amostra
            
        Returns:
            Valor de saturação (0-1)
        """
        if sample_id not in self.sample_ids:
            return 0.0
        
        sample_data = self.data.loc[sample_id]
        
        # Calcular taxa de mudança entre profundidades
        values = sample_data.values
        if len(values) < 2:
            return 0.0
        
        # Taxa de mudança no final da curva
        final_change = abs(values[-1] - values[-2]) / values[-1] if values[-1] > 0 else 0
        
        # Saturação = 1 - taxa de mudança
        saturation = 1.0 - min(final_change, 1.0)
        
        return saturation
    
    def recommend_sampling_depth(self, min_samples_retained: float = 0.8) -> Dict:
        """
        Recomenda profundidade de amostragem ideal
        
        Args:
            min_samples_retained: Fração mínima de amostras a manter
            
        Returns:
            Dicionário com recomendação
        """
        recommendations = {
            'recommended_depth': None,
            'samples_retained': 0,
            'samples_discarded': [],
            'reason': ''
        }
        
        # Calcular saturação média em cada profundidade
        saturations = {}
        for depth in self.depths:
            avg_saturation = self.data[depth].mean()
            saturations[depth] = avg_saturation
        
        # Encontrar profundidade com melhor balanço saturação/amostras
        best_depth = None
        best_score = 0
        
        for depth in self.depths:
            # Contar amostras com valores válidos nesta profundidade
            valid_samples = self.data[depth].notna().sum()
            retention_rate = valid_samples / len(self.sample_ids)
            
            if retention_rate >= min_samples_retained:
                # Score = saturação * taxa de retenção
                score = saturations[depth] * retention_rate
                
                if score > best_score:
                    best_score = score
                    best_depth = depth
        
        if best_depth:
            recommendations['recommended_depth'] = int(best_depth)
            recommendations['samples_retained'] = int(self.data[best_depth].notna().sum())
            
            # Identificar amostras descartadas
            discarded = self.data[self.data[best_depth].isna()].index.tolist()
            recommendations['samples_discarded'] = discarded
            
            avg_sat = saturations[best_depth]
            recommendations['reason'] = f"Profundidade {best_depth} oferece melhor balanço entre saturação ({avg_sat:.2%}) e retenção de amostras"
        else:
            recommendations['reason'] = "Não foi possível encontrar profundidade que mantenha o mínimo de amostras"
        
        return recommendations
    
    def get_summary_stats(self) -> Dict:
        """
        Estatísticas resumidas das curvas de rarefação
        
        Returns:
            Dicionário com estatísticas
        """
        stats = {
            'total_samples': len(self.sample_ids),
            'depth_range': {
                'min': int(min(self.depths)) if self.depths else 0,
                'max': int(max(self.depths)) if self.depths else 0
            },
            'saturation': {
                'mean': 0.0,
                'median': 0.0,
                'samples_saturated': 0
            }
        }
        
        # Calcular saturação para todas as amostras
        saturations = [self.calculate_saturation(sid) for sid in self.sample_ids]
        
        if saturations:
            stats['saturation']['mean'] = float(np.mean(saturations))
            stats['saturation']['median'] = float(np.median(saturations))
            stats['saturation']['samples_saturated'] = sum(1 for s in saturations if s > 0.95)
        
        return stats
    
    def interpret_rarefaction(self, sample_id: Optional[str] = None) -> str:
        """
        Gera interpretação textual das curvas de rarefação
        
        Args:
            sample_id: ID da amostra específica (ou None para geral)
            
        Returns:
            String com interpretação
        """
        if sample_id:
            # Interpretação para amostra específica
            saturation = self.calculate_saturation(sample_id)
            plateau_depth = self.get_plateau_depth(sample_id)
            
            interpretation = f"📊 **Rarefação - Amostra {sample_id}**\n\n"
            
            if saturation > 0.95:
                interpretation += "✅ **Curva saturada** - Sequenciamento capturou a maioria das espécies\n"
            elif saturation > 0.80:
                interpretation += "⚠️ **Curva parcialmente saturada** - Algumas espécies podem não ter sido detectadas\n"
            else:
                interpretation += "❌ **Curva não saturada** - Sequenciamento insuficiente, muitas espécies não detectadas\n"
            
            if plateau_depth:
                interpretation += f"\n📍 Plateau atingido em: **{plateau_depth} sequências**\n"
            else:
                interpretation += "\n📍 Plateau não atingido - considere sequenciamento mais profundo\n"
            
            interpretation += f"\n📈 Saturação: **{saturation:.1%}**"
            
        else:
            # Interpretação geral
            stats = self.get_summary_stats()
            recommendation = self.recommend_sampling_depth()
            
            interpretation = "📊 **Análise de Rarefação - Visão Geral**\n\n"
            interpretation += f"🔢 Total de amostras: **{stats['total_samples']}**\n"
            interpretation += f"📏 Profundidades testadas: **{stats['depth_range']['min']} - {stats['depth_range']['max']}**\n\n"
            
            interpretation += f"📈 Saturação média: **{stats['saturation']['mean']:.1%}**\n"
            interpretation += f"✅ Amostras saturadas (>95%): **{stats['saturation']['samples_saturated']}** de **{stats['total_samples']}**\n\n"
            
            if recommendation['recommended_depth']:
                interpretation += f"💡 **Recomendação de Profundidade:**\n"
                interpretation += f"• Profundidade ideal: **{recommendation['recommended_depth']} sequências**\n"
                interpretation += f"• Amostras mantidas: **{recommendation['samples_retained']}** de **{stats['total_samples']}**\n"
                
                if recommendation['samples_discarded']:
                    interpretation += f"• Amostras descartadas: **{len(recommendation['samples_discarded'])}**\n"
            else:
                interpretation += "⚠️ Não foi possível determinar profundidade ideal\n"
        
        return interpretation
    
    def plot_rarefaction_curves(self, output_path: Optional[str] = None, 
                               max_samples: int = 20) -> str:
        """
        Gera gráfico de curvas de rarefação
        
        Args:
            output_path: Caminho para salvar gráfico
            max_samples: Número máximo de amostras a plotar
            
        Returns:
            Caminho do arquivo salvo
        """
        # Selecionar amostras a plotar
        samples_to_plot = self.sample_ids[:max_samples]
        
        # Criar figura
        plt.figure(figsize=(12, 8))
        
        # Plotar cada amostra
        for sample_id in samples_to_plot:
            sample_data = self.data.loc[sample_id]
            depths_numeric = [int(d) for d in self.depths]
            plt.plot(depths_numeric, sample_data.values, 
                    marker='o', alpha=0.6, label=sample_id)
        
        plt.xlabel('Profundidade de Sequenciamento', fontsize=12)
        plt.ylabel('Número de Features Observadas', fontsize=12)
        plt.title('Curvas de Rarefação', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        
        # Legenda apenas se poucas amostras
        if len(samples_to_plot) <= 10:
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        
        # Salvar
        if output_path is None:
            output_path = "data/qiime2/rarefaction_curves.png"
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path


def load_rarefaction_data(filepath: str) -> pd.DataFrame:
    """
    Carrega dados de rarefação de arquivo TSV
    
    Args:
        filepath: Caminho para arquivo
        
    Returns:
        DataFrame formatado para análise
    """
    df = pd.read_csv(filepath, sep='\t', index_col=0)
    
    # Converter colunas para numérico quando possível
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except:
            pass
    
    return df


def analyze_rarefaction_file(filepath: str) -> Dict:
    """
    Função auxiliar para análise completa de arquivo de rarefação
    
    Args:
        filepath: Caminho para arquivo TSV
        
    Returns:
        Dicionário com resultados da análise
    """
    # Carregar dados
    df = load_rarefaction_data(filepath)
    
    # Criar analisador
    analyzer = RarefactionAnalyzer(df)
    
    # Executar análises
    results = {
        'stats': analyzer.get_summary_stats(),
        'recommendation': analyzer.recommend_sampling_depth(),
        'interpretation': analyzer.interpret_rarefaction()
    }
    
    return results
