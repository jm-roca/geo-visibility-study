"""Informe final: una página HTML autocontenida (para enseñar) y un Markdown (para GitHub).

Los gráficos se dibujan como SVG en el propio HTML, sin librerías externas: el
informe se abre en cualquier navegador, se imprime a PDF y se puede publicar tal cual.
"""

from __future__ import annotations

import html
from datetime import date

from geo_study.config import Study

# Escala secuencial (un solo tono, de claro a oscuro) para los mapas de calor.
SEQ = ["#f0efec", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95"]
TONE_LABEL = {"positivo": "Positivo", "neutro": "Neutro", "mixto": "Mixto", "negativo": "Negativo"}

CSS = """
.viz-root{color-scheme:light;--surface:#fcfcfb;--surface-2:#f4f3f0;--text:#0b0b0b;--text-2:#52514e;
--muted:#8a8984;--line:#e4e2dd;--main:#2a78d6;--other:#82817c;--warn-bg:#fff4dc;--warn-text:#6b4a00}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;
--surface:#1a1a19;--surface-2:#242422;--text:#f0efec;--text-2:#c3c2b7;--muted:#8f8e88;--line:#383835;
--main:#3987e5;--other:#77766f;--warn-bg:#3a2f12;--warn-text:#f5d48a}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;--surface:#1a1a19;--surface-2:#242422;--text:#f0efec;
--text-2:#c3c2b7;--muted:#8f8e88;--line:#383835;--main:#3987e5;--other:#77766f;--warn-bg:#3a2f12;--warn-text:#f5d48a}
*{box-sizing:border-box}
html,body{margin:0;background:var(--surface,#fcfcfb)}
body{font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.viz-root{background:var(--surface);color:var(--text);max-width:880px;margin:0 auto;padding:40px 16px 64px}
h1{font-size:2rem;line-height:1.2;margin:0 0 6px}
h2{font-size:1.25rem;margin:48px 0 4px}
.sub{color:var(--text-2);margin:0 0 4px}
.meta{color:var(--muted);font-size:.875rem;margin:0}
.lead{font-size:1.25rem;line-height:1.45;margin:28px 0 20px}
.note{color:var(--text-2);font-size:.875rem;margin:8px 0 0}
.banner{background:var(--warn-bg);color:var(--warn-text);border-radius:8px;padding:10px 14px;font-size:.875rem;margin:20px 0 0}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:8px 0}
.tile{background:var(--surface-2);border-radius:10px;padding:14px 16px}
.tile b{display:block;font-size:1.75rem;line-height:1.1;font-variant-numeric:tabular-nums}
.tile span{color:var(--text-2);font-size:.875rem}
ul.findings{padding-left:20px;margin:8px 0}
ul.findings li{margin:6px 0}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
.scroll>table.wide{min-width:560px}
table.grid{table-layout:fixed}
table.grid th:first-child,table.grid td:first-child{width:32%}
table.grid th.num{text-align:center;overflow-wrap:anywhere;hyphens:auto}
.chart{max-width:640px}
table{border-collapse:collapse;width:100%;font-size:.9rem;font-variant-numeric:tabular-nums}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{color:var(--text-2);font-weight:600}
td.num,th.num{text-align:right}
td.heat{text-align:center;border-bottom:2px solid var(--surface)}
svg text{font-family:inherit}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.card{border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.card .tone{font-size:.8rem;color:var(--text-2);font-weight:600;text-transform:uppercase;letter-spacing:.04em}
footer{margin-top:56px;color:var(--muted);font-size:.8rem;border-top:1px solid var(--line);padding-top:14px}
"""


def e(text) -> str:
    # Espacio no separable antes de "%": la cifra y su signo nunca se parten en dos líneas.
    return html.escape(str(text)).replace(" %", " %")


def heat(value: float, vmax: float) -> tuple[str, str]:
    """Color de fondo y de texto para una celda de mapa de calor.
    El cero usa la superficie del tema, para no brillar en modo oscuro."""
    idx = round(value / vmax * (len(SEQ) - 1)) if vmax > 0 else 0
    if idx == 0:
        return "var(--surface-2)", "var(--text-2)"
    return SEQ[idx], ("#ffffff" if idx >= 4 else "#0b0b0b")


def sov_chart(brands: list[dict]) -> str:
    """Barras horizontales de cuota de voz, con el intervalo de confianza como bigote."""
    row_h, top, left, width = 44, 8, 128, 480
    plot_w = width - left - 56
    height = top + row_h * len(brands) + 28
    x = lambda v: left + plot_w * v / 100  # noqa: E731
    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" '
             f'aria-label="Cuota de voz por tienda con intervalo de confianza del 95 %">']
    for tick in (0, 25, 50, 75, 100):
        parts.append(f'<line x1="{x(tick)}" x2="{x(tick)}" y1="{top}" y2="{height - 22}" stroke="var(--line)"/>')
        parts.append(f'<text x="{x(tick)}" y="{height - 6}" text-anchor="middle" font-size="12" fill="var(--muted)">{tick} %</text>')
    for i, b in enumerate(brands):
        y = top + i * row_h + 8
        s = b["share_of_voice"]
        color = "var(--main)" if b["is_main"] else "var(--other)"
        weight = "700" if b["is_main"] else "400"
        tip = f'{b["name"]}: {s["rate"]} % ({s["count"]} de {s["n"]} respuestas). IC 95 %: {s["ci"][0]}–{s["ci"][1]} %'
        parts.append(f'<g><title>{e(tip)}</title>')
        parts.append(f'<rect x="{left}" y="{y - 4}" width="{plot_w}" height="34" fill="transparent"/>')
        parts.append(f'<text x="{left - 10}" y="{y + 18}" text-anchor="end" font-size="14" font-weight="{weight}" fill="var(--text)">{e(b["name"])}</text>')
        bw = max(x(s["rate"]) - left, 0)
        parts.append(f'<rect x="{left}" y="{y + 4}" width="{bw}" height="20" rx="4" fill="{color}"/>')
        y_mid = y + 14
        parts.append(f'<line x1="{x(s["ci"][0])}" x2="{x(s["ci"][1])}" y1="{y_mid}" y2="{y_mid}" stroke="var(--text)" stroke-width="1.5"/>')
        for end in s["ci"]:
            parts.append(f'<line x1="{x(end)}" x2="{x(end)}" y1="{y_mid - 6}" y2="{y_mid + 6}" stroke="var(--text)" stroke-width="1.5"/>')
        parts.append(f'<text x="{x(max(s["ci"][1], s["rate"])) + 8}" y="{y + 19}" font-size="14" font-weight="600" fill="var(--text)">{s["rate"]} %</text>')
        parts.append("</g>")
    parts.append("</svg>")
    return "".join(parts)


