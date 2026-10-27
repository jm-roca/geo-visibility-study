"""Análisis: de respuestas brutas a indicadores.

Todo aquí es determinista (mismas respuestas, mismas cifras) y no usa IA:
- Cuota de voz: % de respuestas a preguntas neutrales que mencionan cada tienda.
- Primera recomendación: % de respuestas en que cada tienda es la primera citada.
- Citación como fuente: % de respuestas que usan la web de la tienda como fuente.
- Fuentes más usadas por Gemini para responder.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from geo_study.config import Brand, Study


def brand_pattern(brand: Brand) -> re.Pattern:
    """Regex con todos los alias de una marca, sin distinguir mayúsculas."""
    names = sorted({*brand.aliases, *brand.domains}, key=len, reverse=True)
    return re.compile("|".join(re.escape(n) for n in names), re.IGNORECASE)


def _is_boundary(text: str, start: int, end: int) -> bool:
    """¿Es una palabra completa?

    Al copiar respuestas de las apps a veces se pierden espacios y saltos de línea
    («alta.Neobyte», «PcCompareAmazon», «CoolmodNo obstante»). Se acepta como límite:
    un carácter que no es letra ni número, o un cambio de minúscula a mayúscula.
    Así «Amazonas» o «Coolmodding» no cuentan, pero «PcCompareAmazon» sí.
    """
    before = text[start - 1] if start > 0 else " "
    after = text[end] if end < len(text) else " "
    ok_before = not before.isalnum() or (before.islower() and text[start].isupper())
    ok_after = not after.isalnum() or (after.isupper() and text[end - 1].islower())
    return ok_before and ok_after


def find_brand(text: str, brand: Brand) -> int | None:
    """Posición de la primera mención de la marca, o None."""
    for m in brand_pattern(brand).finditer(text or ""):
        if _is_boundary(text, m.start(), m.end()):
            return m.start()
    return None


def detect_brands(text: str, brands: list[Brand]) -> list[str]:
    """Ids de las marcas mencionadas, ordenadas por su primera aparición en el texto."""
    first_pos = {}
    for b in brands:
        pos = find_brand(text, b)
        if pos is not None:
            first_pos[b.id] = pos
    return sorted(first_pos, key=first_pos.get)


def domain_matches(domain: str, brand: Brand) -> bool:
    return any(domain == d or domain.endswith("." + d) for d in brand.domains)


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de confianza del 95 % para una proporción (método de Wilson).

    Con muestras pequeñas es más fiable que el intervalo normal, y nunca se sale de 0-100 %.
    """
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def pct(x: float) -> int:
    return round(x * 100)


def enrich(answers: list[dict], study: Study) -> list[dict]:
    """Añade a cada respuesta las marcas detectadas y las fuentes de cada marca."""
    out = []
    for a in answers:
        mentioned = detect_brands(a.get("text", ""), study.brands)
        cited = [b.id for b in study.brands if any(domain_matches(s["domain"], b) for s in a.get("sources", []))]
        engine = a.get("engine") or "gemini-api"
        engine_name = a.get("engine_name") or ("Gemini (API)" if engine == "gemini-api" else engine)
        out.append({**a, "engine": engine, "engine_name": engine_name,
                    "mentioned": mentioned, "first": mentioned[0] if mentioned else None, "cited": cited})
    return out


def _rate_block(rows: list[dict], brand_id: str, key: str) -> dict:
    n = len(rows)
    k = sum(1 for r in rows if (brand_id in r[key] if key != "first" else r["first"] == brand_id))
    lo, hi = wilson(k, n)
    return {"count": k, "n": n, "rate": pct(k / n) if n else 0, "ci": [pct(lo), pct(hi)]}


