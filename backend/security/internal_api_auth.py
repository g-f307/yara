"""Autenticação HMAC para chamadas internas do Next.js ao FastAPI."""

from __future__ import annotations

import hashlib
import hmac
import os
import time

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

TIMESTAMP_HEADER = b"x-yara-timestamp"
SIGNATURE_HEADER = b"x-yara-signature"
DEFAULT_MAX_AGE_SECONDS = 60
DEFAULT_FUTURE_TOLERANCE_SECONDS = 5


def sha256_hex(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def build_canonical_request(
    method: str,
    path_with_query: str,
    timestamp: int | str,
    body: bytes,
) -> str:
    return "\n".join(
        [
            method.upper(),
            path_with_query,
            str(timestamp),
            sha256_hex(body),
        ]
    )


def compute_signature(
    secret: str,
    method: str,
    path_with_query: str,
    timestamp: int | str,
    body: bytes,
) -> str:
    canonical = build_canonical_request(
        method,
        path_with_query,
        timestamp,
        body,
    )
    return hmac.new(
        secret.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def is_signature_valid(
    *,
    secret: str,
    method: str,
    path_with_query: str,
    timestamp_value: str | None,
    provided_signature: str | None,
    body: bytes,
    now: int | None = None,
    max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS,
    future_tolerance_seconds: int = DEFAULT_FUTURE_TOLERANCE_SECONDS,
) -> bool:
    if not timestamp_value or not provided_signature:
        return False
    if len(timestamp_value) > 12:
        return False
    if len(provided_signature) != 64:
        return False
    if any(character not in "0123456789abcdef" for character in provided_signature):
        return False

    try:
        timestamp = int(timestamp_value)
    except (TypeError, ValueError):
        return False

    current_time = int(time.time()) if now is None else now
    age = current_time - timestamp
    if age > max_age_seconds or age < -future_tolerance_seconds:
        return False

    expected_signature = compute_signature(
        secret,
        method,
        path_with_query,
        timestamp,
        body,
    )
    return hmac.compare_digest(expected_signature, provided_signature)


def validate_internal_api_configuration() -> None:
    environment = os.getenv("ENVIRONMENT", "development").lower()
    secret = os.getenv("YARA_INTERNAL_API_SECRET", "")
    if environment == "production" and len(secret) < 32:
        raise RuntimeError(
            "YARA_INTERNAL_API_SECRET deve ter ao menos 32 caracteres em produção."
        )


class InternalApiAuthMiddleware:
    """Protege todas as rotas /api sem interferir no health check."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http" or not scope["path"].startswith("/api/"):
            await self.app(scope, receive, send)
            return

        secret = os.getenv("YARA_INTERNAL_API_SECRET")
        if not secret:
            await self._send_error(
                scope,
                receive,
                send,
                status_code=503,
                message="Serviço interno não configurado.",
            )
            return

        body = await self._read_body(receive)
        headers = {name.lower(): value for name, value in scope["headers"]}
        timestamp = self._decode_header(headers.get(TIMESTAMP_HEADER))
        signature = self._decode_header(headers.get(SIGNATURE_HEADER))
        path_with_query = self._path_with_query(scope)

        if not is_signature_valid(
            secret=secret,
            method=scope["method"],
            path_with_query=path_with_query,
            timestamp_value=timestamp,
            provided_signature=signature,
            body=body,
        ):
            await self._send_error(
                scope,
                receive,
                send,
                status_code=401,
                message="Requisição não autorizada.",
            )
            return

        body_sent = False

        async def replay_body() -> Message:
            nonlocal body_sent
            if body_sent:
                return {"type": "http.disconnect"}
            body_sent = True
            return {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }

        await self.app(scope, replay_body, send)

    @staticmethod
    async def _read_body(receive: Receive) -> bytes:
        chunks: list[bytes] = []
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                break
            chunks.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        return b"".join(chunks)

    @staticmethod
    def _decode_header(value: bytes | None) -> str | None:
        if value is None:
            return None
        try:
            return value.decode("ascii")
        except UnicodeDecodeError:
            return None

    @staticmethod
    def _path_with_query(scope: Scope) -> str:
        raw_path = scope.get("raw_path", scope["path"].encode("utf-8"))
        path = raw_path.decode("latin-1")
        query = scope.get("query_string", b"").decode("latin-1")
        return f"{path}?{query}" if query else path

    @staticmethod
    async def _send_error(
        scope: Scope,
        receive: Receive,
        send: Send,
        *,
        status_code: int,
        message: str,
    ) -> None:
        response = JSONResponse(
            {"detail": message},
            status_code=status_code,
        )
        await response(scope, receive, send)
