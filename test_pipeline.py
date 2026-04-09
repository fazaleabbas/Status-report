"""End-to-end tests for the analysis pipeline and presentation generation."""
from __future__ import annotations
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from analyse_projects import check_ollama_available, enrich_projects
from generate_status_report import build_data_from_simple_projects, build_deck

SAMPLE_PROJECTS = [
    {"name": "Tokenization", "status": "80% VISA testing completed, remaining issues resolved."},
    {"name": "QI Tap", "status": "Removed from production pending security review, currently at risk."},
    {"name": "PCI PIN", "status": "Core system development completed, preparing for certification."},
]


def test_rule_based():
    data = build_data_from_simple_projects(SAMPLE_PROJECTS, "Test Report", "09 April 2026", use_llm=False)
    assert len(data["projects"]) == 3
    assert data["projects"][1]["rag"] == "red", "QI Tap should be red"
    assert data["projects"][2]["rag"] == "green", "PCI PIN should be green"
    print("PASS test_rule_based")


def test_ollama_check():
    available, msg = check_ollama_available()
    print(f"PASS test_ollama_check — available={available}: {msg}")


def test_fallback_enrich():
    enriched, summary = enrich_projects(SAMPLE_PROJECTS)
    assert len(enriched) == 3
    assert enriched[1]["rag"] == "red", "QI Tap should remain red after fallback"
    for p in enriched:
        assert len(p["notes"]) == 2, f"Expected 2 notes for {p['name']}"
        assert p["next_step"], f"Expected next_step for {p['name']}"
        assert p["progress"], f"Expected progress for {p['name']}"
    assert summary
    print("PASS test_fallback_enrich")


def test_deck_generation_with_llm_flag():
    out = Path("test-ai-fallback.pptx")
    data = build_data_from_simple_projects(
        SAMPLE_PROJECTS, "AI Fallback Test", "09 April 2026",
        use_llm=True,
    )
    build_deck(data, out)
    assert out.exists() and zipfile.is_zipfile(out)
    print("PASS test_deck_generation_with_llm_flag")
    out.unlink()


if __name__ == "__main__":
    test_rule_based()
    test_ollama_check()
    test_fallback_enrich()
    test_deck_generation_with_llm_flag()
    print("\nAll tests passed.")

