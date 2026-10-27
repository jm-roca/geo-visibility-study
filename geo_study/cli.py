"""Punto de entrada.

  Recogida manual (gratis):
    python -m geo_study template  # crea data/manual/chatgpt.md y gemini.md con las preguntas
    python -m geo_study import    # lee esas respuestas pegadas y prepara los datos

  Recogida por API:
    python -m geo_study collect   # pregunta a Gemini y guarda las respuestas (GEMINI_API_KEY)

  Comunes:
    python -m geo_study audit     # auditoría técnica de cada web con geo-optimizer
    python -m geo_study report    # indicadores + resumen con Claude + informe HTML
    python -m geo_study all       # los tres pasos seguidos
    python -m geo_study models    # qué modelos de Gemini puede usar tu clave
    python -m geo_study report --demo   # demo con datos simulados, sin claves
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from geo_study.analyze import compute_metrics
from geo_study.audit import load_audits, run_audits
from geo_study.collect import collect, load_answers
from geo_study.config import ROOT, load_study
from geo_study.narrative import check_numbers, make_narrative, manual_prompt
from geo_study.report import build_html, build_markdown

DEMO_DIR = ROOT / "examples" / "demo"


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Estudio de visibilidad de marcas en Gemini.")
    p.add_argument("command", choices=["template", "import", "collect", "audit", "report", "all", "models"])
    p.add_argument("--config", default="config/study.yaml")
    p.add_argument("--data", default=str(ROOT / "data"), help="Carpeta de datos brutos")
    p.add_argument("--output", default=None, help="Carpeta del informe (por defecto output/)")
    p.add_argument("--demo", action="store_true", help="Usa los datos simulados de examples/demo")
    p.add_argument("--no-ai", action="store_true", help="Sin IA en la redacción: resumen automático simple")
    p.add_argument("--fresh", action="store_true", help="collect: empieza de cero en lugar de continuar")
    p.add_argument("--force", action="store_true", help="template: sobrescribe plantillas existentes")
    return p.parse_args(argv)


def load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass


def cmd_collect(study, data_dir: Path, fresh: bool) -> int:
    from geo_study.gemini import GeminiClient

    total = len(study.questions) * study.runs
    print(f"{len(study.questions)} preguntas x {study.runs} repeticiones = {total} llamadas a {study.model}"
          f" (pausa de {study.pause:g} s entre llamadas)\n")
    pending = collect(study, GeminiClient(study.model), data_dir / "answers.jsonl", study.pause, fresh)
    if pending:
        print(f"\nQuedan {pending} llamadas pendientes. Vuelve a lanzar 'collect' para completarlas;"
              " lo ya recogido no se repite.")
        print("Puedes generar el informe igualmente con lo que hay: python -m geo_study report")
        return 1
    print(f"\nListo: {total} respuestas recogidas.")
    return 0


def cmd_template(study, data_dir: Path, force: bool) -> int:
    from geo_study.manual import write_templates

    if not study.assistants:
        raise ValueError("No hay asistentes en la sección 'manual' de config/study.yaml")
    for path in write_templates(study, data_dir / "manual", force):
        print(f"Creada: {path}")
    print("\nAbre cada archivo en VS Code, sigue las instrucciones de arriba y pega las respuestas.")
    print("Cuando termines: python -m geo_study import")
    return 0


def cmd_import(study, data_dir: Path) -> int:
    from geo_study.manual import import_manual

    summary = import_manual(study, data_dir / "manual", data_dir / "answers.jsonl")
    total = 0
    for name, s in summary.items():
        if s.get("missing_file"):
            print(f"{name}: no encuentro su archivo (ejecuta 'template')")
            continue
        total += s["filled"]
        line = f"{name}: {s['filled']} de {len(study.questions)} respuestas"
        if s["empty"]:
            line += f" · sin rellenar: {', '.join(s['empty'])}"
        if s.get("excluded"):
            line += f" · excluidas (ver config): {', '.join(s['excluded'])}"
        if not s["date"]:
            line += " · AVISO: falta la fecha (línea 'Fecha:'), uso la de hoy"
        print(line)
    if not total:
        print("\nNo hay ninguna respuesta pegada todavía.")
        return 1
    print(f"\nListo: {total} respuestas en {data_dir / 'answers.jsonl'}. Siguiente paso: audit y report.")
    return 0


def cmd_report(study, data_dir: Path, out_dir: Path, demo: bool, use_ai: bool) -> int:
    answers = load_answers(data_dir / "answers.jsonl")
    if not answers:
        raise FileNotFoundError("No hay respuestas en data/answers.jsonl. Ejecuta antes 'import' (recogida manual) o 'collect' (API).")
    metrics = compute_metrics(answers, study)
    audits = load_audits(study, data_dir / "audit")
    reputation_answers = [a for a in answers if a["block"] not in study.sov_blocks() and not a.get("error")]

    if demo:
        # En la demo, el texto de Claude también está pregrabado (no hace falta clave).
        narrative = json.loads((data_dir / "narrative.json").read_text(encoding="utf-8"))
        narrative["unverified_numbers"] = check_numbers(narrative, metrics)
    else:
        narrative = make_narrative(study, metrics, audits, reputation_answers, use_ai, data_dir / "narrative.json")

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "narrative.json").write_text(json.dumps(narrative, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out_dir / "share_of_voice.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["brand", "share_of_voice_pct", "ci_low", "ci_high", "first_mention_pct", "cited_as_source_pct", "answers"])
        for b in metrics["brands"]:
            s = b["share_of_voice"]
            w.writerow([b["name"], s["rate"], s["ci"][0], s["ci"][1], b["first_mention"]["rate"], b["cited_as_source"]["rate"], s["n"]])
    (out_dir / "report.html").write_text(build_html(study, metrics, audits, narrative, demo), encoding="utf-8")
    (out_dir / "report.md").write_text(build_markdown(study, metrics, audits, narrative, demo), encoding="utf-8")

    if not demo:
        prompt_path = out_dir / "prompt_para_claude.md"
        prompt_path.write_text(manual_prompt(study, metrics, audits, reputation_answers), encoding="utf-8")
        if "sin IA" in narrative.get("generated_by", "") and use_ai:
            print("\nEl informe lleva un resumen simple, sin plan de acción. Para añadirlo gratis con Claude.ai:")
            print(f"  1. Abre {prompt_path}, selecciona todo (Ctrl+A) y cópialo.")
            print("  2. Pégalo en un chat nuevo de claude.ai.")
            print(f"  3. Copia el JSON que te devuelva y guárdalo en {data_dir / 'narrative.json'}")
            print("  4. Vuelve a ejecutar: python -m geo_study report\n")
    if narrative.get("unverified_numbers"):
        print(f"AVISO: el resumen menciona cifras que no salen del análisis: {narrative['unverified_numbers']}")
    print(f"Informe: {out_dir / 'report.html'}")
    return 0


def cmd_models() -> int:
    from geo_study.gemini import list_models

    models = list_models()
    print("Modelos disponibles para tu clave (copia el id en 'model' de config/study.yaml):\n")
    for m in sorted(models, key=lambda m: m["id"]):
        print(f"  {m['id']:<40} {m['name']}")
    print("\nPara la búsqueda en Google usa uno de la familia 'gemini-2.5' o superior, tipo 'flash'.")
    return 0


def main(argv=None) -> int:
    args = parse_args(argv)
    load_env()
    if args.command == "models":
        try:
            return cmd_models()
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
    if args.demo:
        study = load_study(DEMO_DIR / "study.yaml")
        data_dir = DEMO_DIR
        if args.command != "report":
            print("En modo demo los datos ya están recogidos: usa 'report --demo'.")
            return 2
    else:
        study = load_study(args.config)
        data_dir = Path(args.data)
    out_dir = Path(args.output) if args.output else ROOT / "output" / ("demo" if args.demo else "")

    try:
        if args.command == "template":
            return cmd_template(study, data_dir, args.force)
        if args.command == "import":
            return cmd_import(study, data_dir)
        if args.command in ("collect", "all"):
            if cmd_collect(study, data_dir, args.fresh) and args.command == "collect":
                return 1
        if args.command in ("audit", "all"):
            run_audits(study, data_dir / "audit")
        if args.command in ("report", "all"):
            return cmd_report(study, data_dir, out_dir, args.demo, not args.no_ai)
    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
