"""
QIIME 2 Parser Module
=====================

Módulo para ler e processar arquivos do QIIME 2
Suporta: .qzv, .qza, .tsv, .biom

Autor: Projeto YARA - IFAM
Data: Outubro 2025
"""

import pandas as pd
import numpy as np
import zipfile
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

warnings.filterwarnings('ignore')


class QIIME2Parser:
    """
    Parser principal para arquivos QIIME 2
    """
    
    def __init__(self, base_path: str = "data/qiime2"):
        """
        Inicializa parser
        
        Args:
            base_path: Caminho para diretório de dados
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.temp_dir = None
        
    def extract_qzv(self, qzv_path: str) -> Path:
        """
        Extrai conteúdo de arquivo .qzv
        
        Args:
            qzv_path: Caminho para arquivo .qzv
            
        Returns:
            Path do diretório extraído
        """
        qzv_path = Path(qzv_path)
        
        if not qzv_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {qzv_path}")
        
        # Criar diretório temporário
        self.temp_dir = tempfile.mkdtemp(prefix="qiime2_")
        
        # Extrair
        with zipfile.ZipFile(qzv_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)
        
        return Path(self.temp_dir)
    
    def find_data_files(self, extract_path: Path, pattern: str = "*.tsv") -> List[Path]:
        """
        Encontra arquivos de dados no diretório extraído
        
        Args:
            extract_path: Diretório extraído
            pattern: Padrão de arquivo a buscar
            
        Returns:
            Lista de paths encontrados
        """
        files = list(extract_path.rglob(pattern))
        return files
    
    def load_alpha_diversity(self, filepath: str) -> pd.DataFrame:
        """
        Carrega arquivo TSV de diversidade alfa
        
        Args:
            filepath: Caminho para arquivo
            
        Returns:
            DataFrame com métricas de diversidade alfa
        """
        df = pd.read_csv(filepath, sep='\t', index_col=0)
        return df
    
    def load_distance_matrix(self, filepath: str) -> Tuple[pd.DataFrame, List[str]]:
        """
        Carrega matriz de distâncias
        
        Args:
            filepath: Caminho para arquivo
            
        Returns:
            (DataFrame da matriz, lista de sample IDs)
        """
        df = pd.read_csv(filepath, sep='\t', index_col=0)
        sample_ids = list(df.index)
        return df, sample_ids
    
    def load_taxonomy(self, filepath: str) -> pd.DataFrame:
        """
        Carrega classificação taxonômica
        
        Args:
            filepath: Caminho para arquivo
            
        Returns:
            DataFrame com taxonomia
        """
        df = pd.read_csv(filepath, sep='\t')
        
        # Parse taxonomia se estiver em formato string
        if 'Taxon' in df.columns:
            df['Taxonomy_Parsed'] = df['Taxon'].apply(self._parse_taxonomy_string)
        
        return df
    
    def _parse_taxonomy_string(self, tax_string: str) -> Dict[str, str]:
        """
        Parse string de taxonomia do QIIME 2
        
        Args:
            tax_string: String de taxonomia (ex: "k__Bacteria; p__Proteobacteria")
            
        Returns:
            Dicionário com níveis taxonômicos
        """
        levels = {
            'k': 'Kingdom',
            'p': 'Phylum',
            'c': 'Class',
            'o': 'Order',
            'f': 'Family',
            'g': 'Genus',
            's': 'Species'
        }
        
        parsed = {}
        
        if pd.isna(tax_string):
            return parsed
        
        parts = tax_string.split(';')
        
        for part in parts:
            part = part.strip()
            if '__' in part:
                level_code, taxon = part.split('__', 1)
                level_code = level_code.strip()
                taxon = taxon.strip()
                
                if level_code in levels:
                    parsed[levels[level_code]] = taxon if taxon else 'Unassigned'
        
        return parsed
    
    def load_feature_table(self, filepath: str) -> pd.DataFrame:
        """
        Carrega tabela de features (OTU/ASV table)
        
        Args:
            filepath: Caminho para arquivo
            
        Returns:
            DataFrame com abundâncias
        """
        # Tentar ler como TSV normal
        try:
            df = pd.read_csv(filepath, sep='\t', index_col=0, comment='#')
            return df
        except Exception as e:
            print(f"Erro ao ler tabela: {e}")
            return None
    
    def calculate_alpha_diversity_stats(self, df: pd.DataFrame, 
                                       group_column: Optional[str] = None) -> Dict:
        """
        Calcula estatísticas de diversidade alfa
        
        Args:
            df: DataFrame com métricas de diversidade
            group_column: Nome da coluna de grupos (opcional)
            
        Returns:
            Dicionário com estatísticas
        """
        stats = {
            'overall': df.describe().to_dict(),
            'metrics': list(df.columns)
        }
        
        if group_column and group_column in df.columns:
            stats['by_group'] = {}
            for group in df[group_column].unique():
                subset = df[df[group_column] == group]
                stats['by_group'][group] = subset.describe().to_dict()
        
        return stats
    
    def get_top_taxa(self, taxonomy_df: pd.DataFrame, 
                     abundance_df: Optional[pd.DataFrame] = None,
                     level: str = 'Phylum',
                     top_n: int = 10) -> pd.DataFrame:
        """
        Obtém top N táxons mais abundantes
        
        Args:
            taxonomy_df: DataFrame com taxonomia
            abundance_df: DataFrame com abundâncias (opcional)
            level: Nível taxonômico
            top_n: Número de táxons
            
        Returns:
            DataFrame com top táxons
        """
        if abundance_df is not None:
            # Calcular abundância total por táxon
            total_abundance = abundance_df.sum(axis=0)
            taxonomy_df = taxonomy_df.copy()
            taxonomy_df['Total_Abundance'] = taxonomy_df.index.map(total_abundance)
            taxonomy_df = taxonomy_df.sort_values('Total_Abundance', ascending=False)
        
        return taxonomy_df.head(top_n)
    
    def cleanup(self):
        """Remove arquivos temporários"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None


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
            'groups': list(groups),
            'group1_mean': float(group1_data.mean()),
            'group2_mean': float(group2_data.mean()),
            'difference_pct': float(((group2_data.mean() - group1_data.mean()) / group1_data.mean()) * 100),
            'statistic': float(stat),
            'p_value': float(pvalue),
            'significant': pvalue < 0.05
        }


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
        
        return list(zip(closest.index, closest.values))


