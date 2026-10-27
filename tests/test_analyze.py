"""Tests del análisis: detección de marcas, métricas e intervalo de confianza."""

from geo_study.analyze import compute_metrics, detect_brands, wilson
from geo_study.collect import load_answers
from geo_study.config import ROOT, load_study
from geo_study.narrative import check_numbers

STUDY = load_study("config/study.yaml")
DEMO = load_study(ROOT / "examples" / "demo" / "study.yaml")


def test_aliases_and_order_of_appearance():
    text = "Te recomiendo Amazon, aunque en PC Componentes y en pccomponentes.com hay ofertas; MediaMarkt también."
    assert detect_brands(text, STUDY.brands) == ["amazon", "pccomponentes", "mediamarkt"]


def test_no_false_positives_inside_other_words():
    assert detect_brands("La selva del Amazonas y el Coolmodding", STUDY.brands) == []


def test_glued_words_from_copied_answers_are_detected():
    """Al copiar de Gemini se pierden espacios: «alta.Neobyte», «PcCompareAmazon», «CoolmodNo»."""
    text = "de gama media y alta.Neobyte y Wipoid. PcCompareAmazon España. CoolmodNo obstante"
    assert detect_brands(text, STUDY.brands) == ["neobyte", "amazon", "coolmod"]


def test_mentions_inside_urls_count():
    assert detect_brands("Más en www.neobyte.es/ofertas", STUDY.brands) == ["neobyte"]


def test_case_insensitive():
    assert detect_brands("compra en NEOBYTE, en CoolMod o en mediamarkt", STUDY.brands) == ["neobyte", "coolmod", "mediamarkt"]


def test_wilson_interval():
    lo, hi = wilson(20, 30)
    assert 0.48 < lo < 0.50 and 0.80 < hi < 0.82
    assert wilson(0, 0) == (0.0, 0.0)


def test_demo_metrics():
    m = compute_metrics(load_answers(ROOT / "examples" / "demo" / "answers.jsonl"), DEMO)
    assert m["answers_valid"] == 24            # 12 preguntas x 2 asistentes
    assert m["neutral_answers"] == 20          # el bloque D no cuenta para la cuota de voz
    assert [e["name"] for e in m["engines"]] == ["ChatGPT", "Gemini"]
    bitforja = next(b for b in m["brands"] if b["id"] == "bitforja")
    assert bitforja["share_of_voice"]["rate"] == 60
    assert bitforja["share_of_voice_by_engine"] == {"chatgpt": 80, "gemini": 40}
    assert m["brands"][0]["share_of_voice"]["rate"] >= m["brands"][-1]["share_of_voice"]["rate"]  # ordenado


def test_api_answers_without_engine_are_labelled():
    answers = [{"question_id": "A1", "block": "A", "question": "q", "run": 1, "text": "Fnac", "sources": [], "error": None}]
    m = compute_metrics(answers, STUDY)
    assert m["engines"] == [{"id": "gemini-api", "name": "Gemini (API)", "answers": 1}]


def test_failed_answers_are_excluded():
    answers = [
        {"question_id": "A1", "block": "A", "question": "q", "run": 1, "text": "Amazon", "sources": [], "error": None},
        {"question_id": "A1", "block": "A", "question": "q", "run": 2, "text": "", "sources": [], "error": "HTTP 429"},
    ]
    m = compute_metrics(answers, STUDY)
    assert m["answers_failed"] == 1
    amazon = next(b for b in m["brands"] if b["id"] == "amazon")
    assert amazon["share_of_voice"]["rate"] == 100


def test_invented_numbers_are_detected():
    m = compute_metrics(load_answers(ROOT / "examples" / "demo" / "answers.jsonl"), DEMO)
    narrative = {"headline": "Bitforja aparece en el 60 % y crecerá un 99 %", "findings": [], "actions": []}
    assert check_numbers(narrative, m) == [99]
