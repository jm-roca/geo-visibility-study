"""Redacción del informe ejecutivo con Claude.

Claude recibe SOLO los indicadores ya calculados, las auditorías y las respuestas
del bloque de reputación, y devuelve una estructura fija: titular, hallazgos,
valoración de reputación y plan de acciones. Después, el código comprueba que
cada porcentaje que Claude menciona existe en los datos: si se inventa una cifra,
el informe lo avisa.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from geo_study.analyze import reported_percentages

DEFAULT_MODEL = "claude-sonnet-5-5"

REPORT_TOOL = {
    "name": "deliver_report",
    "description": "Entrega el resumen ejecutivo del estudio de visibilidad en IA.",
    "input_schema": {
        "type": "object",
        "properties": {
            "headline": {"type": "string", "description": "Hallazgo principal en una frase, con su cifra."},
            "findings": {"type": "array", "items": {"type": "string"}, "description": "3 a 5 hallazgos, cada uno con su dato."},
            "reputation": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question_id": {"type": "string"},
                        "tone": {"type": "string", "enum": ["positivo", "neutro", "mixto", "negativo"]},
                        "summary": {"type": "string", "description": "Qué dice Gemini, en una o dos frases."},
                    },
                    "required": ["question_id", "tone", "summary"],
                },
            },
            "actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string"},
                        "why": {"type": "string", "description": "Dato del estudio que la justifica."},
                        "impact": {"type": "string", "enum": ["alto", "medio", "bajo"]},
                        "effort": {"type": "string", "enum": ["alto", "medio", "bajo"]},
                    },
                    "required": ["action", "why", "impact", "effort"],
                },
            },
        },
        "required": ["headline", "findings", "reputation", "actions"],
    },
}

SYSTEM = """Eres analista de marketing especializado en visibilidad en buscadores de IA (GEO).
Redactas en español de España, para dirección de marketing: frases cortas, concretas, sin jerga.

