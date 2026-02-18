"""
YARA Actions - Integrado com QIIME2 Parser
===========================================

Actions customizadas que leem dados reais do QIIME 2
quando disponíveis, com fallback para respostas genéricas.

Autor: Projeto YARA - IFAM
Data: Outubro 2025
"""

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from pathlib import Path
import pandas as pd

# Importar parser QIIME2
try:
    from actions.utils.qiime_parser_module import (
        QIIME2Parser,
        AlphaDiversityAnalyzer,
        BetaDiversityAnalyzer,
        load_qiime2_data
    )
    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False
    print("⚠️  Parser QIIME2 não disponível - usando respostas genéricas")


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def get_data_path() -> Path:
    """Retorna caminho para diretório de dados"""
    return Path("data/qiime2")


def check_data_available(data_type: str = "alpha") -> bool:
    """
    Verifica se há dados disponíveis
    
    Args:
        data_type: Tipo de dado ('alpha', 'beta', 'taxonomy')
    
    Returns:
        True se dados existem
    """
    data_path = get_data_path()
    
    if not data_path.exists():
        return False
    
    # Procurar arquivos relevantes
    patterns = {
        'alpha': ['*alpha*.tsv', '*shannon*.tsv', '*simpson*.tsv', '*diversidade_alfa*.tsv'],
        'beta': ['*beta*.tsv', '*distance*.tsv', '*unifrac*.tsv'],
        'taxonomy': ['*taxonomy*.tsv', '*taxa*.tsv']
    }
    
    for pattern in patterns.get(data_type, []):
        if list(data_path.glob(pattern)):
            return True
    
    return False


def load_alpha_diversity_data() -> pd.DataFrame:
    """
    Carrega dados de diversidade alfa
    
    Returns:
        DataFrame ou None se não houver dados
    """
    data_path = get_data_path()
    
    # Procurar arquivo de diversidade alfa
    for pattern in ['*alpha*.tsv', '*shannon*.tsv', '*diversidade_alfa*.tsv']:
        files = list(data_path.glob(pattern))
        if files:
            try:
                df = pd.read_csv(files[0], sep='\t', index_col=0)
                return df
            except Exception as e:
                print(f"Erro ao carregar {files[0]}: {e}")
    
    return None


def format_alpha_stats(df: pd.DataFrame, metric: str = 'Shannon') -> str:
    """
    Formata estatísticas de diversidade alfa
    
    Args:
        df: DataFrame com dados
        metric: Nome da métrica
    
    Returns:
        String formatada
    """
    if metric not in df.columns:
        # Tentar encontrar métrica similar
        for col in df.columns:
            if metric.lower() in col.lower():
                metric = col
                break
    
    if metric not in df.columns:
        return f"Métrica '{metric}' não encontrada nos dados."
    
    stats = df[metric].describe()
    
    texto = f"""📊 **Análise de {metric}**

📈 Estatísticas dos seus dados:
• Média: {stats['mean']:.2f}
• Mediana: {stats['50%']:.2f}
• Desvio padrão: {stats['std']:.2f}
• Mínimo: {stats['min']:.2f}
• Máximo: {stats['max']:.2f}

📋 Total de amostras: {len(df)}

💡 Interpretação:
"""
    
    # Interpretar média
    mean_val = stats['mean']
    if 'shannon' in metric.lower():
        if mean_val < 1.5:
            texto += "• Diversidade BAIXA na maioria das amostras\n"
            texto += "• Comunidades dominadas por poucas espécies"
        elif mean_val < 2.5:
            texto += "• Diversidade MODERADA\n"
            texto += "• Comunidades relativamente equilibradas"
        elif mean_val < 3.5:
            texto += "• Diversidade ALTA\n"
            texto += "• Comunidades bem equilibradas e complexas"
        else:
            texto += "• Diversidade MUITO ALTA\n"
            texto += "• Comunidades extremamente complexas"
    
    return texto


# ============================================================================
# ACTIONS
# ============================================================================