def sources_chart(sources: list[dict]) -> str:
    row_h, left, width = 30, 150, 480
    plot_w = width - left - 48
    height = row_h * len(sources) + 8
    vmax = max((s["rate"] for s in sources), default=1) or 1
    parts = [f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" aria-label="Webs que la IA usa como fuente">']
    for i, s in enumerate(sources):
        y = i * row_h + 4
        color = "var(--main)" if s.get("is_main") else "var(--other)"
        label = s["domain"]
        parts.append(f'<g><title>{e(s["domain"])}: {s["answers"]} respuestas ({s["rate"]} %)</title>')
        parts.append(f'<text x="{left - 10}" y="{y + 15}" text-anchor="end" font-size="13" fill="var(--text)">{e(label)}</text>')
        parts.append(f'<rect x="{left}" y="{y + 3}" width="{max(plot_w * s["rate"] / vmax, 2)}" height="16" rx="4" fill="{color}"/>')
        parts.append(f'<text x="{left + plot_w * s["rate"] / vmax + 8}" y="{y + 16}" font-size="13" fill="var(--text-2)">{s["rate"]} %</text></g>')
    parts.append("</svg>")
    return "".join(parts)


def engine_table(metrics: dict) -> str:
    engines = metrics.get("engines") or []
    head = "".join(f'<th class="num">{e(x["name"])} <span style="color:var(--muted);font-weight:400">· {x["answers"]} resp.</span></th>' for x in engines)
    rows = []
    for b in metrics["brands"]:
        cells = []
        for x in engines:
            v = b["share_of_voice_by_engine"].get(x["id"], 0)
            bg, fg = heat(v, 100)
            cells.append(f'<td class="heat" style="background:{bg};color:{fg}">{v} %</td>')
        name = f"<b>{e(b['name'])}</b>" if b["is_main"] else e(b["name"])
        rows.append(f"<tr><td>{name}</td>{''.join(cells)}</tr>")
    return f'<div class="scroll"><table class="grid"><thead><tr><th>Tienda</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def block_table(study: Study, brands: list[dict]) -> str:
    blocks = study.sov_blocks()
    head = "".join(f'<th class="num">{e(study.blocks[b]["name"])}</th>' for b in blocks)
    rows = []
    for b in brands:
        cells = []
        for blk in blocks:
            v = b["share_of_voice_by_block"][blk]
            bg, fg = heat(v, 100)
            cells.append(f'<td class="heat" style="background:{bg};color:{fg}">{v} %</td>')
        name = f"<b>{e(b['name'])}</b>" if b["is_main"] else e(b["name"])
        rows.append(f"<tr><td>{name}</td>{''.join(cells)}</tr>")
    return f'<div class="scroll"><table class="grid"><thead><tr><th>Tienda</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def matrix_table(study: Study, metrics: dict) -> str:
    order = [b["id"] for b in metrics["brands"]]
    names = {b["id"]: b["name"] for b in metrics["brands"]}
    head = "".join(f'<th class="num">{e(names[i])}</th>' for i in order)
    rows = []
    for q in metrics["matrix"]:
        cells = []
        for bid in order:
            k = q["mentions"][bid]
            bg, fg = heat(k, max(q["runs"], 1))
            cells.append(f'<td class="heat" style="background:{bg};color:{fg}" title="{k} de {q["runs"]} respuestas">{k}/{q["runs"]}</td>')
        rows.append(f'<tr><td><span style="color:var(--muted)">{e(q["id"])}</span> {e(q["text"])}</td>{"".join(cells)}</tr>')
    return f'<div class="scroll"><table class="wide"><thead><tr><th>Pregunta</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'


def audit_table(study: Study, audits: dict) -> str:
    if not audits:
        return '<p class="note">No hay auditoría técnica en esta ejecución.</p>'
    # Categorías en filas y tiendas en columnas: así la tabla cabe en pantalla.
    brands = [b for b in study.brands if b.id in audits]
    cats = []
    for a in audits.values():
        for c in a["categories"]:
            if c["key"] not in [x["key"] for x in cats]:
                cats.append(c)
    head = "".join(
        f'<th class="num">{"<b>" + e(b.name) + "</b>" if b.id == study.main_brand else e(b.name)}</th>' for b in brands
    )
    total_cells = []
    for b in brands:
        a = audits[b.id]
        total_cells.append('<td class="num" style="color:var(--muted)">no auditable</td>' if a.get("error") else f'<td class="num"><b>{a["score"]}</b>/100</td>')
    rows = [f'<tr><td><b>Puntuación total</b></td>{"".join(total_cells)}</tr>']
    for c in cats:
        cells = []
        for b in brands:
            mine = next((x for x in audits[b.id]["categories"] if x["key"] == c["key"]), None)
            if mine and mine["max"] and not audits[b.id].get("error"):
                bg, fg = heat(mine["points"], mine["max"])
                cells.append(f'<td class="heat" style="background:{bg};color:{fg}">{mine["points"]}/{mine["max"]}</td>')
            else:
                cells.append("<td></td>")
        rows.append(f'<tr><td>{e(c["label"])}</td>{"".join(cells)}</tr>')
    errors = "".join(
        f'<p class="note">{e(b.name)}: no se pudo auditar ({e(audits[b.id]["error"])[:160]}). '
        'La web rechazó el acceso automatizado de la herramienta de auditoría; esto no indica que bloquee a los asistentes de IA.</p>'
        for b in brands if audits[b.id].get("error")
    )
    return (f'<div class="scroll"><table class="grid"><thead><tr><th>Categoría</th>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>{errors}')


def build_html(study: Study, metrics: dict, audits: dict, narrative: dict, demo: bool) -> str:
    main = next(b for b in metrics["brands"] if b["is_main"])
    rank = [b["id"] for b in metrics["brands"]].index(main["id"]) + 1
    main_domains = set(study.brand(study.main_brand).domains)
    for s in metrics["top_sources"]:
        s["is_main"] = any(s["domain"] == d or s["domain"].endswith("." + d) for d in main_domains)
    dates = ", ".join(metrics["dates"]) or date.today().isoformat()
    engines = metrics.get("engines") or []
    names = [x["name"] for x in engines] or ["Gemini"]
    engine_names = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " y " + names[-1]
    manual = any(x["id"] != "gemini-api" for x in engines)
    who = engine_names if len(engines) > 1 else (engines[0]["name"] if engines else "Gemini")
    per_question = (f"{len(engines)} asistentes x {metrics['runs_per_question'] if not manual else 1} respuesta"
                    if manual else f"{metrics['runs_per_question']} repeticiones")
    engine_section = ""
    if len(engines) > 1:
        engine_section = (
            "<h2>Por asistente</h2>"
            "<p class=\"sub\">Cuota de voz de cada tienda en cada asistente. Cada uno elige fuentes y tiendas a su manera: "
            "una marca puede estar bien posicionada en uno y ausente en otro.</p>" + engine_table(metrics)
        )
    if manual:
        method = (f"<li>{metrics['questions']} preguntas en español hechas en las aplicaciones de {e(engine_names)}, "
                  "una conversación nueva por pregunta (en ChatGPT, chat temporal para que la memoria no influya). "
                  f"Respuestas copiadas tal cual: {metrics['answers_valid']} en total.</li>"
                  + "".join(
                      f"<li>Excluida del análisis: {e(x['question'])} en {e(x['assistant_name'])} ({e(x['reason'])}).</li>"
                      for x in metrics.get("exclusions", []))
                  + "<li>Mide lo que ve un usuario real en la app. Las respuestas pueden variar según la cuenta, el momento y la ubicación (España).</li>")
    else:
        method = (f"<li>{metrics['questions']} preguntas en español, {metrics['runs_per_question']} repeticiones cada una, "
                  f"a {e(', '.join(metrics['models']) or 'Gemini')} por API con búsqueda en Google activada. "
                  f"{metrics['answers_valid']} respuestas válidas de {metrics['answers_total']}.</li>"
                  "<li>Gemini por API puede responder distinto que la aplicación que usa el público.</li>")
    rep = metrics["reputation"]

    findings = "".join(f"<li>{e(f)}</li>" for f in narrative.get("findings", []))
    cards = "".join(
        f'<div class="card"><div class="tone">{e(r["question_id"])} · {e(TONE_LABEL.get(r["tone"], r["tone"]))}</div>'
        f'<div>{e(next((q.text for q in study.questions if q.id == r["question_id"]), ""))}</div>'
        f'<p class="note">{e(r["summary"])}</p></div>'
        for r in narrative.get("reputation", [])
    ) or '<p class="note">Sin valoración de reputación en esta ejecución (la redacción con IA no estaba disponible).</p>'
    rep_sources = ", ".join(f"{e(d)} ({n})" for d, n in rep["sources"]) or "ninguna"

    actions = narrative.get("actions", [])
    actions_html = (
        '<div class="scroll"><table class="wide"><thead><tr><th>#</th><th>Acción</th><th>Por qué</th><th>Impacto</th><th>Esfuerzo</th></tr></thead><tbody>'
        + "".join(f'<tr><td>{i}</td><td>{e(a["action"])}</td><td>{e(a["why"])}</td><td>{e(a["impact"])}</td><td>{e(a["effort"])}</td></tr>'
                  for i, a in enumerate(actions, 1))
        + "</tbody></table></div>"
    ) if actions else '<p class="note">Sin plan de acción en esta ejecución (la redacción con IA no estaba disponible).</p>'

    warnings = []
    if narrative.get("unverified_numbers"):
        nums = ", ".join(f"{n} %" for n in narrative["unverified_numbers"])
        warnings.append(f"Revisión necesaria: el texto menciona cifras que no salen del análisis ({nums}).")
    banners = "".join(f'<div class="banner">{e(w)}</div>' for w in warnings)

    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(study.title)}</title><style>{CSS}</style></head>
