"""Recogida manual: respuestas copiadas desde las apps de ChatGPT, Gemini, etc.

Alternativa gratuita a la API. Además mide exactamente lo que ve un usuario en
la app. Funciona en dos pasos:

    python -m geo_study template   # crea data/manual/<asistente>.md con las preguntas
    (rellenas los huecos copiando y pegando las respuestas)
    python -m geo_study import     # convierte esos archivos en data/answers.jsonl

Después, el análisis y el informe son los mismos que con la API.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from geo_study.config import Study
from geo_study.gemini import normalize_domain

QUESTION_RE = re.compile(r"^=== ([A-Za-z0-9_-]+) ===\s*$", re.MULTILINE)
ANSWER_MARK = "--- Respuesta ---"
SOURCES_MARK = "--- Fuentes ---"
PLACEHOLDERS = ("(pega aquí", "(pega aqui", "(opcional")
URL_RE = re.compile(r"https?://[^\s)\]>\"']+")
BARE_DOMAIN_RE = re.compile(r"\b((?:[a-z0-9-]+\.)+(?:com|es|net|org|io|eu|info|tv|co))\b", re.IGNORECASE)

HOW_TO = {
    "chatgpt": "Usa un CHAT TEMPORAL (icono arriba a la derecha) para que la memoria no influya. "
               "Comprueba que la respuesta trae fuentes (búsqueda web).",
    "gemini": "Abre una CONVERSACIÓN NUEVA para cada pregunta.",
    "perplexity": "Abre un hilo nuevo para cada pregunta. Copia también las fuentes numeradas.",
}


def template_text(study: Study, assistant: dict) -> str:
    lines = [
        f"# {assistant['name']} · respuestas para el estudio",
        "",
        "Fecha: AAAA-MM-DD",
        "",
        "Instrucciones:",
        "1. Escribe arriba la fecha en que haces las preguntas (por ejemplo 2026-10-27).",
        f"2. {HOW_TO.get(assistant['id'], 'Abre una conversación nueva para cada pregunta.')}",
        "3. Copia cada pregunta TAL CUAL, sin añadir nada.",
        "4. Pega la respuesta completa debajo de '--- Respuesta ---' (borra el texto entre paréntesis).",
        "5. Si la respuesta muestra fuentes o enlaces, pégalos debajo de '--- Fuentes ---', uno por línea.",
        "6. No toques las líneas que empiezan por === ni por ---.",
        "",
    ]
    for q in study.questions:
        lines += [
            f"=== {q.id} ===",
            f"Pregunta: {q.text}",
            ANSWER_MARK,
            "(pega aquí la respuesta)",
            SOURCES_MARK,
            "(opcional: pega aquí los enlaces de las fuentes, uno por línea)",
            "",
        ]
    return "\n".join(lines)


def write_templates(study: Study, manual_dir: Path, force: bool = False) -> list[Path]:
    manual_dir.mkdir(parents=True, exist_ok=True)
    created = []
    for assistant in study.assistants:
        path = manual_dir / f"{assistant['id']}.md"
        if path.exists() and not force:
            print(f"Ya existe {path} (no se sobrescribe; usa --force para regenerarlo)")
            continue
        path.write_text(template_text(study, assistant), encoding="utf-8")
        created.append(path)
    return created


def _clean(block: str) -> str:
    kept = [ln for ln in block.strip().splitlines() if not ln.strip().lower().startswith(PLACEHOLDERS)]
    return "\n".join(kept).strip()


REDIRECT_HOSTS = ("google.com", "google.es")


def unwrap(url: str) -> str:
    """Enlaces de redirección (google.com/search?q=URL, google.com/url?q=URL) -> URL real."""
    parsed = urlparse(url)
    host = normalize_domain(parsed.hostname or "")
    if host in REDIRECT_HOSTS:
        target = (parse_qs(parsed.query).get("q") or parse_qs(parsed.query).get("url") or [""])[0]
        if target.startswith("http"):
            return target
        if BARE_DOMAIN_RE.fullmatch(target.removeprefix("www.")) or BARE_DOMAIN_RE.match(target):
            return "https://" + target
    return url


def extract_domains(text: str, bare: bool = True) -> list[str]:
    """Dominios de fuentes: de URLs completas y, si bare=True, de dominios sueltos ('fnac.es').

    En el texto de la respuesta solo cuentan los enlaces (bare=False): que la respuesta
    nombre «www.coolmod.com» es una mención, no una fuente consultada.
    """
    found = []
    for url in URL_RE.findall(text):
        found.append(normalize_domain(urlparse(unwrap(url)).hostname or ""))
    if bare:
        for dom in BARE_DOMAIN_RE.findall(URL_RE.sub(" ", text)):
            found.append(normalize_domain(dom))
    out = []
    for d in found:
        if d and d not in out:
            out.append(d)
    return out


def parse_manual_file(text: str) -> tuple[str | None, dict[str, dict]]:
    """Devuelve (fecha, {id_pregunta: {"text", "sources"}}) de un archivo rellenado."""
    m = re.search(r"^Fecha:\s*(\d{4}-\d{2}-\d{2})", text, re.MULTILINE)
    when = m.group(1) if m else None

    answers = {}
    parts = QUESTION_RE.split(text)
    # split devuelve [preámbulo, id1, bloque1, id2, bloque2, ...]
    for qid, block in zip(parts[1::2], parts[2::2]):
        if ANSWER_MARK not in block:
            continue
        after = block.split(ANSWER_MARK, 1)[1]
        answer, _, sources = after.partition(SOURCES_MARK)
        answer = _clean(answer)
        sources_text = _clean(sources)
        answers[qid] = {
            "text": answer,
            # fuentes pegadas aparte + enlaces que vengan dentro de la propia respuesta
            "sources": [{"domain": d, "title": d}
                        for d in dict.fromkeys(extract_domains(sources_text) + extract_domains(answer, bare=False))],
        }
    return when, answers


def import_manual(study: Study, manual_dir: Path, out_path: Path) -> dict:
    """Convierte las plantillas rellenas en answers.jsonl. Devuelve un resumen por asistente."""
    records, summary = [], {}
    for assistant in study.assistants:
        path = manual_dir / f"{assistant['id']}.md"
        if not path.exists():
            summary[assistant["name"]] = {"missing_file": True}
            continue
        when, answers = parse_manual_file(path.read_text(encoding="utf-8"))
        asked_at = f"{when or date.today().isoformat()}T12:00:00+00:00"
        filled, empty, excluded = 0, [], []
        skip = {x["question"] for x in study.exclusions if x["assistant"] == assistant["id"]}
        for q in study.questions:
            if q.id in skip:  # respuesta descartada a propósito (p. ej. copiada incompleta)
                excluded.append(q.id)
                continue
            a = answers.get(q.id, {"text": "", "sources": []})
            if not a["text"]:
                empty.append(q.id)
                continue
            filled += 1
            records.append({
                "question_id": q.id, "block": q.block, "question": q.text, "run": 1,
                "engine": assistant["id"], "engine_name": assistant["name"],
                "text": a["text"], "sources": a["sources"], "search_queries": [],
                "input_tokens": 0, "output_tokens": 0, "error": None,
                "model": f"{assistant['name']} (app)", "asked_at": asked_at,
            })
        summary[assistant["name"]] = {"filled": filled, "empty": empty, "excluded": excluded, "date": when}

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return summary
