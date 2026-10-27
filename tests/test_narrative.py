"""Tests de la redacción del informe con Claude o Gemini, usando clientes falsos."""

import dataclasses
import sys
from types import SimpleNamespace

from geo_study import narrative
from geo_study.analyze import compute_metrics
from geo_study.collect import load_answers
from geo_study.config import ROOT, load_study

DEMO = load_study(ROOT / "examples" / "demo" / "study.yaml")
METRICS = compute_metrics(load_answers(ROOT / "examples" / "demo" / "answers.jsonl"), DEMO)
FAKE_REPORT = {
    "headline": "Bitforja aparece en el 60 % de las respuestas.",
    "findings": ["Mercadia lidera con el 85 %."], "reputation": [], "actions": [],
}


def test_claude_is_forced_to_the_report_structure(monkeypatch):
    sent = {}

    class FakeMessages:
        def create(self, **kwargs):
            sent.update(kwargs)
            return SimpleNamespace(content=[SimpleNamespace(type="tool_use", input=FAKE_REPORT)])

    monkeypatch.setitem(sys.modules, "anthropic", SimpleNamespace(
        Anthropic=lambda max_retries: SimpleNamespace(messages=FakeMessages())))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")

    result = narrative.make_narrative(DEMO, METRICS, {}, [], use_ai=True)
    assert sent["tool_choice"] == {"type": "tool", "name": "deliver_report"}
    assert "60" in sent["messages"][0]["content"]          # recibe los indicadores calculados
    assert result["unverified_numbers"] == []


def test_gemini_can_write_the_report_if_configured(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    study = dataclasses.replace(DEMO, narrative_provider="gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    sent = {}

    def fake_generate_json(self, system, prompt, schema, model=None):
        sent["schema"] = schema
        return dict(FAKE_REPORT)

    monkeypatch.setattr("geo_study.gemini.GeminiClient.generate_json", fake_generate_json)
    result = narrative.make_narrative(study, METRICS, {}, [], use_ai=True)
    assert result["generated_by"] == DEMO.narrative_gemini_model
    assert sent["schema"]["type"] == "OBJECT"                             # formato de Gemini
    assert sent["schema"]["properties"]["actions"]["items"]["type"] == "OBJECT"


def test_without_any_key_uses_simple_summary(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = narrative.make_narrative(DEMO, METRICS, {}, [], use_ai=True)
    assert "sin IA" in result["generated_by"]
    assert result["unverified_numbers"] == []


def test_if_the_ai_fails_the_report_still_comes_out(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test")

    def boom(*args, **kwargs):
        raise RuntimeError("cuota agotada")

    monkeypatch.setattr("geo_study.gemini.GeminiClient.generate_json", boom)
    study = dataclasses.replace(DEMO, narrative_provider="gemini")
    result = narrative.make_narrative(study, METRICS, {}, [], use_ai=True)
    assert "sin IA" in result["generated_by"]


def test_text_pasted_from_claude_ai_is_used_and_verified(monkeypatch, tmp_path):
    """Flujo gratuito: el JSON que devuelve Claude.ai se guarda en data/narrative.json."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    pasted = tmp_path / "narrative.json"
    pasted.write_text(
        "Aquí tienes el JSON:\n```json\n"
        '{"headline": "Bitforja aparece en el 60 % y en el 99 %.", "findings": [], "actions": []}'
        "\n```", encoding="utf-8")
    result = narrative.make_narrative(DEMO, METRICS, {}, [], use_ai=True, narrative_file=pasted)
    assert "Claude.ai" in result["generated_by"]
    assert result["unverified_numbers"] == [99]          # el 99 % no sale del análisis


def test_manual_prompt_contains_data_and_format():
    text = narrative.manual_prompt(DEMO, METRICS, {}, [])
    assert '"headline"' in text and "DATOS DEL ESTUDIO" in text and "Bitforja" in text