<body><main class="viz-root">
<h1>{e(study.title)}</h1>
<p class="sub">{e(study.subtitle)}</p>
<p class="meta">{e(study.author)} · Datos recogidos: {e(dates)} · Asistentes: {e(engine_names)}</p>
<div class="banner">{e(study.disclaimer)}</div>{banners}

<p class="lead">{e(narrative.get("headline", ""))}</p>
<div class="tiles">
  <div class="tile"><b>{main["share_of_voice"]["rate"]} %</b><span>de respuestas mencionan a {e(main["name"])}</span></div>
  <div class="tile"><b>{rank}.º de {len(metrics["brands"])}</b><span>en cuota de voz</span></div>
  <div class="tile"><b>{main["first_mention"]["rate"]} %</b><span>de respuestas la citan primero</span></div>
  <div class="tile"><b>{main["cited_as_source"]["rate"]} %</b><span>usan su web como fuente</span></div>
</div>
<ul class="findings">{findings}</ul>

<h2>Cuota de voz en IA</h2>
<p class="sub">Porcentaje de respuestas a preguntas neutrales (bloques {", ".join(study.sov_blocks())}) que mencionan cada tienda, sumando {e(who)}. La línea fina con topes es el intervalo de confianza del 95 %: con {metrics["neutral_answers"]} respuestas, las diferencias pequeñas no son concluyentes.</p>
<div class="chart">{sov_chart(metrics["brands"])}</div>
{engine_section}

