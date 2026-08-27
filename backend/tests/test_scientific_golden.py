from __future__ import annotations

import json
from collections import Counter

import pandas as pd
import pytest

from analysis.alpha_diversity import AlphaDiversityAnalyzer
from analysis.beta_diversity import BetaDiversityAnalyzer
from analysis.rarefaction import RarefactionAnalyzer
from analysis.statistics import calculate_kruskal_wallis
from routers.qc import QCRequest, qc_summary
from routers.taxonomy import _extract_taxa_at_level
from utils.project_manager import ProjectManager


ABS_TOLERANCE = 1e-8
REL_TOLERANCE = 1e-6


@pytest.fixture(scope="module")
def expected(golden_dir):
    return json.loads((golden_dir / "expected.json").read_text(encoding="utf-8"))


@pytest.mark.golden
def test_alpha_summary_matches_known_values(golden_dir, expected) -> None:
    frame = pd.read_csv(golden_dir / "alpha.tsv", sep="\t", index_col=0)
    actual = AlphaDiversityAnalyzer(frame).get_summary_stats("shannon")

    for field, value in expected["alpha"].items():
        assert actual[field] == pytest.approx(
            value,
            abs=ABS_TOLERANCE,
            rel=REL_TOLERANCE,
        )


@pytest.mark.golden
def test_beta_distance_summary_matches_known_values(golden_dir, expected) -> None:
    frame = pd.read_csv(golden_dir / "beta.tsv", sep="\t", index_col=0)
    actual = BetaDiversityAnalyzer(frame).get_distance_stats()

    for field, value in expected["beta"].items():
        assert actual[field] == pytest.approx(
            value,
            abs=ABS_TOLERANCE,
            rel=REL_TOLERANCE,
        )


@pytest.mark.golden
def test_taxonomy_counts_match_known_values(golden_dir, expected) -> None:
    frame = pd.read_csv(golden_dir / "taxonomy.tsv", sep="\t")
    actual = Counter(
        _extract_taxa_at_level(taxon, "Phylum")
        for taxon in frame["Taxon"]
    )

    assert dict(actual) == expected["taxonomy"]


@pytest.mark.golden
def test_rarefaction_recommendation_matches_known_values(golden_dir, expected) -> None:
    frame = pd.read_csv(golden_dir / "rarefaction.tsv", sep="\t", index_col=0)
    analyzer = RarefactionAnalyzer(frame)

    assert analyzer.get_plateau_depth("sample-a") == expected["rarefaction"]["sample_a_plateau"]
    assert analyzer.calculate_saturation("sample-a") == pytest.approx(
        expected["rarefaction"]["sample_a_saturation"],
        abs=ABS_TOLERANCE,
        rel=REL_TOLERANCE,
    )
    assert analyzer.recommend_sampling_depth()["recommended_depth"] == expected["rarefaction"]["recommended_depth"]


@pytest.mark.golden
@pytest.mark.asyncio
async def test_qc_summary_matches_known_values(monkeypatch, golden_dir, expected) -> None:
    monkeypatch.setattr(
        ProjectManager,
        "_valid_files",
        staticmethod(lambda _project_id, _extensions: [golden_dir / "qc.tsv"]),
    )

    response = await qc_summary(QCRequest(project_id="11111111-1111-4111-8111-111111111111"))

    for field, value in expected["qc"].items():
        assert response["data"][field] == pytest.approx(
            value,
            abs=ABS_TOLERANCE,
            rel=REL_TOLERANCE,
        )
    assert response["plotly_spec"]["data"][0]["type"] == "bar"


@pytest.mark.golden
def test_kruskal_wallis_matches_known_values(golden_dir, expected) -> None:
    frame = pd.read_csv(golden_dir / "statistics.tsv", sep="\t")
    actual = calculate_kruskal_wallis(frame, "group", "shannon")

    assert actual["success"] is True
    assert actual["significant"] is expected["statistics"]["significant"]
    assert actual["statistic"] == pytest.approx(
        expected["statistics"]["statistic"],
        abs=ABS_TOLERANCE,
        rel=REL_TOLERANCE,
    )
    assert actual["p_value"] == pytest.approx(
        expected["statistics"]["p_value"],
        abs=ABS_TOLERANCE,
        rel=REL_TOLERANCE,
    )