# Funções auxiliares de conveniência

def load_qiime2_data(filepath: str, data_type: str = 'auto') -> pd.DataFrame:
    """
    Função de conveniência para carregar dados QIIME 2
    
    Args:
        filepath: Caminho para arquivo
        data_type: Tipo de dado ('alpha', 'beta', 'taxonomy', 'auto')
        
    Returns:
        DataFrame com dados
    """
    parser = QIIME2Parser()
    
    filepath = Path(filepath)
    
    # Auto-detectar tipo
    if data_type == 'auto':
        if 'alpha' in filepath.name.lower():
            data_type = 'alpha'
        elif 'distance' in filepath.name.lower() or 'beta' in filepath.name.lower():
            data_type = 'beta'
        elif 'taxonomy' in filepath.name.lower():
            data_type = 'taxonomy'
    
    # Carregar conforme tipo
    if filepath.suffix == '.qzv':
        extract_path = parser.extract_qzv(filepath)
        tsv_files = parser.find_data_files(extract_path)
        if tsv_files:
            df = pd.read_csv(tsv_files[0], sep='\t', index_col=0)
        parser.cleanup()
        return df
    else:
        if data_type == 'alpha':
            return parser.load_alpha_diversity(filepath)
        elif data_type == 'beta':
            df, _ = parser.load_distance_matrix(filepath)
            return df
        elif data_type == 'taxonomy':
            return parser.load_taxonomy(filepath)
        else:
            return pd.read_csv(filepath, sep='\t', index_col=0)


if __name__ == "__main__":
    print("🧬 QIIME 2 Parser Module")
    print("=" * 60)
    print("Módulo carregado com sucesso!")
    print("\nClasses disponíveis:")
    print("  - QIIME2Parser")
    print("  - AlphaDiversityAnalyzer")
    print("  - BetaDiversityAnalyzer")
    print("\nFunções:")
    print("  - load_qiime2_data()")
