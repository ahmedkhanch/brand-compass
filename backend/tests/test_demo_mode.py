"""
DEMO_MODE pipeline test.

Asserts that with DEMO_MODE on and ZERO API keys, the full diagnostic pipeline
returns a complete, error-free report with realistic scores. Fails (RED) if the
mock provider layer is removed/reverted, since the real providers raise without keys.

Run: cd backend && DEMO_MODE=true python -m pytest tests/test_demo_mode.py -q
"""

import os
import sys
from pathlib import Path

os.environ["DEMO_MODE"] = "true"
_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from engine.orchestrator import run_full_diagnostic

_SECTIONS = ["positioning", "swot", "competitive", "recommendations", "seo", "geo"]
_MIN_SCORE = 40


def _report():
    return run_full_diagnostic(
        brand_name="Maison Lumière",
        website_url="https://www.maisonlumiere.fr",
        industry="cosmetics",
        competitor="L'Oréal",
    )


def test_all_sections_present_and_error_free():
    rep = _report()
    for section in _SECTIONS:
        val = rep.get(section)
        assert isinstance(val, dict), f"{section} missing or not a dict: {val!r}"
        assert "error" not in val, f"{section} errored: {val.get('error')!r}"


def test_scores_are_realistic():
    rep = _report()
    assert rep["seo"]["score"] >= _MIN_SCORE, rep["seo"]
    assert rep["geo"]["score"] >= _MIN_SCORE, rep["geo"]
    assert rep["overall_score"] >= _MIN_SCORE
    # Labels must be one of the calibrated buckets, never "Error".
    assert rep["seo"]["label"] != "Error"
    assert rep["geo"]["label"] != "Error"


def test_frontend_contract_fields():
    """The exact fields reports/[id]/page.tsx renders must exist."""
    rep = _report()
    assert rep["positioning"]["archetype"]
    assert isinstance(rep["positioning"]["brand_voice"], list)
    assert {"strengths", "weaknesses", "opportunities", "threats"} <= set(rep["swot"])
    assert isinstance(rep["competitive"]["direct_competitors"], list)
    assert rep["competitive"]["direct_competitors"][0]["threat_level"] in ("high", "medium", "low")
    assert isinstance(rep["recommendations"]["quick_wins"], list)
    assert "breakdown" in rep["seo"] and "breakdown" in rep["geo"]


def test_meta_ads_present():
    rep = _report()
    assert rep.get("meta_ads") and rep["meta_ads"]["total_ads_found"] > 0
    ad = rep["meta_ads"]["ads"][0]
    assert ad["page_name"] and "detected_ctas" in ad


def test_determinism_same_brand_same_scores():
    """A live demo must be reproducible: same brand → same numbers."""
    a, b = _report(), _report()
    assert a["seo"]["score"] == b["seo"]["score"]
    assert a["geo"]["score"] == b["geo"]["score"]
