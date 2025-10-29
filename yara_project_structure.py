#!/usr/bin/env python3
"""
Script simplificado para criar estrutura YARA
Versão corrigida e testada
"""

import os
from pathlib import Path

def create_file(filepath, content):
    """Cria arquivo com conteúdo"""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ {filepath}")

def main():
    print("🚀 Criando estrutura YARA...\n")
    
    base = Path.cwd()
    
    # Diretórios
    dirs = ['data', 'actions', 'notebooks', 'tests', 'docs', 'logs', 'models', '.vscode']
    for d in dirs:
        (base / d).mkdir(exist_ok=True)
    print(f"✅ Diretórios criados\n")
    
    # domain.yml
    create_file(base / "domain.yml", """version: "3.1"

intents:
  - cumprimentar
  - despedir
  - agradecer
  - explicar_diversidade_alfa
  - explicar_diversidade_beta
  - mostrar_taxonomia

responses:
  utter_cumprimentar:
  - text: "Olá! Sou a YARA, sua assistente para análise QIIME 2. Como posso ajudar?"
  
  utter_despedir:
  - text: "Até logo! 👋"
  
  utter_agradecer:
  - text: "Por nada! 😊"

actions:
  - action_explicar_diversidade_alfa
  - action_explicar_diversidade_beta
  - action_mostrar_taxonomia

session_config:
  session_expiration_time: 60
  carry_over_slots_to_new_session: true
""")

    # config.yml
    create_file(base / "config.yml", """recipe: default.v1
language: pt

pipeline:
  - name: WhitespaceTokenizer
  - name: RegexFeaturizer
  - name: LexicalSyntacticFeaturizer
  - name: CountVectorsFeaturizer
  - name: CountVectorsFeaturizer
    analyzer: char_wb
    min_ngram: 1
    max_ngram: 4
  - name: DIETClassifier
    epochs: 100
  - name: EntitySynonymMapper
  - name: ResponseSelector
    epochs: 100
  - name: FallbackClassifier
    threshold: 0.3

policies:
  - name: MemoizationPolicy
  - name: RulePolicy
  - name: TEDPolicy
    max_history: 10
    epochs: 100
""")

    # data/nlu.yml
    create_file(base / "data/nlu.yml", """version: "3.1"

nlu:
- intent: cumprimentar
  examples: |
    - oi
    - olá
    - bom dia
    - hey

- intent: despedir
  examples: |
    - tchau
    - até logo
    - até mais

- intent: agradecer
  examples: |
    - obrigado
    - valeu
    - obrigada

- intent: explicar_diversidade_alfa
  examples: |
    - o que é diversidade alfa?
    - explica diversidade alfa
    - como interpretar shannon
    - índice de simpson

- intent: explicar_diversidade_beta
  examples: |
    - o que é diversidade beta?
    - explica pcoa
    - unifrac
    - diferença entre amostras

- intent: mostrar_taxonomia
  examples: |
    - mostra taxonomia
    - composição taxonômica
    - quais grupos
    - classificação
""")

    # data/stories.yml
    create_file(base / "data/stories.yml", """version: "3.1"

stories:
- story: conversa básica
  steps:
  - intent: cumprimentar
  - action: utter_cumprimentar
  - intent: explicar_diversidade_alfa
  - action: action_explicar_diversidade_alfa
  - intent: agradecer
  - action: utter_agradecer
""")

    # data/rules.yml
    create_file(base / "data/rules.yml", """version: "3.1"

rules:
- rule: Cumprimentar
  steps:
  - intent: cumprimentar
  - action: utter_cumprimentar

- rule: Despedir
  steps:
  - intent: despedir
  - action: utter_despedir
""")

    # actions/__init__.py
    create_file(base / "actions/__init__.py", "")

    # actions/actions.py
    create_file(base / "actions/actions.py", """from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionExplicarDiversidadeAlfa(Action):
    def name(self) -> Text:
        return "action_explicar_diversidade_alfa"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        msg = (
            "📊 **Diversidade Alfa**\\n\\n"
            "É a diversidade de espécies DENTRO de cada amostra.\\n\\n"
            "Principais métricas:\\n"
            "• Shannon: equilíbrio geral\\n"
            "• Simpson: dominância\\n"
            "• Observed Features: riqueza\\n"
        )
        dispatcher.utter_message(text=msg)
        return []

class ActionExplicarDiversidadeBeta(Action):
    def name(self) -> Text:
        return "action_explicar_diversidade_beta"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        msg = (
            "📊 **Diversidade Beta**\\n\\n"
            "Mede diferença ENTRE amostras.\\n\\n"
            "• Bray-Curtis: diferença em abundância\\n"
            "• UniFrac: relações evolutivas\\n"
            "• PCoA: visualização das distâncias\\n"
        )
        dispatcher.utter_message(text=msg)
        return []

class ActionMostrarTaxonomia(Action):
    def name(self) -> Text:
        return "action_mostrar_taxonomia"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        msg = (
            "🦠 **Composição Taxonômica**\\n\\n"
            "Níveis: Reino > Filo > Classe > Ordem > Família > Gênero > Espécie\\n\\n"
            "Use dados do QIIME 2 para visualizar.\\n"
        )
        dispatcher.utter_message(text=msg)
        return []
""")

    # endpoints.yml
    create_file(base / "endpoints.yml", """action_endpoint:
  url: "http://localhost:5055/webhook"
""")

    # credentials.yml
    create_file(base / "credentials.yml", """# Configurações de canais
# Adicionar tokens quando necessário
""")

    # Makefile
    create_file(base / "Makefile", """.PHONY: help train shell actions test clean

help:
\t@echo "Comandos:"
\t@echo "  make train   - Treinar modelo"
\t@echo "  make shell   - Chat teste"
\t@echo "  make actions - Servidor actions"
\t@echo "  make clean   - Limpar cache"

train:
\trasa train

shell:
\trasa shell

actions:
\trasa run actions

test:
\trasa test

clean:
\tfind . -type d -name "__pycache__" -exec rm -rf {} +
\tfind . -type f -name "*.pyc" -delete
""")

    # .gitignore
    create_file(base / ".gitignore", """__pycache__/
*.py[cod]
models/
.rasa/
.ipynb_checkpoints/
*.log
.env
credentials.yml
""")

    # README.md
    create_file(base / "README.md", """# 🧬 YARA - Your Assistant for Results Analysis

Agente conversacional para interpretação de resultados QIIME 2.

## Início Rápido

```bash
# Ativar ambiente
conda activate yara

# Treinar
make train

# Testar
make shell
```

## Estrutura

```
yara/
├── domain.yml      # Definições
├── config.yml      # Configuração
├── data/           # Dados de treino
├── actions/        # Lógica customizada
├── notebooks/      # Análises
└── models/         # Modelos treinados
```

## Comandos

- `make train` - Treinar modelo
- `make shell` - Chat teste
- `make actions` - Servidor actions
- `make clean` - Limpar cache

## Desenvolvimento

1. Editar `data/nlu.yml` - adicionar exemplos
2. Editar `actions/actions.py` - adicionar lógica
3. `make train` - retreinar
4. `make shell` - testar

---

**IFAM - Promovendo soberania científica na Amazônia** 🌳
""")

    # requirements.txt
    create_file(base / "requirements.txt", """rasa==3.6.0
rasa-sdk==3.6.0
pandas==2.0.3
numpy==1.24.3
matplotlib==3.7.2
seaborn==0.12.2
scikit-learn==1.3.0
jupyter==1.0.0
ipykernel==6.24.0
python-telegram-bot==20.4
""")

    # VS Code settings
    create_file(base / ".vscode/settings.json", """{
  "python.defaultInterpreterPath": "${env:HOME}/miniconda3/envs/yara/bin/python",
  "python.linting.enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.trimTrailingWhitespace": true,
  "[yaml]": {
    "editor.tabSize": 2
  }
}
""")

    # Notebook exemplo
    notebook_content = """{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["# Análise QIIME 2\\n", "\\n", "Exemplo de exploração de dados."]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": ["import pandas as pd\\n", "import matplotlib.pyplot as plt\\n", "\\n", "# Carregar dados\\n", "# df = pd.read_csv('dados.tsv', sep='\\\\t')"]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python (YARA)",
   "language": "python",
   "name": "yara"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
"""
    create_file(base / "notebooks/exemplo.ipynb", notebook_content)

    print("\n" + "="*60)
    print("✅ ESTRUTURA CRIADA COM SUCESSO!")
    print("="*60)
    print(f"\n📁 Local: {base}")
    print("\n📋 Próximos passos:")
    print("  1. rasa train")
    print("  2. rasa shell")
    print("  3. code .  (abrir VS Code)")
    print("\n🎉 Pronto para começar!\n")

if __name__ == "__main__":
    main()
