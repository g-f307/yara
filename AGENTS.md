# YARA — Agente de Contexto do Projeto

> Este arquivo é o documento de referência primário para qualquer agente de IA trabalhando neste repositório.
> Leia-o integralmente antes de executar qualquer tarefa.

---

## O que é o YARA

YARA (Your Assistant for Results Analysis) é um chatbot científico especializado em análise metagenômica de sequências 16S rRNA. O produto final é uma aplicação web multi-usuário onde bioinformatas fazem upload de arquivos QIIME 2 (`.qzv`, `.qza`, `.tsv`, `.biom`) e interagem com uma IA em português brasileiro para obter análises estatísticas, visualizações interativas e relatórios exportáveis.

**Usuário-alvo:** Pesquisadores de bioinformática (IFAM, EMBRAPA, INPA e similares) sem necessidade de programar.

---

## Stack Tecnológico Definitivo

```
frontend/          → Next.js 14 + TypeScript + Tailwind + shadcn/ui
                     Vercel AI SDK (streaming) + Plotly.js
                     Auth: Clerk | Upload: Uploadthing

backend/       → FastAPI (Python 3.11+)
                     Análise científica: qiime2, scikit-bio, scipy, pandas
                     Relatórios: ReportLab (PDF), python-docx (DOCX)

Database:          PostgreSQL + Prisma ORM (Neon serverless)
LLM:               Claude API (claude-sonnet-4-6) via Vercel AI SDK
Deploy:            Vercel (frontend) + Railway (backend)
Orquestração:      Docker Compose (desenvolvimento local)
```

---

## Estrutura de Pastas

```
yara/
├── AGENTS.md                  ← este arquivo
├── docker-compose.yml
│
├── frontend/                  ← Next.js App (gerado via v0.dev, já existe)
│   ├── app/
│   │   ├── (auth)/            ← sign-in, sign-up (Clerk)
│   │   ├── dashboard/         ← lista de projetos do usuário
│   │   ├── project/[id]/      ← interface principal (chat + resultados)
│   │   └── api/               ← API Routes Next.js (orquestração/proxy)
│   ├── components/
│   │   ├── chat/              ← ChatWindow, MessageBubble, InputArea
│   │   ├── plots/             ← AlphaPlot, PCoAPlot, TaxonomyPlot, RarefactionPlot
│   │   └── ui/                ← shadcn/ui components
│   └── lib/                   ← utils, tipos TypeScript, prisma client
│
├── backend/               ← FastAPI (serviço científico)
│   ├── main.py                ← app FastAPI + inclusão de routers
│   ├── routers/
│   │   ├── alpha.py           ← POST /api/alpha/analyze
│   │   ├── beta.py            ← POST /api/beta/pcoa, /api/beta/distances
│   │   ├── taxonomy.py        ← POST /api/taxonomy/summary, /barplot
│   │   ├── rarefaction.py     ← POST /api/rarefaction/analyze
│   │   ├── statistics.py      ← POST /api/statistics/compare
│   │   └── reports.py         ← POST /api/reports/pdf, /docx
│   ├── analysis/              ← módulos científicos (preservar lógica existente)
│   │   ├── qiime_parser.py    ← parser QIIME2 (migrado de actions/utils/)
│   │   ├── alpha_diversity.py
│   │   ├── beta_diversity.py
│   │   ├── rarefaction.py
│   │   ├── statistics.py
│   │   └── report_generator.py
│   └── requirements.txt
│
└── actions/utils/             ← código legado Rasa (NÃO APAGAR, servem de referência)
    ├── qiime_parser_module.py
    ├── alpha_diversity_analyzer.py
    ├── beta_diversity_analyzer.py
    ├── rarefaction_analyzer.py
    ├── statistics.py
    └── report_generator.py
```

---

## Módulos Científicos Existentes (preservar 100%)

Os arquivos em `actions/utils/` contêm lógica validada que deve ser migrada (não reescrita) para `backend/analysis/`:

| Arquivo original | Destino | O que contém |
|---|---|---|
| `qiime_parser_module.py` | `analysis/qiime_parser.py` | Parser TSV/QZV/QZA/BIOM |
| `alpha_diversity_analyzer.py` | `analysis/alpha_diversity.py` | Shannon, Simpson, Chao1, Kruskal-Wallis |
| `beta_diversity_analyzer.py` | `analysis/beta_diversity.py` | PCoA, Bray-Curtis, distâncias |
| `rarefaction_analyzer.py` | `analysis/rarefaction.py` | Curvas de rarefação, recomendação de profundidade |
| `statistics.py` | `analysis/statistics.py` | Testes não-paramétricos |
| `report_generator.py` | `analysis/report_generator.py` | Base para PDF/DOCX |

**Regra:** nunca reescrever esses algoritmos do zero. Mover e adaptar a interface para FastAPI.

---

## Endpoints FastAPI a Implementar

Todos os endpoints retornam JSON com dois campos obrigatórios:
- `data`: resultado numérico/tabular da análise
- `plotly_spec`: especificação Plotly.js pronta para renderizar no frontend

