from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionExplicarDiversidadeAlfa(Action):
    def name(self) -> Text:
        return "action_explicar_diversidade_alfa"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        mensagem = """📊 **Diversidade Alfa**

É a diversidade de espécies DENTRO de cada amostra.

**Principais métricas:**
- **Shannon**: equilíbrio entre riqueza e equitabilidade
- **Simpson**: probabilidade de dominância
- **Observed Features**: número de ASVs/OTUs detectados
- **Chao1**: estimativa de riqueza total
- **Faith PD**: diversidade filogenética

**Interpretação:**
✅ Valores altos = comunidades mais diversas e complexas
⚠️  Valores baixos = comunidades dominadas por poucas espécies"""
        
        dispatcher.utter_message(text=mensagem)
        return []


class ActionExplicarDiversidadeBeta(Action):
    def name(self) -> Text:
        return "action_explicar_diversidade_beta"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        mensagem = """📊 **Diversidade Beta**

Mede a diferença na composição de espécies ENTRE amostras.

**Principais métricas:**
- **Bray-Curtis**: diferença baseada em abundância
- **Jaccard**: presença/ausência de espécies
- **UniFrac**: considera relações evolutivas
  - Weighted: leva em conta abundâncias
  - Unweighted: apenas presença/ausência

**PCoA (Principal Coordinates Analysis):**
Visualiza as distâncias entre amostras em gráfico 2D/3D
- Amostras próximas = comunidades similares
- Amostras distantes = comunidades diferentes"""
        
        dispatcher.utter_message(text=mensagem)
        return []


class ActionMostrarTaxonomia(Action):
    def name(self) -> Text:
        return "action_mostrar_taxonomia"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        mensagem = """🦠 **Composição Taxonômica**

Classificação hierárquica dos microrganismos:

**Níveis taxonômicos:**
Reino → Filo → Classe → Ordem → Família → Gênero → Espécie

⚠️ **Importante:**
Nem todas as sequências são classificadas até espécie.
Isso é normal e depende da qualidade das bases de dados de referência.

📊 Use os arquivos do QIIME 2 para visualizar gráficos detalhados."""
        
        dispatcher.utter_message(text=mensagem)
        return []
