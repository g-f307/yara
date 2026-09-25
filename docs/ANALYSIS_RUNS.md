# Execuções científicas imutáveis (`AnalysisRun`)

## Finalidade

`AnalysisRun` é o registro auditável de uma execução científica. Ele substitui gradualmente o uso de `AnalysisSummary` para histórico e reprodutibilidade, sem remover os dados legados.

Cada execução registra projeto e usuário solicitante, método, parâmetros, seed, versões de software, artefatos de entrada com hash, versão de metadata, resultado ou erro público, identificador de requisição e horários.

## Estados

```text
REQUESTED → VALIDATING → QUEUED → RUNNING → SUCCEEDED
                                        └→ FAILED

REQUESTED | VALIDATING | QUEUED | RUNNING → CANCELLED
```

As transições são validadas centralmente e usam atualização condicional para impedir concorrência. `SUCCEEDED`, `FAILED` e `CANCELLED` são terminais.

Uma trigger PostgreSQL impede a alteração das entradas, parâmetros, resultado, falha e demais campos científicos depois da terminalização. O campo técnico `updatedAt` pode ser mantido pelo Prisma sem alterar o conteúdo selado.

## Reprodução

Reproduzir não reabre nem altera a execução original. O sistema cria outra run com:

- `parentRunId` apontando para a original;
- snapshot novo das entradas atualmente selecionadas;
- parâmetros clonados ou explicitamente substituídos;
- novo `requestId` e novos horários;
- o mesmo método científico.

A comparação fica disponível no histórico por meio dos parâmetros, manifesto de entrada, hashes e versão de metadata.

## Rotas autenticadas

```text
POST /api/runs
GET  /api/runs?project_id=<uuid>
GET  /api/runs/<id>?project_id=<uuid>
POST /api/runs/<id>/reproduce
```

Criação:

```json
{
  "project_id": "uuid",
  "method": "alpha",
  "parameters": { "metric": "shannon", "group_col": "group" }
}
```

Reprodução:

```json
{
  "project_id": "uuid",
  "parameters": { "metric": "simpson", "group_col": "group" }
}
```

O usuário precisa ser proprietário do projeto. Busca e reprodução aplicam simultaneamente `runId` e `projectId`, evitando acesso horizontal.

## Compatibilidade legada

`AnalysisSummary` e `AnalysisSession` permanecem no schema. Novas análises executadas pelas Server Actions são registradas em `AnalysisRun`; consumidores antigos continuam funcionando durante a migração gradual.

## Migration e rollback

```bash
cd frontend
npx prisma migrate deploy
npm run test:migration
```

O teste de integração confirma coexistência com `AnalysisSummary`, imutabilidade terminal, vínculo de reprodução e consulta escopada por projeto.

O rollback de desenvolvimento está em `frontend/prisma/migrations/20260924090000_add_analysis_runs/rollback.sql`. Ele remove todo o histórico de runs; em produção, faça backup e valide retenção/auditoria antes de executá-lo.

## Limites desta entrega

- A execução continua síncrona; filas e workers pertencem à Issue #17.
- A inspeção detalhada da proveniência QIIME 2 pertence à Issue #16.
- A geração de pacote reproduzível é uma entrega posterior.
