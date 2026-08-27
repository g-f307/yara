from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("YARA_INTERNAL_API_SECRET", "ci-only-secret-with-at-least-32-chars")
os.environ.setdefault("ALLOWED_STORAGE_HOSTS", "utfs.io")

from main import app
from security.internal_api_auth import compute_signature


@pytest.fixture(scope="session")
def golden_dir() -> Path:
    return Path(__file__).parent / "data" / "golden"


@pytest.fixture()
def api_client() -> TestClient:
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def signed_request(api_client: TestClient) -> Callable[..., Any]:
    def request(
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ):
        body = (
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            if payload is not None
            else b""
        )
        timestamp = str(int(time.time()))
        signature = compute_signature(
            os.environ["YARA_INTERNAL_API_SECRET"],
            method,
            path,
            timestamp,
            body,
        )
        return api_client.request(
            method,
            path,
            content=body,
            headers={
                "content-type": "application/json",
                "x-yara-timestamp": timestamp,
                "x-yara-signature": signature,
            },
        )

    return request
