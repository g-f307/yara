#!/usr/bin/env python3
"""
Gerador de Dados de Teste para YARA
====================================

Gera dados sintéticos no formato QIIME 2 para testar todas as funcionalidades do YARA.

Autor: Projeto YARA - IFAM
Data: Outubro 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
import random

# Configurar seed para reprodutibilidade
np.random.seed(42)
random.seed(42)

# Diretório de saída
OUTPUT_DIR = Path("data/qiime2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("🧬 YARA - Gerador de Dados de Teste")
print("=" * 60)
print()


# ============================================================================
# 1. GERAR DADOS DE DIVERSIDADE ALFA
# ============================================================================

def gerar_diversidade_alfa(n_samples=15):
    """Gera arquivo de diversidade alfa"""
    print("📊 Gerando dados de diversidade alfa...")
    
    sample_ids = [f"amostra_{i:03d}" for i in range(1, n_samples + 1)]
    
    # Gerar métricas de diversidade
    data = {
        'Shannon': np.random.uniform(1.5, 4.5, n_samples),
        'Simpson': np.random.uniform(0.6, 0.95, n_samples),
        'Observed_Features': np.random.randint(80, 350, n_samples),
        'Chao1': np.random.uniform(100, 400, n_samples),
        'Faith_PD': np.random.uniform(5, 25, n_samples)
    }
    
    df = pd.DataFrame(data, index=sample_ids)
    df.index.name = 'sample-id'
    
    output_file = OUTPUT_DIR / "diversidade_alfa.tsv"
    df.to_csv(output_file, sep='\t')
    
    print(f"  ✅ Criado: {output_file}")
    print(f"     • {n_samples} amostras")
    print(f"     • 5 métricas (Shannon, Simpson, Observed_Features, Chao1, Faith_PD)")
    print()
    
    return df


# ============================================================================
# 2. GERAR MATRIZ DE DISTÂNCIAS (DIVERSIDADE BETA)
# ============================================================================

def gerar_matriz_distancias(sample_ids):
    """Gera matriz de distâncias Bray-Curtis"""
    print("📊 Gerando matriz de distâncias (Beta)...")
    
    n = len(sample_ids)
    
    # Gerar matriz simétrica de distâncias
    distances = np.random.uniform(0.1, 0.9, (n, n))
    
    # Tornar simétrica
    distances = (distances + distances.T) / 2
    
    # Diagonal = 0
    np.fill_diagonal(distances, 0)
    
    df = pd.DataFrame(distances, index=sample_ids, columns=sample_ids)
    df.index.name = 'sample-id'
    
    output_file = OUTPUT_DIR / "distance_matrix_braycurtis.tsv"
    df.to_csv(output_file, sep='\t')
    
    print(f"  ✅ Criado: {output_file}")
    print(f"     • Matriz {n}x{n}")
    print(f"     • Métrica: Bray-Curtis")
    print()
    
    return df


# ============================================================================
# 3. GERAR COORDENADAS PCoA
# ============================================================================

def gerar_pcoa_coordinates(sample_ids):
    """Gera coordenadas PCoA"""
    print("📊 Gerando coordenadas PCoA...")
    
    n = len(sample_ids)
    
    # Gerar 3 eixos principais
    data = {
        'PC1': np.random.uniform(-0.5, 0.5, n),
        'PC2': np.random.uniform(-0.4, 0.4, n),
        'PC3': np.random.uniform(-0.3, 0.3, n)
    }
    
    df = pd.DataFrame(data, index=sample_ids)
    df.index.name = 'sample-id'
    
    output_file = OUTPUT_DIR / "pcoa_coordinates.tsv"
    df.to_csv(output_file, sep='\t')
    
    print(f"  ✅ Criado: {output_file}")
    print(f"     • {n} amostras")
    print(f"     • 3 componentes principais")
    print()
    
    return df


# ============================================================================
# 4. GERAR TAXONOMIA
# ============================================================================

def gerar_taxonomia(n_features=200):
    """Gera classificação taxonômica"""
    print("🦠 Gerando dados de taxonomia...")
    
    # Filos comuns em microbioma
    phyla = [
        'Proteobacteria', 'Firmicutes', 'Bacteroidetes', 'Actinobacteria',
        'Verrucomicrobia', 'Planctomycetes', 'Cyanobacteria', 'Acidobacteria'
    ]
    
    # Classes por filo (simplificado)
    classes = {
        'Proteobacteria': ['Alphaproteobacteria', 'Betaproteobacteria', 'Gammaproteobacteria', 'Deltaproteobacteria'],
        'Firmicutes': ['Bacilli', 'Clostridia', 'Negativicutes'],
        'Bacteroidetes': ['Bacteroidia', 'Flavobacteriia', 'Sphingobacteriia'],
        'Actinobacteria': ['Actinobacteria', 'Coriobacteriia'],
        'Verrucomicrobia': ['Verrucomicrobiae'],
        'Planctomycetes': ['Planctomycetacia'],
        'Cyanobacteria': ['Oxyphotobacteria'],
        'Acidobacteria': ['Acidobacteriia']
    }
    
    # Gêneros comuns
    genera = [
        'Escherichia', 'Bacillus', 'Bacteroides', 'Streptococcus', 'Lactobacillus',
        'Clostridium', 'Prevotella', 'Akkermansia', 'Faecalibacterium', 'Bifidobacterium',
        'Ruminococcus', 'Roseburia', 'Blautia', 'Coprococcus', 'Dorea'
    ]
    
    feature_ids = [f"ASV_{i:04d}" for i in range(1, n_features + 1)]
    
    taxonomies = []
    confidence_scores = []
    
    for _ in range(n_features):
        # Escolher filo (com distribuição realista)
        phylum = random.choices(
            phyla,
            weights=[30, 25, 20, 10, 5, 4, 3, 3],  # Proteobacteria mais comum
            k=1
        )[0]
        
        # Escolher classe
        class_name = random.choice(classes[phylum])
        
        # Escolher gênero (com chance de não classificado)
        if random.random() > 0.3:  # 70% classificado até gênero
            genus = random.choice(genera)
            taxonomy = f"k__Bacteria; p__{phylum}; c__{class_name}; o__; f__; g__{genus}; s__"
            confidence = random.uniform(0.85, 0.99)
        elif random.random() > 0.5:  # Classificado até classe
            taxonomy = f"k__Bacteria; p__{phylum}; c__{class_name}; o__; f__; g__; s__"
            confidence = random.uniform(0.70, 0.85)
        else:  # Classificado apenas até filo
            taxonomy = f"k__Bacteria; p__{phylum}; c__; o__; f__; g__; s__"
            confidence = random.uniform(0.60, 0.75)
        
        taxonomies.append(taxonomy)
        confidence_scores.append(confidence)
    
    df = pd.DataFrame({
        'Feature ID': feature_ids,
        'Taxon': taxonomies,
        'Confidence': confidence_scores
    })
    
    output_file = OUTPUT_DIR / "taxonomy.tsv"
    df.to_csv(output_file, sep='\t', index=False)
    
    print(f"  ✅ Criado: {output_file}")
    print(f"     • {n_features} features (ASVs)")
    print(f"     • {len(phyla)} filos diferentes")
    print()
    
    return df


# ============================================================================
# 5. GERAR DADOS DE RAREFAÇÃO
# ============================================================================

def gerar_rarefacao(sample_ids):
    """Gera curvas de rarefação"""
    print("📈 Gerando dados de rarefação...")
    
    n_samples = len(sample_ids)
    
    # Profundidades de sequenciamento
    depths = [1000, 5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000, 45000, 50000]
    
    data = {}
    
    for sample_id in sample_ids:
        # Parâmetros da curva para cada amostra
        max_features = random.randint(150, 350)  # Máximo de features
        saturation_rate = random.uniform(0.0001, 0.0003)  # Taxa de saturação
        
        curve = []
        for depth in depths:
            # Modelo de saturação: features = max * (1 - e^(-rate * depth))
            features = max_features * (1 - np.exp(-saturation_rate * depth))
            
            # Adicionar ruído
            features += random.uniform(-5, 5)
            features = max(0, features)  # Não pode ser negativo
            
            curve.append(features)
        
        data[sample_id] = curve
    
    df = pd.DataFrame(data, index=depths).T
    df.index.name = 'sample-id'
    
    output_file = OUTPUT_DIR / "rarefaction.tsv"
    df.to_csv(output_file, sep='\t')
    
    print(f"  ✅ Criado: {output_file}")
    print(f"     • {n_samples} amostras")
    print(f"     • {len(depths)} profundidades ({min(depths)} - {max(depths)})")
    print()
    
    return df


# ============================================================================
# 6. GERAR METADATA
# ============================================================================

def gerar_metadata(sample_ids):
    """Gera arquivo de metadata"""
    print("📋 Gerando metadata...")
    
    n_samples = len(sample_ids)
    
    # Dividir amostras em grupos
    grupos = ['Controle', 'Tratamento_A', 'Tratamento_B']
    locais = ['Floresta', 'Rio', 'Solo']
    
    data = {
        'sample-id': sample_ids,
        'grupo': [random.choice(grupos) for _ in range(n_samples)],
        'local': [random.choice(locais) for _ in range(n_samples)],
        'pH': np.random.uniform(4.5, 7.5, n_samples),
        'temperatura': np.random.uniform(20, 35, n_samples),
        'umidade': np.random.uniform(40, 90, n_samples)
    }
    
    df = pd.DataFrame(data)
    
    output_file = OUTPUT_DIR / "metadata.tsv"
    df.to_csv(output_file, sep='\t', index=False)
    
    print(f"  ✅ Criado: {output_file}")
    print(f"     • {n_samples} amostras")
    print(f"     • 3 grupos: {', '.join(grupos)}")
    print(f"     • 3 locais: {', '.join(locais)}")
    print(f"     • 3 variáveis ambientais (pH, temperatura, umidade)")
    print()
    
    return df


# ============================================================================
# 7. GERAR TABELA DE ABUNDÂNCIAS
# ============================================================================

def gerar_tabela_abundancias(sample_ids, n_features=200):
    """Gera tabela de abundâncias (feature table)"""
    print("📊 Gerando tabela de abundâncias...")
    
    feature_ids = [f"ASV_{i:04d}" for i in range(1, n_features + 1)]
    
    # Gerar abundâncias com distribuição realista (muitos zeros, alguns valores altos)
    data = {}
    
    for sample_id in sample_ids:
        abundances = []
        for _ in range(n_features):
            # 60% de chance de ser zero (esparsidade)
            if random.random() < 0.6:
                abundances.append(0)
            else:
                # Distribuição log-normal para abundâncias
                abundances.append(int(np.random.lognormal(3, 2)))
        
        data[sample_id] = abundances
    
    df = pd.DataFrame(data, index=feature_ids)
    df.index.name = '#OTU ID'
    
    output_file = OUTPUT_DIR / "feature_table.tsv"
    df.to_csv(output_file, sep='\t')
    
    print(f"  ✅ Criado: {output_file}")
    print(f"     • {n_features} features")
    print(f"     • {len(sample_ids)} amostras")
    print(f"     • Matriz esparsa (abundâncias)")
    print()
    
    return df


# ============================================================================
# 8. GERAR README
# ============================================================================

def gerar_readme():
    """Gera README explicativo"""
    print("📝 Gerando README...")
    
    readme_content = """# Dados de Teste QIIME 2 - YARA