class ActionExplicarDiversidadeAlfa(Action):
    """Action para explicar diversidade alfa com dados reais quando disponível"""
    
    def name(self) -> Text:
        return "action_explicar_diversidade_alfa"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Tentar carregar dados reais
        if PARSER_AVAILABLE and check_data_available('alpha'):
            try:
                df = load_alpha_diversity_data()
                
                if df is not None:
                    # Resposta com dados reais
                    mensagem = "🧬 **Diversidade Alfa - Análise dos Seus Dados**\n\n"
                    
                    # Verificar métricas disponíveis
                    metricas_disponiveis = []
                    for metrica in ['Shannon', 'Shannon_entropy', 'shannon', 
                                   'Simpson', 'simpson', 'observed_features',
                                   'Observed Features', 'observed_otus']:
                        for col in df.columns:
                            if metrica.lower() in col.lower():
                                metricas_disponiveis.append(col)
                    
                    if metricas_disponiveis:
                        # Analisar primeira métrica encontrada
                        metrica = metricas_disponiveis[0]
                        mensagem += format_alpha_stats(df, metrica)
                    else:
                        # Dados encontrados mas sem métricas reconhecidas
                        mensagem += f"📊 Dados carregados com {len(df)} amostras\n"
                        mensagem += f"Métricas disponíveis: {', '.join(df.columns)}\n\n"
                        mensagem += self._get_generic_explanation()
                    
                    dispatcher.utter_message(text=mensagem)
                    return []
            
            except Exception as e:
                print(f"Erro ao processar dados: {e}")
                # Continuar para resposta genérica
        
        # Resposta genérica (fallback)
        mensagem = self._get_generic_explanation()
        dispatcher.utter_message(text=mensagem)
        return []
    
    def _get_generic_explanation(self) -> str:
        """Retorna explicação genérica"""
        return """📊 **Diversidade Alfa**

É a diversidade de espécies DENTRO de cada amostra.

**Principais métricas:**
• **Shannon**: equilíbrio entre riqueza e equitabilidade
  - Valores típicos: 1.5 a 3.5
  - Maior valor = mais diversidade

• **Simpson**: probabilidade de dominância
  - Valores de 0 a 1
  - Próximo de 1 = alta diversidade

• **Observed Features**: número de ASVs/OTUs detectados
  - Contagem simples de espécies
  - Mais features = mais riqueza

• **Chao1**: estimativa de riqueza total
  - Estima espécies não detectadas

• **Faith PD**: diversidade filogenética
  - Considera relações evolutivas

**Interpretação:**
✅ Valores altos = comunidades mais diversas e complexas
⚠️  Valores baixos = comunidades dominadas por poucas espécies

💡 **Dica:** Adicione seus dados em `data/qiime2/` para análise personalizada!"""


class ActionExplicarDiversidadeBeta(Action):
    """Action para explicar diversidade beta"""
    
    def name(self) -> Text:
        return "action_explicar_diversidade_beta"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Verificar se há dados de beta diversidade
        has_data = PARSER_AVAILABLE and check_data_available('beta')
        
        mensagem = "📊 **Diversidade Beta**\n\n"
        
        if has_data:
            mensagem += "🔍 Detectei dados de diversidade beta no projeto!\n\n"
        
        mensagem += """Mede a diferença na composição de espécies ENTRE amostras.

**Principais métricas:**
• **Bray-Curtis**: diferença baseada em abundância
  - Mais comum para dados de contagem
  - Valores de 0 (idênticas) a 1 (totalmente diferentes)

• **Jaccard**: presença/ausência de espécies
  - Ignora abundâncias
  - Útil para dados binários

• **UniFrac**: considera relações evolutivas
  - **Weighted**: leva em conta abundâncias
  - **Unweighted**: apenas presença/ausência
  - Requer árvore filogenética

**PCoA (Principal Coordinates Analysis):**
Visualiza as distâncias entre amostras em gráfico 2D/3D

📍 **Como interpretar PCoA:**
• Amostras próximas = comunidades microbianas similares
• Amostras distantes = comunidades diferentes
• Grupos separados = diferenças significativas

**PERMANOVA:**
Teste estatístico para verificar se grupos são significativamente diferentes
• P < 0.05 = grupos têm composições diferentes"""

        if has_data:
            mensagem += "\n\n💡 Use 'analisar beta diversidade' para análise detalhada!"
        
        dispatcher.utter_message(text=mensagem)
        return []


