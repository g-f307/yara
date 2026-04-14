# YARA

YARA, sigla de Your Assistant for Results Analysis, é uma aplicação web para apoio à análise de resultados metagenômicos de sequências 16S rRNA gerados a partir do QIIME 2. O projeto combina uma interface conversacional em português brasileiro com serviços de análise científica em Python, permitindo que pesquisadores façam upload de arquivos, organizem projetos e solicitem visualizações ou relatórios sem precisar programar.

O público-alvo são pesquisadores de bioinformática e áreas correlatas, especialmente em contextos institucionais como IFAM, EMBRAPA, INPA e laboratórios parceiros.

## Estado Atual

O repositório está em fase de integração do produto web. A antiga base Rasa foi removida, e a arquitetura atual está organizada em dois serviços principais:

- Frontend em Next.js, com dashboard, autenticação, upload de arquivos, páginas de projeto, chat e painel de resultados.
- Backend em FastAPI, com endpoints científicos para parse, diversidade alfa, diversidade beta, taxonomia, rarefação, estatística e relatórios.
- Persistência com Prisma e PostgreSQL, usando modelos para usuários, projetos, arquivos e sessões de análise.
- Upload com Uploadthing, protegido por autenticação Clerk.
- Chat via Vercel AI SDK, com ferramentas que chamam o backend científico e retornam especificações Plotly para renderização no frontend.
- Geração inicial de relatórios PDF e DOCX no backend.
- Validação pós-upload para detectar quais análises estão disponíveis no projeto.
- Modo demonstração com dados mock reais no backend.
- Histórico analítico estruturado para alimentar contexto e relatórios.
- Diagnóstico de qualidade de sequenciamento com QC de reads, detecção de outliers em diversidade alfa e recomendação de rarefação.

## Arquitetura

```text
yara/
├── frontend/                  Next.js, TypeScript, Tailwind, shadcn/ui
│   ├── app/                   Rotas da aplicação e API routes
│   ├── components/            Componentes de UI, chat, upload e resultados
│   ├── lib/                   Cliente Prisma, ações server-side e cliente do backend
│   ├── prisma/                Schema Prisma
│   └── package.json
│
├── backend/                   FastAPI e módulos científicos
│   ├── main.py                Aplicação FastAPI e registro dos routers
│   ├── routers/               Endpoints REST
│   ├── analysis/              Implementações de análise metagenômica
│   ├── utils/                 Utilitários de sincronização de projetos
│   ├── data/mock/             Dados de exemplo para desenvolvimento
│   └── requirements.txt
│
├── docker-compose.yml         Orquestração local do frontend, backend e PostgreSQL
├── AGENTS.md                  Contexto técnico e regras de evolução do projeto
└── README.md
```

## Stack

Frontend:

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS
- shadcn/ui e Radix UI
- Clerk
- Uploadthing
- Vercel AI SDK
- Plotly.js
- Zustand

Backend:

- Python 3.11
- FastAPI
- pandas, NumPy, SciPy e scikit-learn
- scikit-bio
- Plotly
- ReportLab
- python-docx

Banco de dados:

- PostgreSQL
- Prisma ORM

## Funcionalidades Implementadas

- Autenticação com Clerk nas páginas de dashboard e projeto.
- Criação, listagem, renomeação e exclusão de projetos.
- Upload de arquivos via Uploadthing.
- Registro de arquivos por projeto no banco via Prisma.
- Chat em português brasileiro com ferramentas de análise.
- Sincronização de arquivos enviados para o backend Python.
- Visualizações Plotly para diversidade alfa, diversidade beta, taxonomia e rarefação.
- Painel de QC com reads por amostra, detecção de baixa cobertura e fallback por rarefação quando não há arquivo específico de QC.
- Detecção automática de outliers em diversidade alfa, com destaque no gráfico e aviso no painel de resultados.
- Recomendação de profundidade de rarefação exibida junto ao gráfico.
- Visualização conversacional de estatística não-paramétrica.
- Endpoints REST para estatísticas, validação de dados, modo demo e relatórios.
- Persistência de sessões de análise no banco.
- Persistência de resumos analíticos por projeto.
- Exportação de relatórios com metadados do projeto.
- Modo claro/escuro no frontend.

## Endpoints do Backend

O backend FastAPI expõe os seguintes endpoints:

```text
GET  /health

POST /api/parse
POST /api/parse/validate
POST /api/project/sync
POST /api/project/use-demo
GET  /api/project/status/{project_id}

POST /api/qc/summary
POST /api/alpha/analyze
POST /api/beta/pcoa
POST /api/beta/distances
POST /api/taxonomy/summary
POST /api/taxonomy/barplot
POST /api/rarefaction/analyze
POST /api/statistics/compare

POST /api/reports/pdf
POST /api/reports/docx
GET  /api/reports/download/{filename}
```

Por convenção do projeto, os endpoints analíticos devem retornar JSON com `data` e `plotly_spec` quando aplicável.