## 📋 Descrição

Este diretório contém **dados sintéticos** gerados para testar todas as funcionalidades do chatbot YARA.

**⚠️ IMPORTANTE:** Estes são dados de teste fictícios, não representam análises reais.

## 📊 Arquivos Disponíveis

### Diversidade Alfa
- **diversidade_alfa.tsv**: Métricas de diversidade alfa (Shannon, Simpson, etc.)
  - 15 amostras
  - 5 métricas diferentes

### Diversidade Beta
- **distance_matrix_braycurtis.tsv**: Matriz de distâncias Bray-Curtis
  - Matriz 15x15
  - Valores entre 0 (idênticas) e 1 (totalmente diferentes)

- **pcoa_coordinates.tsv**: Coordenadas PCoA
  - 3 componentes principais (PC1, PC2, PC3)

### Taxonomia
- **taxonomy.tsv**: Classificação taxonômica
  - 200 features (ASVs)
  - 8 filos diferentes
  - Níveis: Reino → Filo → Classe → Ordem → Família → Gênero → Espécie

### Rarefação
- **rarefaction.tsv**: Curvas de rarefação
  - 15 amostras
  - 11 profundidades (1.000 - 50.000 sequências)

### Abundâncias
- **feature_table.tsv**: Tabela de abundâncias
  - 200 features x 15 amostras
  - Matriz esparsa (muitos zeros)

