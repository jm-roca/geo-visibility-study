"""Consulta a Gemini con búsqueda en Google activada (grounding).

Por qué no se usa directamente `geo citations` de geo-optimizer: esa herramienta
pregunta a Gemini sin búsqueda, así que Gemini responde solo con lo que aprendió
en su entrenamiento y no devuelve fuentes. Activando la herramienta `google_search`
la respuesta se parece a la que ve un usuario y trae las webs consultadas.

Documentación: https://ai.google.dev/gemini-api/docs/google-search
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
REDIRECT_HOSTS = ("vertexaisearch.cloud.google.com",)


def normalize_domain(value: str) -> str:
    """'https://www.Fnac.es/x' -> 'fnac.es' · 'www.amazon.es' -> 'amazon.es'."""
    value = (value or "").strip().lower()
    if "://" in value:
        value = urlparse(value).hostname or ""
    value = value.split("/")[0]
    return value[4:] if value.startswith("www.") else value


def source_domain(uri: str, title: str) -> str:
    """Dominio real de una fuente.

    Gemini devuelve las fuentes como enlaces de redirección de Google; en ese caso
    el dominio de verdad suele venir en el título. Si el enlace es directo, se usa
    el del enlace.
    """
    host = normalize_domain(uri)
    if host and not host.endswith(REDIRECT_HOSTS):
        return host
    candidate = normalize_domain(title)
    return candidate if "." in candidate and " " not in candidate else ""


def parse_response(data: dict) -> dict:
    """Extrae texto, fuentes, búsquedas y tokens de la respuesta de la API."""
    candidates = data.get("candidates") or []
    if not candidates:
        reason = (data.get("promptFeedback") or {}).get("blockReason", "sin respuesta")
        return {"text": "", "sources": [], "search_queries": [], "error": f"Gemini no respondió: {reason}"}

    cand = candidates[0]
    parts = (cand.get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts)
    meta = cand.get("groundingMetadata") or {}

    sources, seen = [], set()
    for chunk in meta.get("groundingChunks") or []:
        web = chunk.get("web") or {}
        domain = source_domain(web.get("uri", ""), web.get("title", ""))
        if domain and domain not in seen:
            seen.add(domain)
            sources.append({"domain": domain, "title": web.get("title", "")})

    usage = data.get("usageMetadata") or {}
    return {
        "text": text,
        "sources": sources,
        "search_queries": meta.get("webSearchQueries") or [],
        "input_tokens": usage.get("promptTokenCount", 0),
        "output_tokens": usage.get("candidatesTokenCount", 0),
        "error": None if text else "Respuesta vacía",
    }


class GeminiClient:
    def __init__(self, model: str, timeout: int = 60, retries: int = 3):
        import requests  # solo hace falta en modo real

        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "Falta GEMINI_API_KEY. Créala en https://aistudio.google.com/apikey "
                "y pégala en el archivo .env (ver .env.example)."
            )
        self.session = requests.Session()
        self.model = model
        self.timeout = timeout
        self.retries = retries

    def _post(self, payload: dict, model: str | None = None) -> dict:
        """Envía la petición y gestiona los límites de uso (error 429).

        - Límite por minuto: espera lo que indique Google (retryDelay) y reintenta.
        - Cuota diaria agotada o modelo sin nivel gratuito: para con un mensaje claro,
          porque reintentar no sirve de nada.
        """
        model = model or self.model
        last_error = ""
        for attempt in range(1, self.retries + 1):
            try:
                resp = self.session.post(
                    API_URL.format(model=model),
                    headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json"},
                    json=payload,
                    timeout=self.timeout,
                )
            except Exception as exc:  # error de red: se reintenta
                last_error = f"{type(exc).__name__}: {exc}"
                time.sleep(5 * attempt)
                continue
            if resp.status_code == 429:
                info = explain_429(_safe_json(resp))
                if info["fatal"]:
                    raise QuotaError(info["message"])
                wait = info["retry_after"] or 20 * attempt
                print(f"(límite por minuto, espero {wait} s) ", end="", flush=True)
                last_error = info["message"]
                time.sleep(wait)
                continue
            if resp.status_code >= 500:
                last_error = f"HTTP {resp.status_code}"
                time.sleep(5 * attempt)
                continue
            if resp.status_code >= 400:
                detail = (_safe_json(resp).get("error") or {}).get("message", "")
                hint = ""
                if resp.status_code == 404:
                    hint = ("\nEl modelo '" + model + "' no existe o no está disponible para tu clave. "
                            "Ejecuta 'python -m geo_study models' para ver los disponibles y cambia "
                            "'model' en config/study.yaml.")
                raise RuntimeError(f"Gemini rechazó la petición (HTTP {resp.status_code}): {detail}{hint}")
            return resp.json()
        raise TemporaryError(last_error)

    def ask(self, question: str) -> dict:
        payload = {
            "contents": [{"role": "user", "parts": [{"text": question}]}],
            "tools": [{"google_search": {}}],
        }
        try:
            data = self._post(payload)
        except TemporaryError as exc:
            return {"text": "", "sources": [], "search_queries": [], "error": str(exc), "model": self.model}
        result = parse_response(data)
        result["model"] = data.get("modelVersion", self.model)
        result["asked_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return result

    def generate_json(self, system: str, prompt: str, schema: dict, model: str | None = None) -> dict:
        """Respuesta en JSON con un esquema fijo (sin búsqueda). Se usa para redactar el informe."""
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "responseSchema": schema},
        }
        data = self._post(payload, model)
        parts = (data["candidates"][0].get("content") or {}).get("parts") or []
        return json.loads("".join(p.get("text", "") for p in parts))


def list_models() -> list[dict]:
    """Modelos que puede usar tu clave para generar texto (consulta a la API de Google)."""
    import requests

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Falta GEMINI_API_KEY en el archivo .env")
    resp = requests.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        headers={"x-goog-api-key": key}, params={"pageSize": 1000}, timeout=30,
    )
    resp.raise_for_status()
    return [
        {"id": m["name"].removeprefix("models/"), "name": m.get("displayName", "")}
        for m in resp.json().get("models", [])
        if "generateContent" in (m.get("supportedGenerationMethods") or [])
    ]


class QuotaError(RuntimeError):
    """Cuota agotada: no tiene sentido seguir reintentando."""


class TemporaryError(RuntimeError):
    """Fallo temporal que persiste tras los reintentos."""


def _safe_json(resp) -> dict:
    try:
        return resp.json()
    except Exception:
        return {}


def explain_429(body: dict) -> dict:
    """Traduce el error 429 de Google a algo comprensible y decide si merece la pena reintentar."""
    error = body.get("error") or {}
    message = error.get("message", "")
    retry_after, quota_ids = 0, []
    for detail in error.get("details") or []:
        if "retryDelay" in detail:
            retry_after = int(float(str(detail["retryDelay"]).rstrip("s") or 0)) + 1
        for v in detail.get("violations") or []:
            quota_ids.append(v.get("quotaId", ""))
    ids = " ".join(quota_ids)

    if "limit: 0" in message:
        return {"fatal": True, "retry_after": 0, "message": (
            "Este modelo no tiene cuota gratuita para tu cuenta. Cambia 'model' en config/study.yaml "
            "por otro modelo (por ejemplo gemini-2.5-flash) o activa la facturación en Google AI Studio.")}
    if "PerDay" in ids:
        return {"fatal": True, "retry_after": 0, "message": (
            "Se ha agotado la cuota diaria gratuita de Gemini. Lo ya recogido está guardado: "
            "vuelve a lanzar 'collect' mañana y continuará donde se quedó.")}
    return {"fatal": False, "retry_after": retry_after, "message": f"Límite por minuto de Gemini: {message[:200]}"}
