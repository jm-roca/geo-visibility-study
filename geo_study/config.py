"""Carga y validación de la configuración del estudio (config/study.yaml)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Brand:
    id: str
    name: str
    url: str
    domains: list[str]
    aliases: list[str]


@dataclass
class Question:
    id: str
    block: str
    text: str


@dataclass
class Study:
    title: str
    subtitle: str
    author: str
    disclaimer: str
    main_brand: str
    model: str
    runs: int
    brands: list[Brand]
    blocks: dict[str, dict]
    questions: list[Question]
    pause: float = 0
    narrative_provider: str = "auto"
    narrative_gemini_model: str = ""
    assistants: list[dict] = field(default_factory=list)
    exclusions: list[dict] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    def brand(self, brand_id: str) -> Brand:
        return next(b for b in self.brands if b.id == brand_id)

    def sov_blocks(self) -> list[str]:
        """Bloques que cuentan para la cuota de voz (preguntas neutrales)."""
        return [k for k, v in self.blocks.items() if v.get("share_of_voice")]


def load_study(path: str | Path) -> Study:
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    brands = [Brand(**b) for b in data["brands"]]
    questions = [Question(**q) for q in data["questions"]]
    study = Study(
        title=data["study"]["title"],
        subtitle=data["study"]["subtitle"],
        author=data["study"].get("author", ""),
        disclaimer=data["study"]["disclaimer"].strip(),
        main_brand=data["study"]["main_brand"],
        model=data["engine"]["model"],
        runs=int(data["engine"]["runs_per_question"]),
        brands=brands,
        blocks=data["blocks"],
        questions=questions,
        pause=float(data["engine"].get("pause_seconds", 0)),
        narrative_provider=(data.get("narrative") or {}).get("provider", "auto"),
        narrative_gemini_model=(data.get("narrative") or {}).get("gemini_model", data["engine"]["model"]),
        assistants=list((data.get("manual") or {}).get("assistants") or []),
        exclusions=list((data.get("manual") or {}).get("exclude") or []),
        raw=data,
    )
    _validate(study)
    return study


def _validate(study: Study) -> None:
    """Errores de configuración claros antes de gastar una sola llamada de API."""
    ids = [b.id for b in study.brands]
    if study.main_brand not in ids:
        raise ValueError(f"main_brand '{study.main_brand}' no está en la lista de marcas")
    if len(set(ids)) != len(ids):
        raise ValueError("Hay ids de marca repetidos")
    qids = [q.id for q in study.questions]
    if len(set(qids)) != len(qids):
        raise ValueError("Hay ids de pregunta repetidos")
    for q in study.questions:
        if q.block not in study.blocks:
            raise ValueError(f"La pregunta {q.id} usa el bloque '{q.block}', que no está definido")
    if study.narrative_provider not in ("auto", "claude", "gemini", "file", "none"):
        raise ValueError("narrative.provider debe ser auto, claude, gemini, file o none")
    for a in study.assistants:
        if not re.fullmatch(r"[a-z0-9_-]+", str(a.get("id", ""))) or not a.get("name"):
            raise ValueError("Cada asistente de 'manual' necesita un id (minúsculas, sin espacios) y un name")
    assistant_ids = {a["id"] for a in study.assistants}
    for x in study.exclusions:
        if x.get("assistant") not in assistant_ids or x.get("question") not in qids or not x.get("reason"):
            raise ValueError("Cada exclusión necesita assistant y question válidos y un reason")
    if study.runs < 1:
        raise ValueError("runs_per_question debe ser al menos 1")