class ActionMostrarTaxonomia(Action):
    """Action para explicar taxonomia"""
    
    def name(self) -> Text:
        return "action_mostrar_taxonomia"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Verificar se há dados de taxonomia
        has_data = PARSER_AVAILABLE and check_data_available('taxonomy')
        
        mensagem = "🦠 **Composição Taxonômica**\n\n"
        
        if has_data:
            mensagem += "🔍 Detectei dados taxonômicos no projeto!\n\n"
        
        mensagem += """Classificação hierárquica dos microrganismos encontrados.

**Hierarquia taxonômica (do maior para o menor):**
1️⃣ **Reino** (Kingdom) - ex: Bacteria, Archaea
2️⃣ **Filo** (Phylum) - ex: Proteobacteria, Firmicutes
3️⃣ **Classe** (Class) - ex: Gammaproteobacteria
4️⃣ **Ordem** (Order) - ex: Enterobacterales
5️⃣ **Família** (Family) - ex: Enterobacteriaceae
6️⃣ **Gênero** (Genus) - ex: Escherichia
7️⃣ **Espécie** (Species) - ex: Escherichia coli

**IMPORTANTE:**
⚠️ Nem todas as sequências são classificadas até espécie.

**Por quê?**
• Bancos de dados incompletos
• Sequências 16S rRNA são curtas
• Algumas espécies são muito similares
• Microrganismos ainda não catalogados

**O que é normal?**
✅ 70-90% classificadas até Filo
✅ 50-80% classificadas até Família  
✅ 30-60% classificadas até Gênero
❓ 10-30% classificadas até Espécie

**Representação comum:**
"Unassigned" ou "Unknown" = sequência não classificada naquele nível"""

        if has_data:
            mensagem += "\n\n💡 Use 'mostrar grupos taxonômicos' para ver seus dados!"
        
        dispatcher.utter_message(text=mensagem)
        return []


class ActionListarDadosDisponiveis(Action):
    """Action para listar dados disponíveis no projeto"""
    
    def name(self) -> Text:
        return "action_listar_dados_disponiveis"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        data_path = get_data_path()
        
        if not data_path.exists():
            mensagem = """❌ Nenhum dado encontrado.

📁 **Como adicionar dados:**
1. Coloque arquivos QIIME 2 em: `data/qiime2/`
2. Formatos aceitos: `.tsv`, `.qzv`, `.biom`
3. Exemplos de nomes:
   - `shannon_diversity.tsv`
   - `distance_matrix.tsv`
   - `taxonomy.tsv`

💡 Após adicionar, converse comigo novamente!"""
        else:
            # Listar arquivos
            arquivos = list(data_path.glob("*"))
            
            if not arquivos:
                mensagem = "📁 Diretório `data/qiime2/` existe mas está vazio.\n\n"
                mensagem += "Adicione seus arquivos QIIME 2 para análise!"
            else:
                mensagem = f"📊 **Dados Disponíveis ({len(arquivos)} arquivos)**\n\n"
                
                # Categorizar arquivos
                alpha_files = [f for f in arquivos if any(x in f.name.lower() 
                              for x in ['alpha', 'shannon', 'simpson', 'diversity'])]
                beta_files = [f for f in arquivos if any(x in f.name.lower() 
                             for x in ['beta', 'distance', 'unifrac', 'pcoa'])]
                taxa_files = [f for f in arquivos if any(x in f.name.lower() 
                             for x in ['taxonomy', 'taxa', 'classification'])]
                
                if alpha_files:
                    mensagem += "📈 **Diversidade Alfa:**\n"
                    for f in alpha_files[:3]:
                        mensagem += f"  • {f.name}\n"
                    mensagem += "\n"
                
                if beta_files:
                    mensagem += "📊 **Diversidade Beta:**\n"
                    for f in beta_files[:3]:
                        mensagem += f"  • {f.name}\n"
                    mensagem += "\n"
                
                if taxa_files:
                    mensagem += "🦠 **Taxonomia:**\n"
                    for f in taxa_files[:3]:
                        mensagem += f"  • {f.name}\n"
                    mensagem += "\n"
                
                outros = len(arquivos) - len(alpha_files) - len(beta_files) - len(taxa_files)
                if outros > 0:
                    mensagem += f"📁 Outros arquivos: {outros}\n\n"
                
                mensagem += "💡 Pergunte sobre qualquer análise que eu te ajudo!"
        
        dispatcher.utter_message(text=mensagem)
        return []