### Metadata
- **metadata.tsv**: Informações das amostras
  - Grupos experimentais (Controle, Tratamento_A, Tratamento_B)
  - Locais de coleta (Floresta, Rio, Solo)
  - Variáveis ambientais (pH, temperatura, umidade)

## 🧪 Como Usar

### 1. Testar no Chatbot

```bash
cd ~/Documentos/pibic/yara
conda activate yara_rasa

# Treinar modelo
make train

# Terminal 1: Actions
make actions

# Terminal 2: Chat
make shell
```

**Perguntas para testar:**
- "Quais dados tenho disponíveis?"
- "O que é diversidade alfa?"
- "Analisa rarefação"
- "Quais os grupos mais abundantes?"
- "Exporta relatório"

### 2. Testar nos Notebooks

```bash
conda activate yara_notebooks
jupyter lab

# Abrir notebooks:
# - notebooks/notebook_exploracao_qiime2.ipynb
# - notebooks/notebook_diversidade_beta.ipynb
# - notebooks/03_analise_rarefacao.ipynb
```

### 3. Usar Programaticamente

```python
import pandas as pd

# Carregar diversidade alfa
df_alpha = pd.read_csv('data/qiime2/diversidade_alfa.tsv', sep='\\t', index_col=0)

# Carregar rarefação
df_rarefaction = pd.read_csv('data/qiime2/rarefaction.tsv', sep='\\t', index_col=0)

# Usar com YARA
from actions.utils.rarefaction_analyzer import RarefactionAnalyzer
analyzer = RarefactionAnalyzer(df_rarefaction)
```

