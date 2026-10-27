"""Tests de los límites de uso de Gemini (error 429) y de la recogida reanudable."""

import json

from geo_study.collect import collect, load_answers
from geo_study.config import load_study
from geo_study.gemini import QuotaError, explain_429

STUDY = load_study("config/study.yaml")


def test_per_minute_limit_waits_what_google_says():
    body = {"error": {"message": "Quota exceeded for metric ... limit: 10", "details": [
        {"@type": "type.googleapis.com/google.rpc.QuotaFailure",
         "violations": [{"quotaId": "GenerateRequestsPerMinutePerProjectPerModel-FreeTier"}]},
        {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "39s"},
    ]}}
    info = explain_429(body)
    assert not info["fatal"] and info["retry_after"] == 40


def test_daily_quota_stops_with_clear_message():
    body = {"error": {"message": "Quota exceeded ... limit: 250", "details": [
        {"violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]}]}}
    info = explain_429(body)
    assert info["fatal"] and "mañana" in info["message"]


def test_model_without_free_tier_suggests_another_model():
    info = explain_429({"error": {"message": "Quota exceeded for metric ..., limit: 0, model: x"}})
    assert info["fatal"] and "config/study.yaml" in info["message"]


class FakeClient:
    """Responde bien las primeras N llamadas y después simula la cuota diaria agotada."""

    def __init__(self, ok_calls):
        self.ok_calls, self.calls = ok_calls, 0

    def ask(self, question):
        self.calls += 1
        if self.calls > self.ok_calls:
            raise QuotaError("cuota diaria agotada")
        return {"text": "Mira en Amazon", "sources": [], "search_queries": [], "error": None}


def test_collect_resumes_where_it_stopped(tmp_path):
    out = tmp_path / "answers.jsonl"
    pending = collect(STUDY, FakeClient(ok_calls=10), out)
    assert pending == 26 and len(load_answers(out)) == 10      # lo recogido queda guardado

    second = FakeClient(ok_calls=100)
    assert collect(STUDY, second, out) == 0
    assert second.calls == 26                                  # no repite lo que ya tenía
    assert len(load_answers(out)) == 36


def test_failed_answers_are_retried(tmp_path):
    out = tmp_path / "answers.jsonl"
    collect(STUDY, FakeClient(ok_calls=100), out)
    rows = load_answers(out)
    rows[0]["error"] = "HTTP 503"
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    again = FakeClient(ok_calls=100)
    collect(STUDY, again, out)
    assert again.calls == 1