## Variáveis de Ambiente

Crie os arquivos de ambiente localmente. Não versionar chaves, URLs privadas ou segredos.

`frontend/.env.local`:

```env
DATABASE_URL=
GOOGLE_GENERATIVE_AI_API_KEY=
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
CLERK_WEBHOOK_SECRET=
UPLOADTHING_SECRET=
UPLOADTHING_APP_ID=
PYTHON_CORE_URL=http://backend:8000
```

O chat usa `@ai-sdk/google` no estado atual do repositório.

`backend/.env`:

```env
DATABASE_URL=
STORAGE_PATH=./uploads
MAX_FILE_SIZE_BYTES=524288000
```

## Execução Local

### Opção 1: Docker Compose

```bash
docker compose up --build
```

Serviços esperados:

- Frontend: `http://localhost:3001`
- Backend: `http://localhost:8000`
- Documentação FastAPI: `http://localhost:8000/docs`

Observação: o `docker-compose.yml` atual sobe frontend e backend. O `DATABASE_URL` configurado para o frontend aponta para PostgreSQL, mas o serviço de banco ainda precisa estar disponível separadamente ou ser adicionado ao Compose.
O `docker-compose.yml` sobe frontend, backend e PostgreSQL. Após alterar o schema Prisma, sincronize o banco dentro do container:

```bash
docker compose exec frontend npx prisma generate
docker compose exec frontend npx prisma db push
```

### Opção 2: execução manual

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npx prisma generate
npm run dev
```

O frontend será iniciado em `http://localhost:3001`.

## Banco de Dados

O schema Prisma define os seguintes modelos:

- `User`: usuário associado ao `clerkId`.
- `Project`: projeto de análise pertencente a um usuário.
- `File`: arquivo enviado e associado a um projeto.
- `AnalysisSession`: histórico de mensagens e análises por projeto.
- `AnalysisSummary`: resumo estruturado de análises realizadas no projeto.

Após configurar `DATABASE_URL`, gere o cliente Prisma:

```bash
cd frontend
npx prisma generate
```

Use migrações ou sincronização de schema conforme o fluxo adotado no ambiente de desenvolvimento.

## Fluxo Principal

1. O usuário autentica com Clerk.
2. O usuário cria um projeto no dashboard.
3. O usuário faz upload de arquivos pelo Uploadthing.
4. O frontend registra os metadados dos arquivos no PostgreSQL via Prisma.
5. Após o upload, o frontend valida os dados disponíveis e tenta gerar o QC automaticamente quando houver dados compatíveis.
6. Ao solicitar uma análise no chat, o frontend sincroniza os arquivos do projeto com o backend.
7. O backend executa a análise científica e retorna dados estruturados e especificações Plotly.
8. O frontend renderiza o gráfico no painel de resultados, preserva estatísticas auxiliares e mantém o histórico da sessão.

## Dados de Teste

O projeto mantém dois conjuntos de mocks sincronizados:

- `backend/data/mock`: usado pelo modo demonstração do backend.
- `data/mock`: usado para upload manual pela interface.

Arquivos disponíveis:

- `alpha_mock.tsv`: diversidade alfa com uma amostra outlier (`Amostra10`) para testar alertas de alpha.
- `beta_mock.tsv`: matriz de distância para PCoA.
- `taxonomy_mock.tsv`: composição taxonômica para barplot.
- `rarefaction_mock.tsv`: curvas de rarefação com baixa cobertura em profundidades altas para testar recomendação.
- `qc_mock.tsv`: contagem de reads por amostra para testar o painel de QC.

Fluxo sugerido para teste manual:

```text
1. Criar um projeto novo.
2. Fazer upload dos arquivos em data/mock.
3. Pedir ao chat: "avalie o QC dos reads".
4. Pedir: "gere diversidade alfa".
5. Pedir: "gere rarefação".
```

Resultados esperados:

- QC deve destacar `Amostra10` como outlier de baixa cobertura.
- Alpha deve destacar `Amostra10` como outlier em Shannon.
- Rarefação deve mostrar a profundidade recomendada no card de resultados.

## Próximos Passos

- Consolidar testes automatizados para os endpoints científicos.
- Refinar os templates de relatório para submissão científica.
- Ampliar o contexto analítico persistente usado pelo assistente.
- Implementar geração de seção de Métodos e interpretação guiada pós-análise.

## Diretrizes de Evolução

- Não expor chaves de API no cliente.
- Manter filtros por usuário em queries Prisma que acessam projetos, arquivos e sessões.
- Preservar a lógica científica em `backend/analysis/`, alterando interfaces com cuidado.
- Manter respostas do assistente conversacional em português brasileiro.
- Retornar `data` e `plotly_spec` nos endpoints analíticos sempre que houver resultado visualizável.
- Validar extensão e conteúdo dos arquivos antes de processá-los no backend.

## Licença

Este projeto está sob a licença MIT.