```
POST /api/parse              → valida e parseia arquivo enviado
POST /api/alpha/analyze      → diversidade alfa (Shannon, Simpson, Chao1)
POST /api/beta/pcoa          → PCoA com Bray-Curtis ou Jaccard
POST /api/beta/distances     → matriz de distâncias
POST /api/taxonomy/summary   → composição taxonômica por nível
POST /api/taxonomy/barplot   → dados para stacked barplot
POST /api/rarefaction/analyze → curvas de rarefação + profundidade recomendada
POST /api/statistics/compare → Kruskal-Wallis ou Mann-Whitney entre grupos
POST /api/reports/pdf        → gera PDF e retorna URL de download
POST /api/reports/docx       → gera DOCX e retorna URL de download
```

---

## Plano de Trabalho — 5 Fases

### FASE 1 — Fundação e MVP (Semanas 1-3) → 40% do produto
**Objetivo:** login + upload + chat básico funcionando

- Infraestrutura: Docker Compose orquestrando frontend + backend
- Auth: Clerk (sign-in/sign-up integrado ao Next.js)
- DB: schema Postgres — entidades User, Project, File, AnalysisSession
- Upload: Uploadthing integrado, arquivos associados ao projeto no DB
- Chat: Vercel AI SDK + Claude API com streaming em PT-BR
- FastAPI: endpoint `/api/parse` funcional, chamado pelo LLM como tool

**Entregável:** usuário cria conta → cria projeto → faz upload → conversa com YARA → recebe resposta em PT-BR

---

### FASE 2 — Visualizações Essenciais (Semanas 4-7) → 65% do produto
**Objetivo:** todos os gráficos principais interativos no painel direito

- Alpha diversity: boxplot por grupo, tabela estatísticas, interpretação LLM
- Beta diversity: PCoA 2D/3D interativo, coloração por metadata, elipses
- Taxonomia: stacked barplot, seletor de nível taxonômico, heatmap
- Rarefação: curvas por amostra, linha de corte, badge de saturação
- LLM pode solicitar qualquer gráfico durante conversa

**Marco crítico:** na Semana 7, o produto deve estar sendo testado por pesquisador real.

---

### FASE 3 — Inteligência Analítica (Semanas 8-10) → 82% do produto
**Objetivo:** YARA como co-piloto especialista, não apenas executor

- Estatística conversacional: LLM detecta grupos → chama endpoint correto
- Fluxo guiado: após upload, YARA sugere análises, detecta problemas de qualidade
- Contexto persistente: histórico de análises salvo no Postgres por projeto
- LLM recebe histórico resumido como contexto em cada mensagem

---

### FASE 4 — Relatórios (Semanas 11-12) → 93% do produto
**Objetivo:** output profissional exportável para submissão científica

- PDF: template com identidade visual, figuras matplotlib server-side, tabelas
- DOCX: estrutura de artigo científico editável
- Export ZIP: PNG 300 DPI + XLSX + CSV processado

---

### FASE 5 — Polimento e Lançamento (Semanas 13-14) → 100%
**Objetivo:** produto utilizável sem instrução prévia

- Tema visual: roxo (#7C3AED) como acento sobre neutro, modo claro/escuro
- Onboarding: tutorial interativo no primeiro projeto
- Deploy: Vercel (frontend) + Railway (backend), SSL, domínio
- Documentação: manual PDF + Docker 1 comando para instalação local

---

## Estado Atual do Projeto

| Componente | Status |
|---|---|
| Frontend scaffold (3 painéis, chat mockado) | ✅ Gerado via v0.dev, está em `frontend/` |
| Módulos Python de análise | ✅ Migrados para `backend/analysis/` |
| FastAPI `backend/` | ✅ Criado com routers: parse, alpha, beta, taxonomy, rarefaction, statistics, reports |
| Legado Rasa | 🗑️ Removido (config, domain, endpoints, actions, scripts) |
| Integração Claude API | ⏳ A implementar |
| Auth Clerk | ⏳ A implementar |
| Banco de dados Prisma | ⏳ A implementar |
| Upload Uploadthing | ⏳ A implementar |
| Gráficos Plotly reais | ⏳ A implementar |
| Relatórios PDF/DOCX | ⏳ A implementar (scaffold existe) |

**Próxima tarefa imediata:** integrar frontend com backend (Docker Compose + chamadas de API).


---

## Regras para o Agente

1. **Nunca reescrever** os algoritmos científicos existentes em `actions/utils/` — apenas mover e adaptar a interface
2. **Todo endpoint FastAPI** deve retornar `data` + `plotly_spec` no JSON
3. **Toda resposta do chat** deve ser em português brasileiro
4. **Variáveis de ambiente sensíveis** (ANTHROPIC_API_KEY, DATABASE_URL) nunca no código — sempre via `.env`
5. **Segurança de upload:** validar extensão E inspecionar conteúdo antes de processar `.qzv` (risco de path traversal)
6. **Isolamento de projetos:** toda query Prisma filtrada por `userId` — nunca retornar dados de outro usuário
7. **Claude API key** nunca exposta no cliente — sempre via API Route Next.js

---

## Variáveis de Ambiente Necessárias

```env
# frontend/.env.local
ANTHROPIC_API_KEY=
DATABASE_URL=
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
UPLOADTHING_SECRET=
UPLOADTHING_APP_ID=
PYTHON_CORE_URL=http://localhost:8000

# backend/.env
DATABASE_URL=
STORAGE_PATH=./uploads
```
