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