from __future__ import annotations

import asyncio
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from security.internal_api_auth import (
    InternalApiAuthMiddleware,
    build_canonical_request,
    compute_signature,
    is_signature_valid,
    sha256_hex,
    validate_internal_api_configuration,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "internal_api_hmac.json"
)
VECTOR = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
BODY = VECTOR["body"].encode("utf-8")


class InternalApiAuthUnitTests(unittest.TestCase):
    def test_shared_body_hash(self):
        self.assertEqual(sha256_hex(BODY), VECTOR["body_sha256"])

    def test_shared_canonical_request(self):
        canonical = build_canonical_request(
            VECTOR["method"],
            VECTOR["path_with_query"],
            VECTOR["timestamp"],
            BODY,
        )
        self.assertEqual(
            canonical,
            "\n".join(
                [
                    VECTOR["method"],
                    VECTOR["path_with_query"],
                    str(VECTOR["timestamp"]),
                    VECTOR["body_sha256"],
                ]
            ),
        )

    def test_shared_signature(self):
        signature = compute_signature(
            VECTOR["secret"],
            VECTOR["method"],
            VECTOR["path_with_query"],
            VECTOR["timestamp"],
            BODY,
        )
        self.assertEqual(signature, VECTOR["signature"])

    def test_valid_signature(self):
        self.assertTrue(
            is_signature_valid(
                secret=VECTOR["secret"],
                method=VECTOR["method"],
                path_with_query=VECTOR["path_with_query"],
                timestamp_value=str(VECTOR["timestamp"]),
                provided_signature=VECTOR["signature"],
                body=BODY,
                now=VECTOR["timestamp"],
            )
        )

    def test_missing_or_invalid_signature(self):
        common = {
            "secret": VECTOR["secret"],
            "method": VECTOR["method"],
            "path_with_query": VECTOR["path_with_query"],
            "timestamp_value": str(VECTOR["timestamp"]),
            "body": BODY,
            "now": VECTOR["timestamp"],
        }
        self.assertFalse(
            is_signature_valid(
                **common,
                provided_signature=None,
            )
        )
        self.assertFalse(
            is_signature_valid(
                **common,
                provided_signature="0" * 64,
            )
        )

    def test_expired_and_future_timestamps(self):
        common = {
            "secret": VECTOR["secret"],
            "method": VECTOR["method"],
            "path_with_query": VECTOR["path_with_query"],
            "provided_signature": VECTOR["signature"],
            "body": BODY,
        }
        self.assertFalse(
            is_signature_valid(
                **common,
                timestamp_value=str(VECTOR["timestamp"]),
                now=VECTOR["timestamp"] + 61,
            )
        )
        self.assertFalse(
            is_signature_valid(
                **common,
                timestamp_value=str(VECTOR["timestamp"]),
                now=VECTOR["timestamp"] - 6,
            )
        )

    def test_tampered_request_data(self):
        base = {
            "secret": VECTOR["secret"],
            "timestamp_value": str(VECTOR["timestamp"]),
            "provided_signature": VECTOR["signature"],
            "now": VECTOR["timestamp"],
        }
        altered = [
            {
                "method": "GET",
                "path_with_query": VECTOR["path_with_query"],
                "body": BODY,
            },
            {
                "method": VECTOR["method"],
                "path_with_query": "/api/alpha/analyze?mode=other",
                "body": BODY,
            },
            {
                "method": VECTOR["method"],
                "path_with_query": VECTOR["path_with_query"],
                "body": BODY + b" ",
            },
        ]
        for change in altered:
            with self.subTest(change=change):
                self.assertFalse(is_signature_valid(**base, **change))

    def test_production_requires_secret_at_startup(self):
        with patch.dict(
            os.environ,
            {"ENVIRONMENT": "production"},
            clear=True,
        ):
            with self.assertRaises(RuntimeError):
                validate_internal_api_configuration()


class InternalApiAuthMiddlewareTests(unittest.TestCase):
    def setUp(self):
        async def downstream(scope, receive, send):
            request_message = await receive()
            response_body = json.dumps(
                {
                    "path": scope["path"],
                    "body": request_message.get("body", b"").decode("utf-8"),
                }
            ).encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": response_body,
                    "more_body": False,
                }
            )

        self.middleware = InternalApiAuthMiddleware(downstream)
        self.secret_patch = patch.dict(
            os.environ,
            {"YARA_INTERNAL_API_SECRET": VECTOR["secret"]},
        )
        self.secret_patch.start()

    def tearDown(self):
        self.secret_patch.stop()

    def invoke(
        self,
        path: str,
        *,
        method: str = "GET",
        body: bytes = b"",
        headers: dict[str, str] | None = None,
    ):
        request_sent = False
        response_messages = []

        async def receive():
            nonlocal request_sent
            if request_sent:
                return {"type": "http.disconnect"}
            request_sent = True
            return {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }

        async def send(message):
            response_messages.append(message)

        encoded_headers = [
            (name.lower().encode("ascii"), value.encode("ascii"))
            for name, value in (headers or {}).items()
        ]
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": encoded_headers,
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        }

        asyncio.run(self.middleware(scope, receive, send))
        status = next(
            message["status"]
            for message in response_messages
            if message["type"] == "http.response.start"
        )
        response_body = b"".join(
            message.get("body", b"")
            for message in response_messages
            if message["type"] == "http.response.body"
        )
        return status, json.loads(response_body)

    def test_health_is_public(self):
        status, response = self.invoke("/health")
        self.assertEqual(status, 200)
        self.assertEqual(response["path"], "/health")

    def test_api_rejects_unsigned_request(self):
        status, response = self.invoke(
            "/api/echo",
            method="POST",
            body=BODY,
        )
        self.assertEqual(status, 401)
        self.assertEqual(
            response,
            {"detail": "Requisição não autorizada."},
        )

    def test_api_accepts_valid_signed_request(self):
        timestamp = 1_700_000_000
        signature = compute_signature(
            VECTOR["secret"],
            "POST",
            "/api/echo",
            timestamp,
            BODY,
        )
        with patch("security.internal_api_auth.time.time", return_value=timestamp):
            status, response = self.invoke(
                "/api/echo",
                method="POST",
                body=BODY,
                headers={
                    "X-Yara-Timestamp": str(timestamp),
                    "X-Yara-Signature": signature,
                },
            )

        self.assertEqual(status, 200)
        self.assertEqual(response["body"], VECTOR["body"])


if __name__ == "__main__":
    unittest.main()