<h2>Por tipo de pregunta</h2>
<p class="sub">Cuota de voz de cada tienda según la intención de la pregunta.</p>
{block_table(study, metrics["brands"])}

<h2>Pregunta a pregunta</h2>
<p class="sub">En cuántas respuestas aparece cada tienda ({e(per_question)} por pregunta).</p>
{matrix_table(study, metrics)}

<h2>Qué webs usa la IA para responder</h2>
<p class="sub">Porcentaje de respuestas neutrales que citan cada web como fuente. Muestra a quién «lee» la IA para recomendar (solo cuando el asistente muestra sus fuentes). En azul, la web de la marca principal.</p>
<div class="chart">{sources_chart(metrics["top_sources"])}</div>

<h2>Reputación: cuando se pregunta por la marca</h2>
<p class="sub">En {rep["official_site_cited"]} de {rep["answers"]} respuestas se cita la web oficial. Fuentes usadas: {rep_sources}.</p>
<div class="cards">{cards}</div>

<h2>Auditoría técnica de las webs</h2>
<p class="sub">Puntuación de 0 a 100 de geo-optimizer: si los asistentes de IA pueden rastrear, entender y citar cada web. Solo se audita la página de inicio.</p>
{audit_table(study, audits)}

<h2>Plan de acción</h2>
{actions_html}