class ActionDefaultFallback(Action):
    """Action de fallback quando não entende"""
    
    def name(self) -> Text:
        return "action_default_fallback"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        mensagem = """Desculpe, não entendi sua pergunta. 🤔

**Posso te ajudar com:**
• Diversidade Alfa (Shannon, Simpson, riqueza)
• Diversidade Beta (PCoA, distâncias, PERMANOVA)
• Taxonomia (classificação de microrganismos)
• Rarefação (curvas de amostragem)
• Listar dados disponíveis

**Exemplos de perguntas:**
• "O que é diversidade alfa?"
• "Explica PCoA"
• "Quais dados tenho disponíveis?"

Tente reformular sua pergunta! 😊"""
        
        dispatcher.utter_message(text=mensagem)
        return []


# ============================================================================
# ACTIONS PARA REGISTRO
# ============================================================================

# Esta lista é usada pelo Rasa para descobrir actions
__all__ = [
    'ActionExplicarDiversidadeAlfa',
    'ActionExplicarDiversidadeBeta',
    'ActionMostrarTaxonomia',
    'ActionListarDadosDisponiveis',
    'ActionDefaultFallback'
]


class ActionAnalisarRarefacao(Action):
    """Action para análise de curvas de rarefação"""
    
    def name(self) -> Text:
        return "action_analisar_rarefacao"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            from actions.utils.rarefaction_analyzer import (
                RarefactionAnalyzer,
                load_rarefaction_data,
                analyze_rarefaction_file
            )
            
            # Procurar arquivo de rarefação
            data_path = get_data_path()
            rarefaction_files = list(data_path.glob("*rarefaction*.tsv")) + \
                              list(data_path.glob("*rarefacao*.tsv"))
            
            if not rarefaction_files:
                mensagem = """📊 **Análise de Rarefação**

❌ Nenhum arquivo de rarefação encontrado.

**Como adicionar:**
1. Exporte curvas de rarefação do QIIME 2
2. Salve em `data/qiime2/rarefaction.tsv`
3. Pergunte novamente!

**O que é rarefação?**
Curvas de rarefação mostram se o sequenciamento foi suficiente para capturar
a diversidade microbiana da amostra. Uma curva que atinge um "plateau" indica
que a maioria das espécies foi detectada."""
                
                dispatcher.utter_message(text=mensagem)
                return []
            
            # Analisar primeiro arquivo encontrado
            results = analyze_rarefaction_file(str(rarefaction_files[0]))
            
            # Gerar mensagem com interpretação
            mensagem = results['interpretation']
            
            dispatcher.utter_message(text=mensagem)
            
        except Exception as e:
            print(f"Erro na análise de rarefação: {e}")
            mensagem = """⚠️ Erro ao analisar rarefação.

Verifique se o arquivo está no formato correto (TSV do QIIME 2)."""
            dispatcher.utter_message(text=mensagem)
        
        return []


