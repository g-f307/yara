# Runbook de observabilidade do YARA

Este runbook orienta o diagnóstico local e operacional sem expor credenciais,
URLs assinadas, corpos de arquivos ou metadados científicos. O identificador de
correlação é transmitido no header `X-Request-ID` e aparece como `request_id` nos
logs JSON do Next.js (`yara-nextjs`) e FastAPI (`yara-python-core`).

## Triagem inicial

1. Copie o identificador de suporte mostrado ao usuário ou o `X-Request-ID` da
   resposta. Ele deve ser um UUID; nunca use tokens ou URLs como identificador.
2. Consulte os logs sem imprimir variáveis de ambiente:

   ```bash
   docker compose logs --since=30m frontend backend | rg '<request_id>'
   ```

3. Compare `status`, `duration_ms` e `error_code` nos dois serviços.
4. Restrinja a investigação ao intervalo e rota encontrados. Não copie corpos,
   headers de autenticação ou URLs assinadas para issues.

## Backend indisponível

Sinais: HTTP 503 e `BACKEND_UNAVAILABLE` no proxy.

```bash
docker compose ps backend
docker compose logs --tail=100 backend
curl -i http://localhost:8000/health
```

Confirme que o container está saudável, a porta 8000 está disponível e
`PYTHON_CORE_URL` aponta para `http://backend:8000` dentro do Compose. Reinicie
somente o serviço afetado após preservar os logs necessários.

## Banco indisponível

Sinais: operações de projeto falham no Next.js enquanto `/health` do FastAPI
continua respondendo.

```bash
docker compose ps db
docker compose logs --tail=100 db
docker compose exec db pg_isready -U yara -d yara_db
```

Confirme o healthcheck e a conectividade. Não exiba `DATABASE_URL` nos logs ou
na issue.

## Sincronização falhando

Sinais: `SYNC_FAILED`, artefatos com estado `FAILED` ou nenhum arquivo válido.

- Localize o `request_id` nos dois serviços.
- Confirme somente hostname permitido, extensão, tamanho e código público do
  artefato; não registre a URL assinada completa.
- Verifique espaço em disco e permissões de `backend/uploads`.
- Diferencie rejeição de segurança (`INVALID_FILE`, `FILE_TOO_LARGE` ou
  `UNSUPPORTED_FILE`) de indisponibilidade de armazenamento.

## Análise científica falhando

Sinais: HTTP 422 e `ANALYSIS_FAILED`.

- Correlacione a chamada pelo `request_id`.
- Confirme que existem artefatos `VALID` no manifesto.
- Execute o teste golden da análise afetada.
- Registre somente tipo da análise, código do erro e versão do serviço; não
  inclua tabelas, nomes de amostras ou metadata científica.

```bash
docker compose exec backend python -m pytest -m golden
```

## Armazenamento cheio

Sinais: sincronização ou relatório falha com erro de escrita.

```bash
df -h
docker system df
du -sh backend/uploads
```

Não apague uploads ou volumes automaticamente. Identifique o volume afetado e
obtenha autorização antes de qualquer limpeza.

## Segredo interno inválido

Sinais: HTTP 401 `AUTH_REQUIRED` em todas as rotas `/api/*`, enquanto `/health`
permanece disponível.

- Confirme que `YARA_INTERNAL_API_SECRET` existe nos dois serviços e deriva da
  mesma configuração, sem imprimir seu valor.
- Confirme que os relógios dos containers estão sincronizados.
- Recrie os containers após corrigir a configuração.
- Nunca registre a assinatura `X-Yara-Signature` completa.

## Validação manual do request ID

```bash
curl -i \
  -H 'X-Request-ID: 550e8400-e29b-41d4-a716-446655440000' \
  http://localhost:8000/health
```

A resposta e o log devem conter o mesmo UUID. Um header inválido ou maior que
36 caracteres deve ser substituído por um UUID novo.

## Contrato público de erro

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Requisição inválida.",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

Detalhes técnicos e stack traces nunca fazem parte da resposta. O frontend deve
mostrar a mensagem em PT-BR e o identificador de suporte.