<h2>Metodología y limitaciones</h2>
<ul class="findings">
{method}
<li>Una tienda «aparece» si su nombre o dominio está en el texto de la respuesta. «Fuente» es una web que el asistente muestra como consultada.</li>
<li>Las respuestas de la IA varían entre ejecuciones y en el tiempo. Es una foto de la fecha indicada, con una muestra pequeña: los resultados son indicios.</li>
<li>Auditoría técnica: <a href="https://github.com/Auriti-Labs/geo-optimizer-skill">geo-optimizer</a> (licencia MIT), solo la página de inicio de cada web.</li>
</ul>

<footer>Resumen y plan de acción: {e(narrative.get("generated_by", ""))}. Todas las cifras del texto se verifican automáticamente contra el análisis.</footer>
</main></body></html>
"""


def build_markdown(study: Study, metrics: dict, audits: dict, narrative: dict, demo: bool) -> str:
    lines = [f"# {study.title}", "", f"_{study.subtitle}_", "", f"> {study.disclaimer}", ""]
    if demo:
        lines += ["> **DATOS SIMULADOS** (tiendas ficticias).", ""]
    lines += [f"**{narrative.get('headline', '')}**", ""]
    lines += [f"- {f}" for f in narrative.get("findings", [])]
    lines += ["", "## Cuota de voz", "", "| Tienda | Cuota de voz | IC 95 % | Citada primero | Web como fuente |", "|---|---|---|---|---|"]
    for b in metrics["brands"]:
        s = b["share_of_voice"]
        lines.append(f"| {b['name']} | {s['rate']} % | {s['ci'][0]}–{s['ci'][1]} % | {b['first_mention']['rate']} % | {b['cited_as_source']['rate']} % |")
    engines = metrics.get("engines") or []
    if len(engines) > 1:
        lines += ["", "## Por asistente", "", "| Tienda | " + " | ".join(x["name"] for x in engines) + " |",
                  "|---|" + "---|" * len(engines)]
        for b in metrics["brands"]:
            lines.append(f"| {b['name']} | " + " | ".join(f"{b['share_of_voice_by_engine'].get(x['id'], 0)} %" for x in engines) + " |")
    if audits:
        lines += ["", "## Auditoría técnica", "", "| Tienda | Puntuación |", "|---|---|"]
        for brand in study.brands:
            if brand.id in audits:
                a = audits[brand.id]
                lines.append(f"| {brand.name} | {'error' if a.get('error') else str(a['score']) + '/100'} |")
    if narrative.get("actions"):
        lines += ["", "## Plan de acción", "", "| Acción | Por qué | Impacto | Esfuerzo |", "|---|---|---|---|"]
        lines += [f"| {a['action']} | {a['why']} | {a['impact']} | {a['effort']} |" for a in narrative["actions"]]
    lines += ["", f"Informe completo con gráficos: `report.html`. Datos: {', '.join(metrics['dates'])}."]
    return "\n".join(lines) + "\n"