class ActionExportarRelatorio(Action):
    """Action para exportar relatório em diferentes formatos"""
    
    def name(self) -> Text:
        return "action_exportar_relatorio"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            from actions.utils.report_generator import create_comprehensive_report
            
            # Coletar todas as análises disponíveis
            analyses = {}
            
            # Diversidade Alfa
            if check_data_available('alpha'):
                df = load_alpha_diversity_data()
                if df is not None:
                    stats = df.describe().to_dict()
                    analyses['alpha'] = f"Análise de {len(df)} amostras com métricas: {', '.join(df.columns)}"
            
            # Diversidade Beta
            if check_data_available('beta'):
                analyses['beta'] = "Análise de distâncias entre amostras disponível"
            
            # Taxonomia
            if check_data_available('taxonomy'):
                analyses['taxonomy'] = "Classificação taxonômica disponível"
            
            if not analyses:
                mensagem = """📄 **Exportar Relatório**

❌ Nenhum dado disponível para gerar relatório.

Adicione dados em `data/qiime2/` e tente novamente!"""
                dispatcher.utter_message(text=mensagem)
                return []
            
            # Gerar relatório em Markdown
            md_path = create_comprehensive_report(analyses, output_format="markdown")
            
            # Gerar relatório em HTML
            html_path = create_comprehensive_report(analyses, output_format="html")
            
            mensagem = f"""📄 **Relatórios Gerados com Sucesso!**

✅ Markdown: `{md_path}`
✅ HTML: `{html_path}`

**Conteúdo incluído:**
"""
            for key in analyses.keys():
                mensagem += f"• {key.title()}\n"
            
            mensagem += "\n💡 Abra os arquivos para visualizar os resultados completos!"
            
            dispatcher.utter_message(text=mensagem)
            
        except Exception as e:
            print(f"Erro ao exportar relatório: {e}")
            mensagem = """⚠️ Erro ao gerar relatório.

Verifique os logs para mais detalhes."""
            dispatcher.utter_message(text=mensagem)
        
        return []


class ActionCompararGrupos(Action):
    """Action para comparar diversidade entre grupos"""
    
    def name(self) -> Text:
        return "action_comparar_grupos"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Verificar se há dados para análise
        data_path = get_data_path()
        metadata_file = data_path / "metadata.tsv"
        alpha_file = data_path / "diversidade_alfa.tsv"
        
        if metadata_file.exists() and alpha_file.exists():
            try:
                from actions.utils.statistics import calculate_kruskal_wallis, get_group_stats
                
                # Carregar dados
                metadata = pd.read_csv(metadata_file, sep='\t')
                alpha = pd.read_csv(alpha_file, sep='\t', index_col=0)
                
                # Merge dados
                # Assumindo que o índice do alpha é o ID da amostra
                if 'sample-id' in metadata.columns:
                    metadata.set_index('sample-id', inplace=True)
                
                # Juntar (inner join para garantir que apenas amostras em ambos sejam usadas)
                df_full = alpha.join(metadata, how='inner')
                
                if df_full.empty:
                    dispatcher.utter_message(text="⚠️ Erro: Amostras do metadata não correspondem aos dados de diversidade.")
                    return []
                
                # Identificar coluna de grupos (procurar por 'grupo', 'group', 'treatment', etc)
                group_col = None
                for col in df_full.columns:
                    if col.lower() in ['grupo', 'group', 'treatment', 'tratamento', 'class']:
                        group_col = col
                        break
                
                if not group_col:
                    dispatcher.utter_message(text="⚠️ Não encontrei uma coluna de grupos no metadata (ex: 'grupo', 'tratamento').")
                    return []
                
                # Escolher métrica (padrão: Shannon)
                metric = 'Shannon'
                if metric not in df_full.columns:
                    # Tentar achar outra
                    for col in df_full.columns:
                        if col.lower() in ['shannon', 'simpson', 'chao1', 'observed_features']:
                            metric = col
                            break
                            
                # Executar análise
                mensagem = f"📊 **Análise Estatística - {metric} por {group_col}**\n\n"
                
                # 1. Estatísticas Descritivas
                mensagem += get_group_stats(df_full, group_col, metric)
                mensagem += "\n"
                
                # 2. Teste Estatístico
                groups = df_full[group_col].unique()
                if len(groups) >= 2:
                    result = calculate_kruskal_wallis(df_full, group_col, metric)
                    
                    if result['success']:
                        mensagem += f"**Teste de Kruskal-Wallis:**\n"
                        mensagem += f"Statistic={result['statistic']:.4f}, p-value={result['p_value']:.4f}\n\n"
                        mensagem += result['interpretation']
                    else:
                        mensagem += f"⚠️ {result['message']}"
                else:
                    mensagem += "⚠️ Menos de 2 grupos encontrados para comparação."
                
                dispatcher.utter_message(text=mensagem)
                return []
                
            except Exception as e:
                print(f"Erro na análise estatística: {e}")
                # Fallback para mensagem de ajuda
        
        # Mensagem educacional (fallback)
        mensagem = """📊 **Comparação Entre Grupos**

Para comparar grupos, você precisa:

**1. Arquivo de Metadata**
Crie um arquivo `metadata.tsv` com:
- Coluna 1: sample-id (IDs das amostras)
- Outras colunas: grupos, tratamentos, etc.

Exemplo:
```
sample-id    grupo    local
amostra1     controle    floresta
amostra2     tratamento  floresta
amostra3     controle    rio
```

**2. Testes Estatísticos Disponíveis**
• **PERMANOVA**: testa diferenças na composição beta
• **Kruskal-Wallis**: compara diversidade alfa entre grupos
• **Mann-Whitney**: compara dois grupos

**3. Como usar**
Após adicionar metadata, pergunte:
• "Comparar grupo controle com tratamento"
• "Testar diferença entre locais"
• "Fazer PERMANOVA"

💡 **Dica:** Certifique-se que os sample-ids no metadata
correspondem aos IDs nos seus dados QIIME 2!"""
        
        dispatcher.utter_message(text=mensagem)
        return []


