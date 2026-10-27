"""Tests de configuración, auditoría y flujo completo en modo demo."""

import json

import pytest

from geo_study.audit import summarize_audit
from geo_study.cli import main
from geo_study.config import load_study


def test_real_study_config_is_valid():
    s = load_study("config/study.yaml")
    assert s.main_brand == "coolmod"
    assert {b.name for b in s.brands} == {"Coolmod", "PcComponentes", "Amazon", "MediaMarkt", "Neobyte"}
    assert next(q.text for q in s.questions if q.id == "D1") == "¿Es fiable Coolmod?"


def test_bad_config_fails_before_spending_api_calls(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "study: {title: t, subtitle: s, disclaimer: d, main_brand: nadie}\n"
        "engine: {provider: gemini, model: m, runs_per_question: 1}\n"
        "brands: [{id: a, name: A, url: u, domains: [a.es], aliases: [A]}]\n"
        "blocks: {A: {name: x, share_of_voice: true}}\n"
        "questions: [{id: Q1, block: A, text: q}]\n"
    )
    with pytest.raises(ValueError):
        load_study(bad)


def test_audit_summary_matches_geo_optimizer_output():
    """Contrato con geo-optimizer: se genera un JSON con su propio formateador."""
    formatters = pytest.importorskip("geo_optimizer.cli.formatters")
    from geo_optimizer.models.results import AuditResult

    raw = json.loads(formatters.format_audit_json(AuditResult(url="https://ejemplo.es", score=70, band="good")))
    summary = summarize_audit(raw)
    assert summary["score"] == 70
    assert summary["error"] is None
    assert isinstance(summary["recommendations"], list)


def test_demo_report_end_to_end(tmp_path):
    assert main(["report", "--demo", "--output", str(tmp_path)]) == 0
    html = (tmp_path / "report.html").read_text(encoding="utf-8")
    assert "Bitforja" in html and "<svg" in html
    assert "ficticias" in html                  # el aviso de datos simulados es visible
    narrative = json.loads((tmp_path / "narrative.json").read_text(encoding="utf-8"))
    assert narrative["unverified_numbers"] == []  # el texto de la demo no inventa cifras
    for name in ("metrics.json", "share_of_voice.csv", "report.md"):
        assert (tmp_path / name).exists()
