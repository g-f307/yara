# 🧬 YARA - Your Assistant for Results Analysis

**Inteligência Artificial para geração automática de relatórios bioinformáticos na Amazônia**

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Rasa](https://img.shields.io/badge/Rasa-3.6-purple)
![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow)

---

## 📋 Sobre

YARA é um agente conversacional inteligente desenvolvido para interpretar resultados de análises metagenômicas geradas pelo QIIME 2, criado especificamente para pesquisadores da região amazônica.

### 🎯 Objetivos

- ✅ Interpretar automaticamente resultados do QIIME 2
- ✅ Gerar relatórios em linguagem natural
- ✅ Promover autonomia científica regional
- ✅ Democratizar acesso à bioinformática

### 🏛️ Instituições

- Instituto Federal do Amazonas (IFAM)
- EMBRAPA Amazônia Ocidental
- Instituto Nacional de Pesquisas da Amazônia (INPA)

---

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.10+
- Conda instalado
- Fedora Linux (recomendado)

### Instalação
```bash
# Clonar repositório
git clone https://github.com/seu-usuario/yara.git
cd yara

# Criar ambiente
conda create -n yara python=3.10 -y
conda activate yara

# Instalar dependências
make install

# Treinar modelo
make train
```

### Uso
```bash
# Terminal 1: Actions Server
make actions

# Terminal 2: Chat
make shell
```

---

## 💬 Funcionalidades

O YARA atualmente responde sobre:

- ✅ **Diversidade Alfa** (Shannon, Simpson, Observed Features)
- ✅ **Diversidade Beta** (PCoA, UniFrac, Bray-Curtis)
- ✅ **Taxonomia** (Classificação hierárquica)
- ✅ **Rarefação** (Curvas de amostragem e saturação)
- ✅ **Análises estatísticas** (Kruskal-Wallis e Mann-Whitney)

---

## 📁 Estrutura
```
yara/
├── domain.yml          # Intents, entities, responses
├── config.yml          # Pipeline NLU e políticas
├── data/
│   ├── nlu.yml        # Exemplos de treinamento
│   ├── stories.yml    # Fluxos de conversação
│   └── rules.yml      # Regras fixas
├── actions/
│   └── actions.py     # Lógica customizada
├── models/            # Modelos treinados
├── Makefile           # Comandos úteis
└── README.md          # Este arquivo
```

---

## 🛠️ Desenvolvimento

### Adicionar Nova Funcionalidade

1. **Adicionar exemplos** em `data/nlu.yml`
2. **Criar action** em `actions/actions.py`
3. **Registrar** em `domain.yml`
4. **Treinar**: `make train`
5. **Testar**: `make shell`

### Comandos Úteis
```bash
make help      # Ver todos comandos
make train     # Treinar modelo
make shell     # Chat teste
make actions   # Servidor actions
make test      # Rodar testes
make clean     # Limpar cache
```

---

## 📊 Cronograma

**Ago-Out/2025**: Desenvolvimento core
**Nov/2025-Jan/2026**: Integração QIIME 2
**Fev-Ago/2026**: Validação e refinamento

---

## 🤝 Contribuir

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit (`git commit -m 'Adiciona nova feature'`)
4. Push (`git push origin feature/nova-feature`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT.

---

## 👥 Equipe

**Coordenador**: Prof. Diego Lisboa Rios (IFAM)
**Email**: diego.rios@ifam.edu.br
**Projeto**: PVM2264-2025

---

## 🙏 Agradecimentos

- IFAM - Campus Manaus Centro
- EMBRAPA Amazônia Ocidental
- INPA
- Comunidade Rasa
- Comunidade QIIME 2

---

<p align="center">
  <strong>Desenvolvido com ❤️ para a ciência amazônica 🌳</strong>
</p>
