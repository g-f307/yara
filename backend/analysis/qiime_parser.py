"""
QIIME 2 Parser Module
=====================

Módulo para ler e processar arquivos do QIIME 2
Suporta: .qzv, .qza, .tsv, .biom

Migrado de: actions/utils/qiime_parser_module.py
Autor: Projeto YARA - IFAM
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
    
    def load_feature_table(self, filepath: str) -> Optional[pd.DataFrame]:
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


# Funções auxiliares de conveniência

def load_qiime2_data(filepath: str, data_type: str = 'auto') -> Optional[pd.DataFrame]:
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
        extract_path = parser.extract_qzv(str(filepath))
        tsv_files = parser.find_data_files(extract_path)
        df = None
        if tsv_files:
            df = pd.read_csv(tsv_files[0], sep='\t', index_col=0)
        parser.cleanup()
        return df
    else:
        if data_type == 'alpha':
            return parser.load_alpha_diversity(str(filepath))
        elif data_type == 'beta':
            df, _ = parser.load_distance_matrix(str(filepath))
            return df
        elif data_type == 'taxonomy':
            return parser.load_taxonomy(str(filepath))
        else:
            return pd.read_csv(filepath, sep='\t', index_col=0)
