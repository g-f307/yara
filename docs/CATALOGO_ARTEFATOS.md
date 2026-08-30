# Catálogo semântico de artefatos

## Responsabilidades

O catálogo possui duas camadas deliberadamente separadas:

- o manifesto `.artifacts.json` do Python Core autoriza quais arquivos físicos
  estão `VALID` e podem ser lidos;
- as tabelas Prisma `Artifact` e `ArtifactCompatibility` projetam a
  classificação para consultas autenticadas e para a interface.

O banco não autoriza a leitura de bytes. Um registro Prisma sem entrada válida
no manifesto não é processado pelo backend.

## Classificação

O classificador `1.0.0` inspeciona conteúdo de TSV/CSV, estrutura BIOM e
`metadata.yaml`/`VERSION` de QZA/QZV. Os papéis suportados são:

```text
FEATURE_TABLE, TAXONOMY, METADATA, PHYLOGENETIC_TREE,
ALPHA_VECTOR, DISTANCE_MATRIX, PCOA_ORDINATION,
RAREFACTION_CURVE e UNKNOWN
```

Extensão não determina o papel. Cada classificação registra confiança e versão.
Somente hashes dos conjuntos de identificadores são persistidos na metadata
derivada; IDs de amostras não são enviados ao frontend.

## Ambiguidade

Quando mais de um artefato possui o mesmo papel, a análise retorna
`AMBIGUOUS_ARTIFACT` (HTTP 409). O usuário deve selecionar um candidato no painel
Files. A escolha é armazenada em `.artifact-selections.json` e as análises passam
a usar somente o candidato selecionado.

## Contratos internos

```text
GET  /api/artifacts?project_id=<uuid>
POST /api/artifacts/classify
POST /api/artifacts/select
GET  /api/artifacts/compatibility?project_id=<uuid>
```

Todas as rotas pertencem a `/api/*`, exigem assinatura HMAC e são acessadas pelo
frontend somente após `requireOwnedProject()`.

## Migração e rollback

Aplicar em produção/staging:

```bash
cd frontend
npx prisma migrate deploy
npx prisma generate
```

Em um banco criado antes da adoção de migrations, fazer uma única vez o
baseline antes do deploy:

```bash
npx prisma migrate resolve --applied 20260801000000_baseline
npx prisma migrate deploy
```

Não executar `resolve --applied` em banco vazio; nesse caso, `migrate deploy`
deve criar o baseline normalmente.

A migration é aditiva e não altera `File`, `AnalysisSession` ou
`AnalysisSummary`. Antes do deploy, realizar backup do PostgreSQL. Para rollback
manual, interromper o uso do catálogo e executar, na ordem apresentada, o
arquivo:

```text
frontend/prisma/migrations/20260830080000_add_semantic_artifact_catalog/rollback.sql
```

O rollback remove somente `ArtifactCompatibility`, `Artifact` e seus enums. O
manifesto seguro e os arquivos físicos permanecem intactos. Depois, retornar o
código para a versão anterior e regenerar o Prisma Client.

## Limitações conhecidas

- A compatibilidade inicial compara conjuntos completos de IDs por hash; relações
  parciais serão tratadas na evolução de metadata.
- BIOM é classificado como feature table, mas a inspeção científica detalhada
  depende do parser BIOM da fase seguinte.
- QZA/QZV sem semantic type conhecido permanecem `UNKNOWN` e não são escolhidos
  automaticamente.
