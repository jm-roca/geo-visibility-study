"""Tests de la lectura de respuestas de Gemini (sin llamar a la API)."""

from types import SimpleNamespace

from geo_study.gemini import GeminiClient, normalize_domain, parse_response, source_domain

# Respuesta con la forma documentada de la API de Gemini con búsqueda en Google:
# las fuentes llegan como enlaces de redirección y el dominio real va en el título.
GROUNDED = {
    "candidates": [{
        "content": {"parts": [{"text": "Puedes mirar en PcComponentes o en Amazon."}]},
        "groundingMetadata": {
            "webSearchQueries": ["mejor tienda componentes pc españa"],
            "groundingChunks": [
                {"web": {"uri": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/AbC", "title": "pccomponentes.com"}},
                {"web": {"uri": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/XyZ", "title": "reddit.com"}},
                {"web": {"uri": "https://vertexaisearch.cloud.google.com/grounding-api-redirect/Dup", "title": "reddit.com"}},
                {"web": {"uri": "https://www.xataka.com/guia", "title": "Guía de compra"}},
            ],
        },
    }],
    "usageMetadata": {"promptTokenCount": 20, "candidatesTokenCount": 80},
}


def test_parse_grounded_response():
    r = parse_response(GROUNDED)
    assert r["text"].startswith("Puedes mirar")
    assert [s["domain"] for s in r["sources"]] == ["pccomponentes.com", "reddit.com", "xataka.com"]  # sin duplicados
    assert r["search_queries"] == ["mejor tienda componentes pc españa"]
    assert (r["input_tokens"], r["output_tokens"]) == (20, 80)
    assert r["error"] is None


def test_blocked_prompt_is_an_error_not_a_silent_zero():
    r = parse_response({"promptFeedback": {"blockReason": "SAFETY"}})
    assert r["error"] and "SAFETY" in r["error"]


def test_domains_are_normalized():
    assert normalize_domain("https://www.Fnac.es/informatica") == "fnac.es"
    assert source_domain("https://vertexaisearch.cloud.google.com/x", "Título sin dominio") == ""


def test_missing_key_gives_clear_message(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    try:
        GeminiClient("gemini-3.8-flash")
    except RuntimeError as exc:
        assert "aistudio" in str(exc)
    else:
        raise AssertionError("Debería pedir la clave")


def test_ask_enables_google_search(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    client = GeminiClient("gemini-3.8-flash")
    sent = {}

    def fake_post(url, headers, json, timeout):
        sent.update(url=url, body=json)
        return SimpleNamespace(status_code=200, raise_for_status=lambda: None, json=lambda: GROUNDED)

    client.session = SimpleNamespace(post=fake_post)
    result = client.ask("¿Dónde compro una gráfica?")
    assert sent["body"]["tools"] == [{"google_search": {}}]
    assert "gemini-3.8-flash:generateContent" in sent["url"]
    assert len(result["sources"]) == 3


def test_429_per_minute_waits_and_retries(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    waits = []
    monkeypatch.setattr("geo_study.gemini.time.sleep", lambda s: waits.append(s))
    client = GeminiClient("gemini-3.8-flash")
    limited = {"error": {"message": "limit: 10", "details": [{"retryDelay": "3s"}]}}
    responses = iter([
        SimpleNamespace(status_code=429, json=lambda: limited),
        SimpleNamespace(status_code=200, json=lambda: GROUNDED),
    ])
    client.session = SimpleNamespace(post=lambda *a, **k: next(responses))
    result = client.ask("pregunta")
    assert waits == [4] and result["error"] is None


def test_daily_quota_raises_instead_of_retrying(monkeypatch):
    import pytest
    from geo_study.gemini import QuotaError

    monkeypatch.setenv("GEMINI_API_KEY", "test")
    client = GeminiClient("gemini-3.8-flash")
    daily = {"error": {"message": "x", "details": [{"violations": [{"quotaId": "RequestsPerDay-FreeTier"}]}]}}
    client.session = SimpleNamespace(post=lambda *a, **k: SimpleNamespace(status_code=429, json=lambda: daily))
    with pytest.raises(QuotaError):
        client.ask("pregunta")


def test_unknown_model_explains_how_to_fix(monkeypatch):
    import pytest

    monkeypatch.setenv("GEMINI_API_KEY", "test")
    client = GeminiClient("gemini-1.5-flash")
    not_found = {"error": {"message": "models/gemini-1.5-flash is not found for API version v1beta"}}
    client.session = SimpleNamespace(post=lambda *a, **k: SimpleNamespace(status_code=404, json=lambda: not_found))
    with pytest.raises(RuntimeError, match="geo_study models"):
        client.ask("pregunta")


def test_list_models_keeps_only_text_models(monkeypatch):
    import requests

    from geo_study.gemini import list_models

    monkeypatch.setenv("GEMINI_API_KEY", "test")
    payload = {"models": [
        {"name": "models/gemini-2.5-flash", "displayName": "Gemini 2.5 Flash", "supportedGenerationMethods": ["generateContent"]},
        {"name": "models/text-embedding-004", "displayName": "Embedding", "supportedGenerationMethods": ["embedContent"]},
    ]}
    monkeypatch.setattr(requests, "get", lambda *a, **k: SimpleNamespace(raise_for_status=lambda: None, json=lambda: payload))
    assert [m["id"] for m in list_models()] == ["gemini-2.5-flash"]