def compute_metrics(answers: list[dict], study: Study) -> dict:
    valid = [a for a in enrich(answers, study) if not a.get("error")]
    neutral = [a for a in valid if a["block"] in study.sov_blocks()]

    # Asistentes presentes en los datos (ChatGPT, Gemini...), en orden de aparición.
    engines = []
    for a in valid:
        if a["engine"] not in [e["id"] for e in engines]:
            engines.append({"id": a["engine"], "name": a["engine_name"]})
    for e in engines:
        e["answers"] = sum(1 for a in neutral if a["engine"] == e["id"])

    brands = []
    for b in study.brands:
        by_block = {
            blk: _rate_block([a for a in neutral if a["block"] == blk], b.id, "mentioned")["rate"]
            for blk in study.sov_blocks()
        }
        brands.append({
            "id": b.id,
            "name": b.name,
            "is_main": b.id == study.main_brand,
            "share_of_voice": _rate_block(neutral, b.id, "mentioned"),
            "first_mention": _rate_block(neutral, b.id, "first"),
            "cited_as_source": _rate_block(neutral, b.id, "cited"),
            "share_of_voice_by_block": by_block,
            "share_of_voice_by_engine": {
                e["id"]: _rate_block([a for a in neutral if a["engine"] == e["id"]], b.id, "mentioned")["rate"]
                for e in engines
            },
        })
    brands.sort(key=lambda x: x["share_of_voice"]["rate"], reverse=True)

    # Matriz pregunta x marca: en cuántas repeticiones aparece cada tienda.
    matrix = []
    for q in study.questions:
        rows = [a for a in valid if a["question_id"] == q.id]
        matrix.append({
            "id": q.id, "block": q.block, "text": q.text, "runs": len(rows),
            "mentions": {b.id: sum(1 for r in rows if b.id in r["mentioned"]) for b in study.brands},
        })

    # Fuentes: en cuántas respuestas neutrales aparece cada dominio.
    def canonical(domain: str) -> str:
        """help.pccomponentes.com y soporte.coolmod.com cuentan como la web de su marca."""
        owner = next((b for b in study.brands if domain_matches(domain, b)), None)
        return owner.domains[0] if owner else domain

    source_counter = Counter(d for a in neutral for d in {canonical(s["domain"]) for s in a.get("sources", [])})
    top_sources = []
    for domain, count in source_counter.most_common(10):
        owner = next((b.name for b in study.brands if domain_matches(domain, b)), None)
        top_sources.append({"domain": domain, "answers": count, "rate": pct(count / len(neutral)) if neutral else 0, "brand": owner})

    # Bloque de reputación: qué fuentes usa Gemini cuando se pregunta por la marca.
    main = study.brand(study.main_brand)
    reputation_rows = [a for a in valid if a["block"] not in study.sov_blocks()]
    reputation = {
        "answers": len(reputation_rows),
        "official_site_cited": sum(1 for a in reputation_rows if main.id in a["cited"]),
        "sources": Counter(d for a in reputation_rows for d in {canonical(s["domain"]) for s in a.get("sources", [])}).most_common(8),
    }

    models = sorted({a.get("model", "") for a in valid if a.get("model")})
    return {
        "answers_total": len(answers),
        "answers_valid": len(valid),
        "answers_failed": len(answers) - len(valid),
        "neutral_answers": len(neutral),
        "runs_per_question": study.runs,
        "questions": len(study.questions),
        "models": models,
        "dates": sorted({a["asked_at"][:10] for a in valid if a.get("asked_at")}),
        "main_brand": study.main_brand,
        "engines": engines,
        "exclusions": [
            {**x, "assistant_name": next((a["name"] for a in study.assistants if a["id"] == x["assistant"]), x["assistant"])}
            for x in study.exclusions
        ],
        "brands": brands,
        "matrix": matrix,
        "top_sources": top_sources,
        "reputation": reputation,
        "input_tokens": sum(a.get("input_tokens", 0) for a in answers),
        "output_tokens": sum(a.get("output_tokens", 0) for a in answers),
    }


def reported_percentages(metrics: dict) -> set[int]:
    """Todos los porcentajes que el análisis ha calculado. Sirve para comprobar que
    el texto que redacta Claude no se inventa ninguna cifra."""
    values = set()
    for b in metrics["brands"]:
        for key in ("share_of_voice", "first_mention", "cited_as_source"):
            values.add(b[key]["rate"])
            values.update(b[key]["ci"])
        values.update(b["share_of_voice_by_block"].values())
        values.update(b.get("share_of_voice_by_engine", {}).values())
    values.update(s["rate"] for s in metrics["top_sources"])
    return values