class ActionMostrarGruposTaxonomicos(Action):
    """Action para mostrar grupos taxonômicos mais abundantes"""
    
    def name(self) -> Text:
        return "action_mostrar_grupos_taxonomicos"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Procurar arquivo de taxonomia
            data_path = get_data_path()
            taxonomy_files = list(data_path.glob("*taxonomy*.tsv")) + \
                           list(data_path.glob("*taxa*.tsv"))
            
            if not taxonomy_files:
                mensagem = """🦠 **Grupos Taxonômicos**

❌ Nenhum arquivo de taxonomia encontrado.

Adicione `taxonomy.tsv` em `data/qiime2/` e tente novamente!"""
                dispatcher.utter_message(text=mensagem)
                return []
            
            # Carregar taxonomia
            df = pd.read_csv(taxonomy_files[0], sep='\t')
            
            mensagem = f"""🦠 **Composição Taxonômica**

📊 Total de features: **{len(df)}**

"""
            
            # Tentar extrair filos mais comuns
            if 'Taxon' in df.columns:
                # Parse básico de filos
                phyla = []
                for tax_string in df['Taxon']:
                    if pd.notna(tax_string) and 'p__' in tax_string:
                        parts = tax_string.split(';')
                        for part in parts:
                            if 'p__' in part:
                                phylum = part.split('__')[1].strip()
                                if phylum:
                                    phyla.append(phylum)
                                break
                
                if phyla:
                    from collections import Counter
                    phylum_counts = Counter(phyla)
                    top_phyla = phylum_counts.most_common(10)
                    
                    mensagem += "**Top 10 Filos Mais Abundantes:**\n\n"
                    for i, (phylum, count) in enumerate(top_phyla, 1):
                        percentage = (count / len(df)) * 100
                        mensagem += f"{i}. **{phylum}**: {count} features ({percentage:.1f}%)\n"
                else:
                    mensagem += "⚠️ Não foi possível extrair informações de filos\n"
            
            mensagem += "\n💡 Use 'exportar relatório' para análise completa!"
            
            dispatcher.utter_message(text=mensagem)
            
        except Exception as e:
            print(f"Erro ao mostrar grupos taxonômicos: {e}")
            mensagem = """⚠️ Erro ao processar taxonomia.

Verifique o formato do arquivo."""
            dispatcher.utter_message(text=mensagem)
        
        return []


# Atualizar lista de actions exportadas
__all__ = [
    'ActionExplicarDiversidadeAlfa',
    'ActionExplicarDiversidadeBeta',
    'ActionMostrarTaxonomia',
    'ActionListarDadosDisponiveis',
    'ActionDefaultFallback',
    'ActionAnalisarRarefacao',
    'ActionExportarRelatorio',
    'ActionCompararGrupos',
    'ActionMostrarGruposTaxonomicos'
]