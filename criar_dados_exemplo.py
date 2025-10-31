#!/usr/bin/env python3
"""
Script para criar dados de exemplo do QIIME 2
Para testar o bot YARA
"""

import pandas as pd
import numpy as np
from pathlib import Path

def criar_dados_exemplo():
    """Cria dados sintéticos de exemplo"""
    
    print("🧬 Criando dados de exemplo QIIME 2...")
    print("=" * 60)
    
    # Criar diretório
    data_dir = Path("data/qiime2")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    np.random.seed(42)
    
    # ========================================================================
    # 1. DIVERSIDADE ALFA
    # ========================================================================
    print("\n📊 Criando dados de Diversidade Alfa...")
    
    n_samples = 20
    sample_ids = [f"Amostra_{i+1:02d}" for i in range(n_samples)]
    grupos = ['Controle'] * 10 + ['Tratamento'] * 10
    
    # Shannon
    shannon_controle = np.random.normal(2.5, 0.3, 10)
    shannon_tratamento = np.random.normal(3.2, 0.4, 10)
    shannon = np.concatenate([shannon_controle, shannon_tratamento])
    
    # Simpson
    simpson_controle = np.random.normal(0.85, 0.05, 10)
    simpson_tratamento = np.random.normal(0.92, 0.04, 10)
    simpson = np.concatenate([simpson_controle, simpson_tratamento])
    
    # Observed Features
    observed_controle = np.random.randint(150, 250, 10)
    observed_tratamento = np.random.randint(200, 350, 10)
    observed = np.concatenate([observed_controle, observed_tratamento])
    
    # Chao1
    chao1 = observed * np.random.uniform(1.1, 1.3, n_samples)
    
    # Faith PD
    faith_controle = np.random.normal(12.5, 2.0, 10)
    faith_tratamento = np.random.normal(15.8, 2.5, 10)
    faith = np.concatenate([faith_controle, faith_tratamento])
    
    # Criar DataFrame
    df_alpha = pd.DataFrame({
        'shannon': shannon,
        'simpson': simpson,
        'observed_features': observed,
        'chao1': chao1,
        'faith_pd': faith,
        'grupo': grupos
    }, index=sample_ids)
    
    # Salvar
    output_file = data_dir / "diversidade_alfa.tsv"
    df_alpha.to_csv(output_file, sep='\t')
    print(f"✅ Salvo: {output_file}")
    print(f"   {len(df_alpha)} amostras")
    print(f"   Grupos: {', '.join(df_alpha['grupo'].unique())}")
    
    # ========================================================================
    # 2. MATRIZ DE DISTÂNCIAS (Beta Diversidade)
    # ========================================================================
    print("\n📊 Criando Matriz de Distâncias (Bray-Curtis)...")
    
    from scipy.spatial.distance import pdist, squareform
    
    # Criar abundâncias sintéticas
    n_asvs = 50
    abundancias_controle = np.random.poisson(lam=50, size=(10, n_asvs))
    abundancias_tratamento = np.random.poisson(lam=50, size=(10, n_asvs))
    
    # Diferenças entre grupos
    abundancias_controle[:, 0:10] *= 3
    abundancias_tratamento[:, 10:20] *= 3
    
    abundancias = np.vstack([abundancias_controle, abundancias_tratamento])
    
    # Calcular distâncias
    distances = pdist(abundancias, metric='braycurtis')
    distance_matrix = squareform(distances)
    
    df_distances = pd.DataFrame(
        distance_matrix,
        index=sample_ids,
        columns=sample_ids
    )
    
    output_file = data_dir / "distance_matrix_braycurtis.tsv"
    df_distances.to_csv(output_file, sep='\t')
    print(f"✅ Salvo: {output_file}")
    print(f"   Matriz {distance_matrix.shape[0]}x{distance_matrix.shape[1]}")
    
    # ========================================================================
    # 3. TAXONOMIA
    # ========================================================================
    print("\n🦠 Criando dados de Taxonomia...")
    
    n_asvs_taxa = 30
    asv_ids = [f"ASV_{i+1:03d}" for i in range(n_asvs_taxa)]
    
    # Filos comuns em microbioma intestinal
    phyla = ['Firmicutes', 'Bacteroidetes', 'Proteobacteria', 'Actinobacteria', 'Verrucomicrobia']
    
    taxonomias = []
    for i in range(n_asvs_taxa):
        phylum = np.random.choice(phyla, p=[0.35, 0.30, 0.20, 0.10, 0.05])
        
        if phylum == 'Firmicutes':
            classes = ['Clostridia', 'Bacilli']
            cls = np.random.choice(classes)
            if cls == 'Clostridia':
                family = np.random.choice(['Lachnospiraceae', 'Ruminococcaceae'])
            else:
                family = np.random.choice(['Lactobacillaceae', 'Streptococcaceae'])
        elif phylum == 'Bacteroidetes':
            cls = 'Bacteroidia'
            family = np.random.choice(['Bacteroidaceae', 'Prevotellaceae'])
        elif phylum == 'Proteobacteria':
            cls = 'Gammaproteobacteria'
            family = np.random.choice(['Enterobacteriaceae', 'Pseudomonadaceae'])
        elif phylum == 'Actinobacteria':
            cls = 'Actinobacteria'
            family = 'Bifidobacteriaceae'
        else:
            cls = 'Verrucomicrobiae'
            family = 'Akkermansiaceae'
        
        # Formato QIIME 2
        taxonomy = f"k__Bacteria; p__{phylum}; c__{cls}; o__; f__{family}; g__; s__"
        taxonomias.append(taxonomy)
    
    # Abundância total
    abundancia_total = np.random.randint(100, 5000, n_asvs_taxa)
    
    df_taxonomy = pd.DataFrame({
        'Feature ID': asv_ids,
        'Taxon': taxonomias,
        'Confidence': np.random.uniform(0.85, 0.99, n_asvs_taxa),
        'Total_Abundance': abundancia_total
    })
    
    output_file = data_dir / "taxonomy.tsv"
    df_taxonomy.to_csv(output_file, sep='\t', index=False)
    print(f"✅ Salvo: {output_file}")
    print(f"   {len(df_taxonomy)} ASVs classificados")
    
    # ========================================================================
    # 4. METADADOS
    # ========================================================================
    print("\n📋 Criando arquivo de metadados...")
    
    df_metadata = pd.DataFrame({
        'sample_id': sample_ids,
        'grupo': grupos,
        'local': ['Amazônia'] * n_samples,
        'tipo_amostra': ['Solo'] * 10 + ['Água'] * 10,
        'profundidade_sequenciamento': np.random.randint(10000, 50000, n_samples)
    })
    
    output_file = data_dir / "metadata.tsv"
    df_metadata.to_csv(output_file, sep='\t', index=False)
    print(f"✅ Salvo: {output_file}")
    
    # ========================================================================
    # 5. README
    # ========================================================================
    readme_content = """# Dados de Exemplo QIIME 2

Este diretório contém dados sintéticos de exemplo para testar o bot YARA.

## Arquivos:

1. **diversidade_alfa.tsv**
   - Métricas de diversidade alfa (Shannon, Simpson, etc)
   - 20 amostras (10 Controle, 10 Tratamento)

2. **distance_matrix_braycurtis.tsv**
   - Matriz de distâncias Bray-Curtis
   - Usado para análise de diversidade beta

3. **taxonomy.tsv**
   - Classificação taxonômica de 30 ASVs
   - Formato QIIME 2

4. **metadata.tsv**
   - Informações sobre as amostras
   - Grupo, local, tipo, etc

## Como usar:

Converse com o bot YARA e pergunte sobre diversidade!

Exemplos:
- "Quais dados tenho disponíveis?"
- "O que é diversidade alfa?"
- "Analisa minha diversidade"
"""
    
    readme_file = data_dir / "README.md"
    with open(readme_file, 'w') as f:
        f.write(readme_content)
    print(f"✅ Salvo: {readme_file}")
    
    # ========================================================================
    # RESUMO
    # ========================================================================
    print("\n" + "=" * 60)
    print("🎉 Dados de exemplo criados com sucesso!")
    print("=" * 60)
    print(f"\n📁 Localização: {data_dir.absolute()}")
    print(f"\n📊 Arquivos criados:")
    for arquivo in data_dir.glob("*"):
        print(f"   • {arquivo.name}")
    
    print("\n💡 Próximos passos:")
    print("   1. Reiniciar servidor de actions: rasa run actions")
    print("   2. Conversar com o bot: rasa shell")
    print("   3. Perguntar: 'quais dados tenho disponíveis?'")
    print("   4. Perguntar: 'o que é diversidade alfa?'")
    print()


if __name__ == "__main__":
    criar_dados_exemplo()