Reglas:
- Usa SOLO las cifras que aparecen en los datos. No calcules porcentajes nuevos ni redondees distinto.
- Es una muestra pequeña: habla de indicios ("en esta muestra", "apunta a"), nunca de certezas.
- Describe hechos medidos, sin juicios de valor sobre las empresas.
- Las acciones deben ser concretas y estar justificadas por un dato del estudio o de la auditoría técnica.
- Si hay varios asistentes (ChatGPT, Gemini...), compara la marca principal entre ellos.
- En "reputation", una entrada por pregunta de marca (question_id), resumiendo todas sus respuestas.
- Propón 4 o 5 acciones, ordenadas de mayor a menor impacto."""


def build_payload(study, metrics: dict, audits: dict, reputation_answers: list[dict]) -> str:
    data = {
        "estudio": {"titulo": study.title, "marca_principal": study.brand(study.main_brand).name},
        "indicadores": {k: metrics.get(k) for k in ("brands", "engines", "top_sources", "reputation", "neutral_answers", "runs_per_question")},
        "auditoria_tecnica": audits,
        "respuestas_reputacion": [
            {"question_id": a["question_id"], "asistente": a.get("engine_name", "Gemini"), "pregunta": a["question"],
             "repeticion": a["run"], "respuesta": a["text"][:3000]}
            for a in reputation_answers
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=1)


def write_with_claude(study, metrics, audits, reputation_answers, model: str = DEFAULT_MODEL) -> dict:
    import anthropic

    client = anthropic.Anthropic(max_retries=3)
    response = client.messages.create(
        model=model,
        max_tokens=3000,
        system=SYSTEM,
        tools=[REPORT_TOOL],
        tool_choice={"type": "tool", "name": REPORT_TOOL["name"]},
        messages=[{"role": "user", "content": build_payload(study, metrics, audits, reputation_answers)}],
    )
    block = next(b for b in response.content if b.type == "tool_use")
    return {**block.input, "generated_by": model}


def fallback_narrative(study, metrics: dict) -> dict:
    """Resumen automático sin IA, para cuando no hay clave de Anthropic."""
    main = next(b for b in metrics["brands"] if b["is_main"])
    leader = metrics["brands"][0]
    findings = [
        f"{b['name']} aparece en el {b['share_of_voice']['rate']} % de las respuestas neutrales." for b in metrics["brands"]
    ]
    return {
        "headline": (
            f"{main['name']} aparece en el {main['share_of_voice']['rate']} % de las respuestas; "
            f"la tienda más mencionada es {leader['name']} ({leader['share_of_voice']['rate']} %)."
        ),
        "findings": findings,
        "reputation": [],
        "actions": [],
        "generated_by": "resumen automático (sin IA)",
    }


def check_numbers(narrative: dict, metrics: dict) -> list[int]:
    """Porcentajes del texto de Claude que no salen del análisis."""
    allowed = reported_percentages(metrics)
    text = " ".join([narrative.get("headline", ""), *narrative.get("findings", [])]
                    + [a.get("why", "") for a in narrative.get("actions", [])])
    found = {int(n) for n in re.findall(r"(\d{1,3})\s?%", text)}
    return sorted(found - allowed)


def to_gemini_schema(schema: dict) -> dict:
    """Convierte el esquema JSON de la herramienta de Claude al formato que pide Gemini
    (mismos campos, tipos en mayúsculas). Así ambos modelos devuelven la misma estructura."""
    out = {}
    for key, value in schema.items():
        if key == "type":
            out[key] = value.upper()
        elif key == "properties":
            out[key] = {k: to_gemini_schema(v) for k, v in value.items()}
        elif key == "items":
            out[key] = to_gemini_schema(value)
        else:
            out[key] = value
    return out


def write_with_gemini(study, metrics, audits, reputation_answers) -> dict:
    from geo_study.gemini import GeminiClient

    model = study.narrative_gemini_model
    client = GeminiClient(model)
    result = client.generate_json(
        SYSTEM,
        build_payload(study, metrics, audits, reputation_answers),
        to_gemini_schema(REPORT_TOOL["input_schema"]),
    )
    return {**result, "generated_by": model}


def choose_provider(study, use_ai: bool, narrative_file: Path | None = None) -> str:
    """auto: Claude por API si hay clave; si no, el texto pegado desde Claude.ai; si no, resumen simple."""
    if not use_ai or study.narrative_provider == "none":
        return "none"
    has_file = bool(narrative_file and Path(narrative_file).exists())
    if study.narrative_provider == "claude":
        return "claude" if os.environ.get("ANTHROPIC_API_KEY") else "none"
    if study.narrative_provider == "gemini":
        return "gemini" if os.environ.get("GEMINI_API_KEY") else "none"
    if study.narrative_provider == "file":
        return "file" if has_file else "none"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude"
    return "file" if has_file else "none"


# --- Redacción gratuita: el usuario pega un prompt en Claude.ai y guarda la respuesta ---

def manual_prompt(study, metrics, audits, reputation_answers) -> str:
    example = {
        "headline": "Hallazgo principal en una frase, con su cifra.",
        "findings": ["Hallazgo 1 con su dato", "Hallazgo 2 con su dato", "Hallazgo 3 con su dato"],
        "reputation": [{"question_id": "D1", "tone": "positivo | neutro | mixto | negativo", "summary": "Qué dicen los asistentes."}],
        "actions": [{"action": "Qué hacer", "why": "Dato del estudio que lo justifica", "impact": "alto | medio | bajo", "effort": "alto | medio | bajo"}],
    }
    return (
        SYSTEM
        + "\n\nCon los datos de abajo, devuelve ÚNICAMENTE un JSON válido con esta estructura "
        "(sin texto antes ni después):\n\n"
        + json.dumps(example, ensure_ascii=False, indent=2)
        + "\n\nDATOS DEL ESTUDIO:\n\n"
        + build_payload(study, metrics, audits, reputation_answers)
    )


def load_file_narrative(path: Path) -> dict:
    """Lee el JSON que devolvió Claude.ai. Acepta que venga dentro de un bloque ```json."""
    text = Path(path).read_text(encoding="utf-8").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"{path} no contiene un JSON")
    data = json.loads(match.group(0))
    missing = [k for k in ("headline", "findings", "actions") if k not in data]
    if missing:
        raise ValueError(f"Al JSON de {path} le faltan los campos: {', '.join(missing)}")
    data.setdefault("reputation", [])
    data.setdefault("generated_by", "Claude (Claude.ai, texto pegado)")
    return data


def make_narrative(study, metrics, audits, reputation_answers, use_ai: bool, narrative_file: Path | None = None) -> dict:
    provider = choose_provider(study, use_ai, narrative_file)
    try:
        if provider == "claude":
            narrative = write_with_claude(study, metrics, audits, reputation_answers)
        elif provider == "gemini":
            narrative = write_with_gemini(study, metrics, audits, reputation_answers)
        elif provider == "file":
            narrative = load_file_narrative(narrative_file)
        else:
            narrative = fallback_narrative(study, metrics)
    except Exception as exc:  # si la IA falla, el informe sale igual con el resumen simple
        print(f"AVISO: no se pudo redactar con {provider} ({exc}). Uso el resumen simple.")
        narrative = fallback_narrative(study, metrics)
    narrative["unverified_numbers"] = check_numbers(narrative, metrics)
    return narrative