## 🔄 Regenerar Dados

Para gerar novos dados de teste:

```bash
python gerar_dados_teste.py
```

## 📚 Referências

- [QIIME 2 Documentation](https://docs.qiime2.org/)
- [QIIME 2 Tutorials](https://docs.qiime2.org/2024.10/tutorials/)

---

**Gerado por:** YARA - Your Assistant for Results Analysis  
**Projeto:** IFAM - EMBRAPA - INPA  
**Data:** Outubro 2025
"""
    
    output_file = OUTPUT_DIR / "README.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"  ✅ Criado: {output_file}")
    print()


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Função principal"""
    
    # 1. Diversidade Alfa
    df_alpha = gerar_diversidade_alfa(n_samples=15)
    sample_ids = list(df_alpha.index)
    
    # 2. Diversidade Beta
    gerar_matriz_distancias(sample_ids)
    gerar_pcoa_coordinates(sample_ids)
    
    # 3. Taxonomia
    gerar_taxonomia(n_features=200)
    
    # 4. Rarefação
    gerar_rarefacao(sample_ids)
    
    # 5. Metadata
    gerar_metadata(sample_ids)
    
    # 6. Tabela de Abundâncias
    gerar_tabela_abundancias(sample_ids, n_features=200)
    
    # 7. README
    gerar_readme()
    
    # Resumo final
    print("=" * 60)
    print("✅ GERAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print()
    print(f"📁 Diretório: {OUTPUT_DIR.absolute()}")
    print()
    print("📊 Arquivos criados:")
    files = sorted(OUTPUT_DIR.glob("*"))
    for f in files:
        size = f.stat().st_size / 1024  # KB
        print(f"  • {f.name:<35} ({size:>6.1f} KB)")
    
    print()
    print("🚀 Próximos passos:")
    print("  1. Treinar modelo: make train")
    print("  2. Testar chatbot: make shell")
    print("  3. Abrir notebooks: jupyter lab")
    print()
    print("💡 Leia data/qiime2/README.md para mais informações!")
    print()


if __name__ == "__main__":
    main()
