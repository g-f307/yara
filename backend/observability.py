"""Contrato de erros, correlação, métricas e logs seguros do serviço FastAPI."""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = b"x-request-id"
SERVICE_NAME = "yara-python-core"

ERROR_MESSAGES = {
    "AUTH_REQUIRED": "Autenticação necessária.",
    "INVALID_REQUEST": "Requisição inválida.",
    "RESOURCE_NOT_FOUND": "Recurso não encontrado.",
    "PROJECT_ACCESS_DENIED": "Recurso não encontrado.",
    "INVALID_FILE": "Arquivo inválido.",
    "ARTIFACT_NOT_FOUND": "Nenhum artefato compatível foi encontrado.",
    "AMBIGUOUS_ARTIFACT": "Selecione explicitamente o artefato desejado.",
    "METADATA_NOT_FOUND": "Nenhum arquivo de metadata válido foi encontrado.",
    "METADATA_VERSION_NOT_FOUND": "A versão de metadata não foi encontrada.",
    "METADATA_TEMPLATE_NOT_FOUND": "O template de metadata não foi encontrado.",
    "INVALID_METADATA": "A metadata não atende ao formato esperado.",
    "METADATA_NOT_READY": "A metadata possui bloqueios que impedem esta análise.",
    "METADATA_CONFIRMATION_REQUIRED": "Confirme o preview antes de criar uma versão.",
    "METADATA_VERSION_CONFLICT": "A metadata foi alterada; gere um novo preview.",
    "FILE_TOO_LARGE": "O arquivo excede o tamanho permitido.",
    "UNSUPPORTED_FILE": "Formato de arquivo não suportado.",
    "SYNC_FAILED": "Não foi possível sincronizar os arquivos.",
    "ANALYSIS_FAILED": "Não foi possível concluir a análise.",
    "BACKEND_UNAVAILABLE": "O serviço de análise está indisponível.",
    "REPORT_FAILED": "Não foi possível gerar o relatório.",
    "INTERNAL_ERROR": "Ocorreu um erro interno.",
}


class ApiError(Exception):
    """Erro conhecido que pode ser convertido em uma resposta pública segura."""

    def __init__(self, code: str, status_code: int, message: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.status_code = status_code
        self.public_message = message or ERROR_MESSAGES.get(code, ERROR_MESSAGES["INTERNAL_ERROR"])


def normalize_request_id(value: str | None) -> str:
    if not value or len(value) > 36:
        return str(uuid.uuid4())
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError):
        return str(uuid.uuid4())
    return str(parsed) if str(parsed) == value.lower() else str(uuid.uuid4())


def request_id_from_scope(scope: Scope) -> str:
    state = scope.setdefault("state", {})
    request_id = state.get("request_id")
    if request_id:
        return request_id
    headers = {name.lower(): value for name, value in scope.get("headers", [])}
    raw = headers.get(REQUEST_ID_HEADER)
    try:
        candidate = raw.decode("ascii") if raw else None
    except UnicodeDecodeError:
        candidate = None
    request_id = normalize_request_id(candidate)
    state["request_id"] = request_id
    return request_id


def error_payload(code: str, message: str, request_id: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "request_id": request_id}}


def error_response(scope: Scope, code: str, status_code: int, message: str | None = None) -> JSONResponse:
    request_id = request_id_from_scope(scope)
    scope.setdefault("state", {})["error_code"] = code
    return JSONResponse(
        error_payload(code, message or ERROR_MESSAGES.get(code, ERROR_MESSAGES["INTERNAL_ERROR"]), request_id),
        status_code=status_code,
        headers={"X-Request-ID": request_id},
    )


@dataclass
class Metrics:
    requests: Counter
    statuses: Counter
    failures: Counter
    duration_ms_total: Counter


_metrics = Metrics(Counter(), Counter(), Counter(), Counter())
_metrics_lock = Lock()
_logger = logging.getLogger("yara.observability")
if not _logger.handlers:
    _logger.addHandler(logging.StreamHandler())
_logger.setLevel(logging.INFO)
_logger.propagate = False


def metrics_snapshot() -> dict[str, dict[str, int | float]]:
    with _metrics_lock:
        return {
            "requests": dict(_metrics.requests),
            "statuses": dict(_metrics.statuses),
            "failures": dict(_metrics.failures),
            "duration_ms_total": dict(_metrics.duration_ms_total),
        }


def record_failure(code: str) -> None:
    """Registra falhas internas sem adicionar dimensões de alta cardinalidade."""
    with _metrics_lock:
        _metrics.failures[code] += 1


def _safe_route(scope: Scope) -> str:
    route = scope.get("route")
    path = getattr(route, "path", None) or scope.get("path", "/")
    return re.sub(
        r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}(?=/|$)",
        "/{id}",
        path,
    )


def _write_log(event: dict[str, Any]) -> None:
    # JSON também em desenvolvimento facilita a correlação no Docker Compose.
    _logger.info(json.dumps(event, ensure_ascii=False, separators=(",", ":")))


class ObservabilityMiddleware:
    """Gera/propaga correlation ID e registra uma linha segura por requisição."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = request_id_from_scope(scope)
        started = time.perf_counter()
        status_code = 500

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = list(message.get("headers", []))
                headers = [(name, value) for name, value in headers if name.lower() != REQUEST_ID_HEADER]
                headers.append((REQUEST_ID_HEADER, request_id.encode("ascii")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception as exc:  # última barreira: nunca expõe exceção ou stack trace
            scope.setdefault("state", {})["error_code"] = "INTERNAL_ERROR"
            _write_log({
                "timestamp": datetime.now(UTC).isoformat(),
                "level": "error",
                "service": SERVICE_NAME,
                "request_id": request_id,
                "event": "unhandled_exception",
                "exception_type": type(exc).__name__,
            })
            response = error_response(scope, "INTERNAL_ERROR", 500)
            status_code = 500
            await response(scope, receive, send_with_request_id)

        duration_ms = round((time.perf_counter() - started) * 1000, 3)
        route = _safe_route(scope)
        error_code = scope.get("state", {}).get("error_code")
        metric_key = f"{scope['method']} {route}"
        with _metrics_lock:
            _metrics.requests[metric_key] += 1
            _metrics.statuses[str(status_code)] += 1
            _metrics.duration_ms_total[metric_key] += duration_ms
            if error_code:
                _metrics.failures[error_code] += 1
        _write_log({
            "timestamp": datetime.now(UTC).isoformat(),
            "level": "error" if status_code >= 500 else "warning" if status_code >= 400 else "info",
            "service": SERVICE_NAME,
            "request_id": request_id,
            "method": scope["method"],
            "path": route,
            "status": status_code,
            "duration_ms": duration_ms,
            "error_code": error_code,
        })


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        return error_response(request.scope, exc.code, exc.status_code, exc.public_message)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, _: RequestValidationError):
        return error_response(request.scope, "INVALID_REQUEST", 422)

    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException):
        if exc.status_code == 401:
            code = "AUTH_REQUIRED"
        elif exc.status_code in {403, 404}:
            code = "RESOURCE_NOT_FOUND"
        elif exc.status_code == 413:
            code = "FILE_TOO_LARGE"
        elif exc.status_code in {400, 422}:
            code = "INVALID_REQUEST"
        else:
            code = "INTERNAL_ERROR"
        may_use_detail = exc.status_code in {400, 422} and isinstance(exc.detail, str) and exc.detail.endswith(".")
        message = exc.detail if may_use_detail else ERROR_MESSAGES[code]
        return error_response(request.scope, code, exc.status_code, message)
