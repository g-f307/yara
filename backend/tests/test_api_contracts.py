from __future__ import annotations

import uuid

import pandas as pd

from utils.project_manager import ProjectManager


PROJECT_ID = str(uuid.UUID("11111111-1111-4111-8111-111111111111"))


def _assert_plot_contract(response) -> None:
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("data"), dict)
    assert isinstance(payload.get("plotly_spec"), dict)
    assert isinstance(payload["plotly_spec"].get("data"), list)
    assert isinstance(payload["plotly_spec"].get("layout"), dict)


def test_health_check_is_public(api_client) -> None:
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "yara-python-core"}


def test_internal_router_rejects_unsigned_request(api_client) -> None:
    response = api_client.post(
        "/api/alpha/analyze",
        json={"project_id": PROJECT_ID},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Requisição não autorizada."}


def test_router_rejects_invalid_schema(signed_request) -> None:
    response = signed_request("POST", "/api/alpha/analyze", {})

    assert response.status_code == 422


def test_project_router_rejects_invalid_identifier(signed_request) -> None:
    response = signed_request("GET", "/api/project/status/not-a-uuid")

    assert response.status_code == 400
    assert response.json() == {"detail": "Identificador de projeto inválido."}


def test_analytical_routers_preserve_success_contract(
    monkeypatch,
    golden_dir,
    signed_request,
) -> None:
    frames = {
        "alpha": pd.read_csv(golden_dir / "alpha.tsv", sep="\t", index_col=0),
        "beta": pd.read_csv(golden_dir / "beta.tsv", sep="\t", index_col=0),
        "taxonomy": pd.read_csv(golden_dir / "taxonomy.tsv", sep="\t"),
        "rarefaction": pd.read_csv(
            golden_dir / "rarefaction.tsv",
            sep="\t",
            index_col=0,
        ),
    }

    def project_data(_project_id: str, data_type: str):
        return frames[data_type].copy()

    monkeypatch.setattr(ProjectManager, "get_project_data", staticmethod(project_data))
    monkeypatch.setattr(
        ProjectManager,
        "get_project_metadata",
        staticmethod(lambda _project_id: None),
    )
    monkeypatch.setattr(
        ProjectManager,
        "_valid_files",
        staticmethod(lambda _project_id, _extensions: [golden_dir / "qc.tsv"]),
    )

    requests = [
        ("/api/alpha/analyze", {"project_id": PROJECT_ID, "metric": "shannon"}),
        ("/api/beta/pcoa", {"project_id": PROJECT_ID}),
        ("/api/beta/distances", {"project_id": PROJECT_ID}),
        ("/api/taxonomy/summary", {"project_id": PROJECT_ID, "level": "Phylum"}),
        ("/api/taxonomy/barplot", {"project_id": PROJECT_ID, "level": "Phylum"}),
        ("/api/rarefaction/analyze", {"project_id": PROJECT_ID}),
        ("/api/qc/summary", {"project_id": PROJECT_ID}),
        (
            "/api/statistics/compare",
            {
                "data": pd.read_csv(
                    golden_dir / "statistics.tsv",
                    sep="\t",
                ).to_dict(orient="records"),
                "group_col": "group",
                "metric_col": "shannon",
            },
        ),
    ]

    for path, payload in requests:
        _assert_plot_contract(signed_request("POST", path, payload))


def test_analytical_failure_keeps_null_plot_contract(monkeypatch, signed_request) -> None:
    def unavailable(_project_id: str, _data_type: str):
        raise FileNotFoundError("fixture indisponível")

    monkeypatch.setattr(ProjectManager, "get_project_data", staticmethod(unavailable))

    response = signed_request(
        "POST",
        "/api/alpha/analyze",
        {"project_id": PROJECT_ID},
    )

    assert response.status_code == 200
    assert response.json()["plotly_spec"] is None
    assert "error" in response.json()
