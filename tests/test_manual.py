"""Tests de la recogida manual: plantilla -> respuestas pegadas -> answers.jsonl."""

from geo_study.cli import main
from geo_study.collect import load_answers
from geo_study.config import load_study
from geo_study.manual import extract_domains, import_manual, parse_manual_file, write_templates

STUDY = load_study("config/study.yaml")


def fill(path, answers: dict, date="2026-10-27"):
    """Simula lo que hace el usuario: pega respuestas debajo de cada pregunta."""
    text = path.read_text(encoding="utf-8").replace("Fecha: AAAA-MM-DD", f"Fecha: {date}")
    for qid, (answer, sources) in answers.items():
        block_start = text.index(f"=== {qid} ===")
        before, after = text[:block_start], text[block_start:]
        after = after.replace("(pega aquí la respuesta)", answer, 1)
        if sources:
            after = after.replace("(opcional: pega aquí los enlaces de las fuentes, uno por línea)", sources, 1)
        text = before + after
    path.write_text(text, encoding="utf-8")


def test_templates_have_every_question(tmp_path):
    paths = write_templates(STUDY, tmp_path)
    assert [p.name for p in paths] == ["chatgpt.md", "gemini.md"]
    text = paths[0].read_text(encoding="utf-8")
    assert all(f"=== {q.id} ===" in text for q in STUDY.questions)
    assert "CHAT TEMPORAL" in text


def test_templates_are_not_overwritten(tmp_path):
    write_templates(STUDY, tmp_path)
    (tmp_path / "chatgpt.md").write_text("mis respuestas", encoding="utf-8")
    write_templates(STUDY, tmp_path)
    assert (tmp_path / "chatgpt.md").read_text(encoding="utf-8") == "mis respuestas"


def test_pasted_answers_are_imported(tmp_path):
    manual = tmp_path / "manual"
    write_templates(STUDY, manual)
    fill(manual / "chatgpt.md", {
        "A1": ("Te recomiendo PcComponentes y Amazon.\nOtra línea de la respuesta.",
               "https://www.pccomponentes.com/guia\n[1] xataka.com"),
        "D1": ("PcComponentes es fiable según opiniones en Trustpilot (es.trustpilot.com).", ""),
    })
    fill(manual / "gemini.md", {"A1": ("Puedes mirar en MediaMarkt o Fnac.", "")})

    summary = import_manual(STUDY, manual, tmp_path / "answers.jsonl")
    assert summary["ChatGPT"]["filled"] == 2 and "A2" in summary["ChatGPT"]["empty"]
    assert summary["Gemini"]["filled"] == 1

    rows = {(r["engine"], r["question_id"]): r for r in load_answers(tmp_path / "answers.jsonl")}
    a1 = rows[("chatgpt", "A1")]
    assert a1["text"].startswith("Te recomiendo") and "Otra línea" in a1["text"]
    assert [s["domain"] for s in a1["sources"]] == ["pccomponentes.com", "xataka.com"]
    assert rows[("chatgpt", "D1")]["sources"] == []          # un dominio nombrado en el texto no es una fuente
    assert a1["asked_at"].startswith("2026-10-27")


def test_placeholders_never_count_as_answers():
    text = "Fecha: AAAA-MM-DD\n=== A1 ===\nPregunta: x\n--- Respuesta ---\n(pega aquí la respuesta)\n--- Fuentes ---\n"
    when, answers = parse_manual_file(text)
    assert when is None and answers["A1"]["text"] == ""


def test_domain_extraction():
    assert extract_domains("Ver https://www.amazon.es/dp/1 y también fnac.es, o www.mediamarkt.es.") == [
        "amazon.es", "fnac.es", "mediamarkt.es"]


def test_full_manual_flow_from_the_command_line(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    data = tmp_path / "data"
    assert main(["template", "--data", str(data)]) == 0
    assert main(["import", "--data", str(data)]) == 1                 # aún sin respuestas
    fill(data / "manual" / "chatgpt.md", {"A1": ("Mira en PcComponentes.", ""), "B1": ("En Amazon.", "")})
    fill(data / "manual" / "gemini.md", {"A1": ("Prueba en Fnac.", "")})
    assert main(["import", "--data", str(data)]) == 0
    out = tmp_path / "out"
    assert main(["report", "--data", str(data), "--output", str(out)]) == 0
    html = (out / "report.html").read_text(encoding="utf-8")
    assert "ChatGPT" in html and "Gemini" in html
    assert (out / "prompt_para_claude.md").exists()                   # para redactar gratis en Claude.ai


def test_google_redirect_links_point_to_the_real_site():
    text = "https://www.google.com/search?q=https%3A%2F%2Fwww.coolmod.com\nhttps://www.google.com/url?q=https://neobyte.es/x"
    assert extract_domains(text) == ["coolmod.com", "neobyte.es"]


def test_domains_named_in_the_answer_are_mentions_not_sources(tmp_path):
    """Un «(www.coolmod.com)» dentro del texto no es una fuente consultada; un enlace pegado, sí."""
    text = ("Fecha: 2026-10-27\n=== A1 ===\nPregunta: x\n--- Respuesta ---\n"
            "Mira en Coolmod (www.coolmod.com). Según https://www.xataka.com/guia es buena.\n"
            "--- Fuentes ---\nWeb: pccomponentes.com\n")
    _, answers = parse_manual_file(text)
    assert [s["domain"] for s in answers["A1"]["sources"]] == ["pccomponentes.com", "xataka.com"]


def test_brand_subdomains_count_as_the_brand_site():
    from geo_study.analyze import compute_metrics

    answers = [{"question_id": "C1", "block": "C", "question": "q", "run": 1, "text": "PcComponentes", "error": None,
                "sources": [{"domain": "help.pccomponentes.com"}, {"domain": "pccomponentes.com"}]}]
    m = compute_metrics(answers, STUDY)
    assert m["top_sources"][0]["domain"] == "pccomponentes.com" and m["top_sources"][0]["answers"] == 1


def test_excluded_answers_are_skipped_and_reported(tmp_path):
    import dataclasses

    study = dataclasses.replace(STUDY, exclusions=[{"assistant": "gemini", "question": "A1", "reason": "incompleta"}])
    manual = tmp_path / "manual"
    write_templates(study, manual)
    fill(manual / "gemini.md", {"A1": ("Texto cortado", ""), "A3": ("Mira en Coolmod.", "")})
    summary = import_manual(study, manual, tmp_path / "answers.jsonl")
    assert summary["Gemini"]["excluded"] == ["A1"] and summary["Gemini"]["filled"] == 1
    assert {r["question_id"] for r in load_answers(tmp_path / "answers.jsonl")} == {"A3"}
