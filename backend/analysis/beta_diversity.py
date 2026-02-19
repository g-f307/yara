"""
Beta Diversity Analyzer
========================

Analisador de diversidade beta para dados metagenômicos.

Migrado de: actions/utils/qiime_parser_module.py (classe BetaDiversityAnalyzer)
Autor: Projeto YARA - IFAM
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class BetaDiversityAnalyzer:
    """
    Analisador específico para diversidade beta
    """
    
    def __init__(self, distance_matrix: pd.DataFrame):
        """
        Args:
            distance_matrix: Matriz de distâncias
        """
        self.distance_matrix = distance_matrix
        self.sample_ids = list(distance_matrix.index)
    
    def get_distance_stats(self) -> Dict:
        """
        Estatísticas gerais das distâncias
        
        Returns:
            Dicionário com estatísticas
        """
        # Pegar apenas triângulo superior (sem diagonal)
        triu_indices = np.triu_indices_from(self.distance_matrix.values, k=1)
        distances = self.distance_matrix.values[triu_indices]
        
        return {
            'mean': float(np.mean(distances)),
            'median': float(np.median(distances)),
            'std': float(np.std(distances)),
            'min': float(np.min(distances)),
            'max': float(np.max(distances))
        }
    
    def calculate_pcoa(self, n_components: int = 2) -> pd.DataFrame:
        """
        Calcula PCoA
        
        Args:
            n_components: Número de componentes
            
        Returns:
            DataFrame com coordenadas
        """
        from sklearn.manifold import MDS
        
        mds = MDS(
            n_components=n_components,
            dissimilarity='precomputed',
            random_state=42
        )
        
        coords = mds.fit_transform(self.distance_matrix.values)
        
        columns = [f'PC{i+1}' for i in range(n_components)]
        df_coords = pd.DataFrame(
            coords,
            index=self.sample_ids,
            columns=columns
        )
        
        return df_coords
    
    def get_closest_samples(self, sample_id: str, n: int = 5) -> List[Tuple[str, float]]:
        """
        Encontra amostras mais próximas
        
        Args:
            sample_id: ID da amostra
            n: Número de amostras
            
        Returns:
            Lista de (sample_id, distância)
        """
        if sample_id not in self.sample_ids:
            raise ValueError(f"Amostra '{sample_id}' não encontrada")
        
        distances = self.distance_matrix.loc[sample_id]
        distances = distances[distances.index != sample_id]
        closest = distances.nsmallest(n)
        
        return [(str(idx), float(val)) for idx, val in zip(closest.index, closest.values)]
