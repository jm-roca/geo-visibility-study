"""Recogida de respuestas: cada pregunta x N repeticiones, guardadas tal cual.

Las respuestas brutas se guardan en JSONL (una respuesta por línea). Así el
análisis se puede repetir o mejorar sin volver a pagar llamadas, y cualquiera
puede auditar de dónde sale cada cifra del informe.

La recogida se puede interrumpir: al relanzarla, solo pregunta lo que falta o
lo que dio error. Cada respuesta se guarda en cuanto llega.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from geo_study.config import Study
from geo_study.gemini import QuotaError


def load_answers(path: Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _save(path: Path, records: dict) -> None:
    with path.open("w", encoding="utf-8") as f:
        for key in sorted(records):
            f.write(json.dumps(records[key], ensure_ascii=False) + "\n")


def pending_calls(study: Study, done: dict) -> list[tuple]:
    """Pares (pregunta, repetición) que faltan o que fallaron en una ejecución anterior."""
    return [
        (q, run)
        for q in study.questions
        for run in range(1, study.runs + 1)
        if (q.id, run) not in done or done[(q.id, run)].get("error")
    ]


def collect(study: Study, client, out_path: Path, pause: float = 0, fresh: bool = False) -> int:
    """Devuelve cuántas llamadas quedan pendientes (0 = recogida completa)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = {} if fresh else {(a["question_id"], a["run"]): a for a in load_answers(out_path)}
    todo = pending_calls(study, done)
    if not todo:
        print("Ya están todas las respuestas recogidas. Usa --fresh para empezar de cero.")
        return 0
    if done:
        print(f"Continuando: {len(todo)} llamadas pendientes de {len(study.questions) * study.runs}.\n")

    for n, (q, run) in enumerate(todo, 1):
        print(f"[{n}/{len(todo)}] {q.id} · repetición {run}...", end=" ", flush=True)
        try:
            result = client.ask(q.text)
        except QuotaError as exc:
            print(f"\n\n{exc}")
            _save(out_path, done)
            return len(pending_calls(study, done))
        done[(q.id, run)] = {"question_id": q.id, "block": q.block, "question": q.text, "run": run, **result}
        _save(out_path, done)  # se guarda tras cada respuesta: un corte no pierde nada
        print(f"ERROR: {result['error']}" if result.get("error") else f"ok ({len(result['sources'])} fuentes)")
        if pause and n < len(todo):
            time.sleep(pause)
    return len(pending_calls(study, done))
