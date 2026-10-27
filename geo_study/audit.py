"""Auditoría técnica con geo-optimizer (https://github.com/Auriti-Labs/geo-optimizer-skill).

No se reinventa: se ejecuta su comando `geo audit` para cada web y se guarda el
JSON. Este módulo solo lo lanza y resume lo que interesa para el informe.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from geo_study.config import Study

CATEGORY_LABELS = {
    "google_ai": "Preparación para Google IA",
    "robots": "Acceso de rastreadores de IA (robots.txt)",
    "schema": "Datos estructurados",
    "content": "Contenido citable",
    "brand_entity": "Señales de marca",
    "meta": "Metadatos",
    "llms": "Archivo llms.txt",
    "signals": "Señales técnicas",
    "ai_discovery": "Endpoints para IA",
}


def run_audits(study: Study, out_dir: Path) -> None:
    if not shutil.which("geo"):
        raise RuntimeError("No se encuentra el comando 'geo'. Instálalo con: pip install -r requirements.txt")
    out_dir.mkdir(parents=True, exist_ok=True)
    for brand in study.brands:
        out = out_dir / f"{brand.id}.json"
        print(f"→ geo audit {brand.url}")
        proc = subprocess.run(
            ["geo", "audit", "--url", brand.url, "--format", "json", "--output", str(out)],
            capture_output=True, text=True, timeout=300,
        )
        if not out.exists():
            # Si la herramienta no pudo ni escribir el archivo, se guarda el error para el informe.
            out.write_text(json.dumps({"url": brand.url, "score": 0, "error": proc.stderr.strip()[-500:]}))


def summarize_audit(data: dict) -> dict:
    """Resumen de una auditoría: puntuación, categorías, bloqueos y recomendaciones."""
    breakdown = data.get("score_breakdown") or {}
    maxima = data.get("score_max") or {}
    by_cat = data.get("recommendations_by_category") or {}
    categories = [
        {
            "key": k,
            "label": CATEGORY_LABELS.get(k, k),
            "points": breakdown.get(k, 0),
            "max": maxima.get(k, 0),
        }
        for k in CATEGORY_LABELS
        if k in breakdown
    ]
    return {
        "url": data.get("url", ""),
        "score": data.get("score", 0),
        "band": data.get("band", ""),
        "error": data.get("error"),
        "categories": categories,
        "blockers": by_cat.get("blockers", []),
        "recommendations": (data.get("recommendations") or [])[:5],
    }


def load_audits(study: Study, audit_dir: Path) -> dict[str, dict]:
    audits = {}
    for brand in study.brands:
        path = audit_dir / f"{brand.id}.json"
        if path.exists():
            audits[brand.id] = summarize_audit(json.loads(path.read_text(encoding="utf-8")))
    return audits
