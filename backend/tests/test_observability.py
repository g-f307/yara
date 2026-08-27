from __future__ import annotations

import uuid

from observability import ERROR_MESSAGES, error_payload, metrics_snapshot, normalize_request_id


VALID_REQUEST_ID = "550e8400-e29b-41d4-a716-446655440000"


def test_valid_request_id_is_preserved(api_client) -> None:
    response = api_client.get("/health", headers={"X-Request-ID": VALID_REQUEST_ID})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == VALID_REQUEST_ID


def test_invalid_and_oversized_request_ids_are_replaced(api_client) -> None:
    for candidate in ("invalid", "x" * 200):
        response = api_client.get("/health", headers={"X-Request-ID": candidate})
        generated = response.headers["x-request-id"]
        assert str(uuid.UUID(generated)) == generated
        assert generated != candidate


def test_error_payload_has_only_public_fields() -> None:
    payload = error_payload(
        "INTERNAL_ERROR",
        ERROR_MESSAGES["INTERNAL_ERROR"],
        VALID_REQUEST_ID,
    )

    assert payload == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Ocorreu um erro interno.",
            "request_id": VALID_REQUEST_ID,
        }
    }


def test_request_metrics_do_not_contain_headers_or_bodies(api_client) -> None:
    secret_marker = "token-que-nao-pode-aparecer"
    api_client.get(
        "/health",
        headers={"Authorization": f"Bearer {secret_marker}"},
    )

    snapshot = metrics_snapshot()
    serialized = repr(snapshot)
    assert secret_marker not in serialized
    assert "GET /health" in snapshot["requests"]


def test_normalizer_never_accepts_arbitrary_content() -> None:
    generated = normalize_request_id("../../segredo\nconteudo")
    assert str(uuid.UUID(generated)) == generated
