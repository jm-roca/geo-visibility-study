"""Genera los datos SIMULADOS de la demo (examples/demo).

Respuestas inventadas para tiendas ficticias, con un patrón deliberado para que el
informe tenga algo que contar: Bitforja (la marca principal) es fuerte en
componentes y débil en servicio; Mercadia domina las preguntas de servicio.
Se ejecuta una vez; el resultado se guarda en el repositorio.
"""

import json
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "examples" / "demo"
random.seed(7)

# Probabilidad de que cada tienda aparezca en una respuesta, por asistente y bloque.
# Patrón deliberado: a Bitforja le va bien en ChatGPT y peor en Gemini.
PROB = {
    "chatgpt": {
        "A": {"Bitforja": 0.95, "Mercadia": 0.7, "Voltio Store": 0.5, "Librotek": 0.2},
        "B": {"Bitforja": 0.8, "Mercadia": 0.8, "Voltio Store": 0.4, "Librotek": 0.2},
        "C": {"Bitforja": 0.3, "Mercadia": 0.9, "Voltio Store": 0.7, "Librotek": 0.3},
    },
    "gemini": {
        "A": {"Bitforja": 0.6, "Mercadia": 0.9, "Voltio Store": 0.6, "Librotek": 0.3},
        "B": {"Bitforja": 0.4, "Mercadia": 0.95, "Voltio Store": 0.5, "Librotek": 0.3},
        "C": {"Bitforja": 0.1, "Mercadia": 0.9, "Voltio Store": 0.8, "Librotek": 0.4},
    },
}
ENGINES = {"chatgpt": "ChatGPT", "gemini": "Gemini"}
DOMAIN = {"Bitforja": "bitforja.es", "Mercadia": "mercadia.es", "Voltio Store": "voltiostore.es", "Librotek": "librotek.es"}
THIRD_PARTY = ["reddit.com", "comparatech.es", "foropc.es", "youtube.com", "guiahardware.es"]
PHRASES = {
    "Bitforja": "Bitforja, especializada en componentes y con un configurador de PC muy completo",
    "Mercadia": "Mercadia, con un catálogo enorme y envíos rápidos",
    "Voltio Store": "Voltio Store, que suele tener promociones de financiación",
    "Librotek": "Librotek, con una sección de informática más reducida",
}

study_questions = [
    ("A1", "A"), ("A2", "A"), ("A3", "A"), ("A4", "A"),
    ("B1", "B"), ("B2", "B"), ("B3", "B"), ("B4", "B"),
    ("C1", "C"), ("C2", "C"), ("D1", "D"), ("D2", "D"),
]
texts = {q["id"]: q["text"] for q in __import__("yaml").safe_load((OUT / "study.yaml").read_text())["questions"]}

lines = []
for (engine, engine_name), (qid, block) in [(e, q) for e in ENGINES.items() for q in study_questions]:
    for run in (1,):
        if block == "D":
            text = (
                "Bitforja es una tienda con buena reputación entre aficionados al hardware. Las opiniones "
                "destacan el precio y el configurador, aunque algunos usuarios mencionan retrasos en "
                "devoluciones en temporada alta. Frente a Mercadia, suele tener mejor surtido de tarjetas gráficas."
                if qid == "D2" or engine == "chatgpt" else
                "En general Bitforja se considera fiable: tiene años de trayectoria y valoraciones positivas, "
                "aunque hay quejas puntuales sobre el servicio posventa."
            )
            sources = ["reddit.com", "foropc.es", "trustscore.es"] + (["bitforja.es"] if engine == "chatgpt" else [])
        else:
            stores = [s for s, p in PROB[engine][block].items() if random.random() < p]
            random.shuffle(stores)
            if not stores:
                stores = ["Mercadia"]
            text = "Estas son algunas opciones recomendables en España: " + "; ".join(PHRASES[s] for s in stores) + "."
            own = [DOMAIN[s] for s in stores if random.random() < 0.35]
            sources = random.sample(THIRD_PARTY, 2) + own
        lines.append({
            "question_id": qid, "block": block, "question": texts[qid], "run": run,
            "engine": engine, "engine_name": engine_name,
            "text": text, "sources": [{"domain": d, "title": d} for d in sources],
            "search_queries": [], "input_tokens": 0, "output_tokens": 0,
            "error": None, "model": f"{engine_name} (app, simulado)", "asked_at": "2026-10-27T12:00:00+00:00",
        })

(OUT / "answers.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in lines) + "\n", encoding="utf-8")

# Auditorías simuladas con la misma estructura que `geo audit --format json`.
MAX = {"google_ai": 20, "robots": 14, "schema": 14, "content": 14, "brand_entity": 12, "meta": 11, "llms": 6, "signals": 6, "ai_discovery": 3}
AUDITS = {
    "bitforja": ({"google_ai": 11, "robots": 14, "schema": 6, "content": 9, "brand_entity": 7, "meta": 10, "llms": 0, "signals": 5, "ai_discovery": 0},
                 {"schema": ["Añadir schema Organization con sameAs", "Añadir FAQPage en páginas de ayuda"], "llms": ["Crear /llms.txt"]}),
    "mercadia": ({"google_ai": 16, "robots": 14, "schema": 12, "content": 11, "brand_entity": 10, "meta": 11, "llms": 4, "signals": 6, "ai_discovery": 1}, {}),
    "voltio": ({"google_ai": 12, "robots": 9, "schema": 10, "content": 8, "brand_entity": 8, "meta": 9, "llms": 0, "signals": 5, "ai_discovery": 0},
               {"robots": ["Permitir OAI-SearchBot y PerplexityBot en robots.txt"]}),
    "librotek": ({"google_ai": 9, "robots": 14, "schema": 8, "content": 7, "brand_entity": 9, "meta": 10, "llms": 0, "signals": 6, "ai_discovery": 0}, {}),
}
(OUT / "audit").mkdir(exist_ok=True)
for bid, (breakdown, recs) in AUDITS.items():
    flat = [r for v in recs.values() for r in v]
    data = {"url": f"https://{bid}.example", "score": sum(breakdown.values()), "band": "good", "error": None,
            "score_version": 2, "score_max": MAX, "score_breakdown": breakdown,
            "recommendations": flat, "recommendations_by_category": recs}
    (OUT / "audit" / f"{bid}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("Datos de demo generados en", OUT)
