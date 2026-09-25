# Metadata versionada e orientação MIxS/MIMARKS

## Escopo

O YARA valida e versiona metadata tabular associada aos artefatos `VALID` do
manifesto seguro. Os perfis desta primeira versão são orientações locais,
versionadas e inspiradas em MIxS/MIMARKS; eles não representam certificação de
conformidade integral com todos os pacotes e extensões publicados pelo GSC.
O catálogo oficial consultado é mantido pelo
[Genomic Standards Consortium](https://genomicsstandardsconsortium.github.io/mixs/);
por isso a versão local do template é registrada em cada revisão e pode evoluir
sem reinterpretar versões históricas.

Perfis disponíveis:

- solo;
- rizosfera;
- água;
- hospedeiro;
- intestino;
- perfil estrutural neutro, usado enquanto o pesquisador não escolhe o contexto.

Cada campo informa nome, descrição, tipo, unidade, obrigatoriedade e vocabulário
permitido. Colunas não reconhecidas nunca são removidas.

## Imutabilidade e autoridade

O arquivo original continua autorizado pelo manifesto da sincronização segura.
A primeira leitura cria uma cópia derivada imutável em
`.metadata/versions/<uuid>.tsv`. Edições criam novos arquivos e registros; nunca
alteram versões anteriores. Uma restauração também cria uma nova versão cujo
`source` referencia a revisão restaurada.

O índice `.metadata/index.json` determina a versão ativa no Python Core. As
tabelas Prisma são uma projeção autenticada para histórico, consultas e UI. Cada
versão mantém SHA-256, schema inferido, artefato de origem, versão pai, template,
autor e data.

## Validação

As regras `1.0.0` verificam:

- coluna de identificação, IDs ausentes e duplicados;
- compatibilidade dos IDs com a tabela de features;
- campos mínimos e recomendados do perfil selecionado;
- valores ausentes e grupos pequenos;
- categorias inconsistentes;
- números, datas ISO 8601, unidades e limites de latitude/longitude;
- colunas desconhecidas, preservadas com diagnóstico informativo.

Diagnósticos usam `BLOCKING`, `WARNING` ou `INFO`, sempre com código, mensagem,
sugestão, coluna e amostras afetadas quando aplicável. O score soma cinco itens
explicitamente ponderados: identificadores (30), compatibilidade (25), campos
mínimos (25), completude (10) e formatos (10). O score não substitui os
diagnósticos nem transforma os dados automaticamente.

As regras por método indicam prontidão separada para exploração descritiva,
comparação entre grupos e uso geoespacial. Bloqueios globais impedem que uma
análise consuma metadata inválida. Quando metadata é utilizada, o contrato da
análise inclui `metadata_version_id`, preparado para persistência no futuro
modelo `AnalysisRun`.

## Fluxo de edição

1. Escolher o perfil científico.
2. Editar células ou adicionar ao rascunho os campos ausentes do template.
3. Solicitar `Validar preview`; nada é persistido nessa etapa.
4. Revisar score e diagnósticos detalhados.
5. Confirmar explicitamente a nova versão.
6. Restaurar uma versão anterior somente após confirmação; o histórico permanece.

Limites iniciais: 5.000 linhas e 200 colunas por versão editável na interface.
Não há geocodificação, preenchimento automático ou edição colaborativa.

## Rotas internas

```text
GET  /api/metadata/versions?project_id=<uuid>
POST /api/metadata/validate
POST /api/metadata/versions
POST /api/metadata/versions/<id>/restore
GET  /api/metadata/readiness?project_id=<uuid>
```

Todas pertencem ao namespace interno protegido por HMAC. Server Actions validam
a sessão e a propriedade do projeto antes de chamar o Python Core ou consultar
Prisma. IDs de versão e artefato sempre são filtrados pelo projeto autenticado.

## Migração

Aplicação em ambiente existente ou novo:

```bash
cd frontend
npx prisma migrate deploy
npx prisma generate
```

A migration `20260831160000_add_metadata_versioning` adiciona somente
`MetadataVersion`, `MetadataValidation`, `MetadataTemplate`,
`MetadataTemplateField` e o enum `MetadataSeverity`.

Rollback manual, depois de interromper escritas e realizar backup:

```text
frontend/prisma/migrations/20260831160000_add_metadata_versioning/rollback.sql
```

O rollback remove a projeção no PostgreSQL, mas não apaga os arquivos originais
nem o manifesto seguro. A pasta derivada `.metadata` deve ser preservada até a
decisão explícita de retenção, pois contém o histórico físico das versões.
