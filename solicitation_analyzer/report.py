"""Reports: JSON for machines, Markdown for pasting, HTML for reading."""
from __future__ import annotations

import html
import json
from datetime import date
from pathlib import Path

from .analyze import Analysis, key_facts
from .redact import contact_names, redact
from .schema import CATEGORIES, CATEGORY_TITLES, Item


def write_reports(analysis: Analysis, out: Path, redact_contacts: bool = False) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    if redact_contacts:
        names = contact_names([p.searchable for d in analysis.documents for p in d.pages])
        clean = lambda s: redact(s, names)  # noqa: E731
    else:
        clean = lambda s: s  # noqa: E731
    data = to_json(analysis, clean)
    paths = [out / "report.json", out / "report.md", out / "report.html"]
    paths[0].write_text(json.dumps(data, indent=2) + "\n")
    paths[1].write_text(to_markdown(data))
    paths[2].write_text(to_html(data))
    return paths


def _item(i: Item, clean) -> dict:
    d = i.to_dict()
    d["statement"] = clean(i.statement)
    d["quote"] = clean(i.quote)
    return d


def to_json(analysis: Analysis, clean=lambda s: s) -> dict:
    facts = key_facts(analysis)
    return {
        "title": analysis.title,
        "created": analysis.created,
        "model": analysis.model,
        "provider": analysis.provider,
        "seconds": analysis.seconds,
        "documents": [{"id": d.id, "title": d.title, "short": d.short or d.title, "role": d.role, "pages": len(d.pages)} for d in analysis.documents],
        "key_facts": {k: ([_item(i, clean) for i in v] if isinstance(v, list) else (_item(v, clean) if v else None)) for k, v in facts.items()},
        "items": [_item(i, clean) for i in analysis.items],
        "rejected": [_item(i, clean) for i in analysis.rejected],
        "errors": analysis.errors,
        "stats": {
            "kept": len(analysis.kept),
            "superseded": sum(1 for i in analysis.items if i.superseded_by),
            "rejected": len(analysis.rejected),
            "exact": sum(1 for i in analysis.items if i.verification == "exact"),
            "fuzzy": sum(1 for i in analysis.items if i.verification == "fuzzy"),
            "assembled": sum(1 for i in analysis.items if i.verification == "assembled"),
            "warnings": sum(1 for i in analysis.items if i.warnings),
        },
    }


def _when(item: dict | None) -> str:
    if not item:
        return "Not found"
    out = item["date"] or item["statement"]
    if item["date"]:
        d = date.fromisoformat(item["date"])
        out = f"{d:%B} {d.day}, {d.year}"
        if item["time"]:
            h, m = map(int, item["time"].split(":"))
            out += f", {(h % 12) or 12}:{m:02d} {'PM' if h >= 12 else 'AM'}"
    return out


def _doc_titles(data: dict) -> dict:
    return {d["id"]: d["title"] for d in data["documents"]}


def _doc_short(data: dict) -> dict:
    return {d["id"]: d.get("short") or d["title"] for d in data["documents"]}


def _cite(item: dict, data: dict) -> str:
    base = data["documents"][0]["id"]
    where = (f"pp. {item['page']}–{item['end_page']}" if item.get("end_page") else f"p. {item['page']}") + (
        f", also p. {', '.join(map(str, item['also_on']))}" if item["also_on"] else ""
    )
    if item["document"] != base:
        where = f"{_doc_short(data)[item['document']]}, {where}"
    return where


# ---------------------------------------------------------------- markdown

def to_markdown(data: dict) -> str:
    facts = data["key_facts"]
    lines = [f"# {data['title']}", "", f"Generated {data['created'][:10]} with {data['model']}. Every item quotes the page it cites.", "", "## Key facts", ""]
    for label, key in [("Response due", "response_due"), ("Questions due", "questions_due")]:
        lines.append(f"- **{label}:** {_when(facts[key])}" + (f" ({_cite(facts[key], data)})" if facts[key] else ""))
    for label, key in [("Submit", "submission_method"), ("Page limit", "page_limit"), ("Basis of award", "basis_of_award"), ("Set-aside", "set_aside"), ("NAICS", "naics")]:
        f = facts[key]
        lines.append(f"- **{label}:** " + (f"{f['statement']} ({_cite(f, data)})" if f else "Not found"))
    for cat, kinds in CATEGORIES.items():
        group = [i for i in data["items"] if i["kind"] in kinds]
        if not group:
            continue
        lines += ["", f"## {CATEGORY_TITLES[cat]}", ""]
        for i in group:
            box = "~~" if i["superseded_by"] else ""
            extra = f" **{i['weight']}**" if i["weight"] else ""
            lines.append(f"- [ ] {box}{i['statement']}{box}{extra} ({_cite(i, data)})")
            lines.append(f"  > {i['quote']}")
            for w in i["warnings"]:
                lines.append(f"  - Check: {w}")
    if data["rejected"]:
        lines += ["", "## Removed: quote not found in the document", ""]
        for i in data["rejected"]:
            lines.append(f"- {i['statement']} (claimed p. {i['cited_page']})")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- html

E = html.escape

CSS = """
:root{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--line:rgba(11,11,11,.1);--grid:#e1e0d9;--accent:#1c5cab;--warn-bg:#fff4dc;--warn-ink:#6b4a00;--ok:#006300;--quote:#f1f0ec}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--line:rgba(255,255,255,.1);--grid:#2c2c2a;--accent:#86b6ef;--warn-bg:#3a2e12;--warn-ink:#ffd27a;--ok:#0ca30c;--quote:#232321}}
:root[data-theme=dark]{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--line:rgba(255,255,255,.1);--grid:#2c2c2a;--accent:#86b6ef;--warn-bg:#3a2e12;--warn-ink:#ffd27a;--ok:#0ca30c;--quote:#232321}
*{box-sizing:border-box}body{margin:0;background:var(--page);color:var(--ink);font:400 16px/1.55 "Atkinson Hyperlegible Next",system-ui,sans-serif}
main{max-width:1040px;margin:0 auto;padding:32px 16px 64px}
h1,h2{font-family:"Young Serif",Georgia,serif;font-weight:400;margin:0}h1{font-size:clamp(1.8rem,4vw,2.6rem);line-height:1.15}h2{font-size:1.35rem;margin:40px 0 12px}
.eyebrow{font-size:.8rem;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--ink2);margin:0 0 10px}
.meta{color:var(--ink2);font-size:.92rem;margin:12px 0 0}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-top:24px}
.fact{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.fact .label{font-size:.82rem;font-weight:700;color:var(--ink2)}.fact .value{font-size:1.1rem;font-weight:700;margin-top:4px}.fact .value.big{font-size:1.45rem}.fact .cite{font-size:.82rem;color:var(--ink2);margin-top:4px;overflow-wrap:anywhere;text-align:left;white-space:normal}
.stats{display:flex;flex-wrap:wrap;gap:8px 20px;margin-top:20px;font-size:.92rem;color:var(--ink2)}.stats strong{color:var(--ink)}
.group{background:var(--surface);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.item{display:grid;grid-template-columns:24px 1fr auto;gap:4px 12px;padding:14px 16px;border-top:1px solid var(--grid)}.item:first-child{border-top:0}
.item input{margin:4px 0 0;width:18px;height:18px;accent-color:var(--accent)}
.statement{font-weight:600}.weight{display:inline-block;margin-left:8px;padding:0 8px;border-radius:999px;border:1px solid var(--line);font-size:.85rem;font-weight:700}
.cite{white-space:nowrap;font-size:.85rem;color:var(--ink2);text-align:right}
blockquote{grid-column:2/4;margin:6px 0 0;padding:8px 12px;background:var(--quote);border-radius:8px;font-size:.92rem;color:var(--ink2)}
.badge{font-size:.75rem;font-weight:700;color:var(--ok);margin-left:8px;white-space:nowrap}.badge.fuzzy{color:var(--ink2)}
.warn{grid-column:2/4;margin:6px 0 0;padding:6px 10px;border-radius:8px;background:var(--warn-bg);color:var(--warn-ink);font-size:.88rem}
.warn::before{content:"⚠ ";font-weight:700}
.superseded .statement{text-decoration:line-through;color:var(--ink2)}.superseded .note{grid-column:2/4;font-size:.85rem;color:var(--ink2)}
table{border-collapse:collapse;width:100%;background:var(--surface);border:1px solid var(--line);border-radius:12px;overflow:hidden}th,td{text-align:left;padding:10px 14px;border-top:1px solid var(--grid);vertical-align:top}thead th{border-top:0;font-size:.82rem;color:var(--ink2)}td.num{white-space:nowrap;font-weight:700}
details{margin-top:12px}summary{cursor:pointer;font-weight:700}
.rejected{color:var(--ink2);font-size:.92rem}
footer{margin-top:48px;color:var(--ink2);font-size:.85rem;border-top:1px solid var(--line);padding-top:16px}
@media (max-width:640px){.item{grid-template-columns:24px 1fr}.cite{grid-column:2;text-align:left}blockquote,.warn,.superseded .note{grid-column:1/3}}
@media print{.item input{display:none}}
"""


def _fact(label: str, item: dict | None, data: dict, value: str | None = None, big: bool = False) -> str:
    text = value if value is not None else (item["statement"] if item else "Not found")
    cite = f'<div class="cite">{E(_cite(item, data))}</div>' if item else ""
    return f'<div class="fact"><div class="label">{E(label)}</div><div class="value{" big" if big else ""}">{E(text)}</div>{cite}</div>'


def _item_html(i: dict, data: dict) -> str:
    cls = "item superseded" if i["superseded_by"] else "item"
    badge = {
        "exact": '<span class="badge">quote verified</span>',
        "fuzzy": f'<span class="badge fuzzy">close match {round(i["similarity"] * 100)}%</span>',
        "assembled": '<span class="badge fuzzy">words found in a table</span>',
    }.get(i["verification"], "")
    weight = f'<span class="weight">{E(i["weight"])}</span>' if i["weight"] else ""
    parts = [
        f'<div class="{cls}"><input type="checkbox" aria-label="Done">',
        f'<div><span class="statement">{E(i["statement"])}</span>{weight}{badge}</div>',
        f'<div class="cite">{E(_cite(i, data))}</div>',
        f"<blockquote>{E(i['quote'])}</blockquote>",
    ]
    if i["superseded_by"]:
        parts.append(f'<div class="note">Replaced by {E(_doc_short(data).get(i["superseded_by"], i["superseded_by"]))}.</div>')
    parts += [f'<div class="warn">{E(w)}</div>' for w in i["warnings"]]
    parts.append("</div>")
    return "".join(parts)


def to_html(data: dict) -> str:
    facts = data["key_facts"]
    s = data["stats"]
    docs = ", ".join(f"{E(d['title'])} ({d['pages']} pages{', ' + d['role'] if d['role'] != 'base' else ''})" for d in data["documents"])
    out = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        f"<title>{E(data['title'])} · Solicitation checklist</title>",
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Next:wght@400;600;700&family=Young+Serif&display=swap">',
        f"<style>{CSS}</style></head><body><main>",
        '<p class="eyebrow">Compliance checklist</p>',
        f"<h1>{E(data['title'])}</h1>",
        f'<p class="meta">{docs}</p>',
        '<div class="facts">',
        _fact("Response due", facts["response_due"], data, _when(facts["response_due"]), big=True),
        _fact("Questions due", facts["questions_due"], data, _when(facts["questions_due"])),
        _fact("How to submit", facts["submission_method"], data),
        _fact("Basis of award", facts["basis_of_award"], data),
        _fact("Set-aside", facts["set_aside"], data),
        _fact("Page limit", facts["page_limit"], data),
        "</div>",
        f'<div class="stats"><span><strong>{s["kept"]}</strong> checklist items</span><span><strong>{s["exact"]}</strong> quotes found word for word</span>'
        f'<span><strong>{s["fuzzy"]}</strong> close matches</span>' + (f'<span><strong>{s["assembled"]}</strong> read across table cells</span>' if s.get("assembled") else "") + f'<span><strong>{s["rejected"]}</strong> removed, quote not in the document</span>'
        f'<span><strong>{s["warnings"]}</strong> flagged to check</span></div>',
    ]
    if facts["evaluation_factors"]:
        out.append("<h2>Evaluation factors</h2><table><thead><tr><th>Factor</th><th>Weight</th><th>Source</th></tr></thead><tbody>")
        for f in facts["evaluation_factors"]:
            out.append(f'<tr><td>{E(f["statement"])}</td><td class="num">{E(f["weight"] or "Not stated")}</td><td class="cite">{E(_cite(f, data))}</td></tr>')
        out.append("</tbody></table>")
    for cat, kinds in CATEGORIES.items():
        group = [i for i in data["items"] if i["kind"] in kinds]
        if group:
            out.append(f'<h2>{E(CATEGORY_TITLES[cat])} <span class="meta">({len(group)})</span></h2><div class="group">')
            out += [_item_html(i, data) for i in group]
            out.append("</div>")
    if data["rejected"]:
        out.append(f'<details><summary>Removed items ({len(data["rejected"])}): the quoted words are not in the document</summary><ul class="rejected">')
        out += [f'<li>{E(i["statement"])} <em>(claimed page {E(str(i["cited_page"]))})</em></li>' for i in data["rejected"]]
        out.append("</ul></details>")
    if data["errors"]:
        out.append('<details open><summary>Problems during the run</summary><ul class="rejected">' + "".join(f"<li>{E(e)}</li>" for e in data["errors"]) + "</ul></details>")
    out.append(
        f'<footer>Generated {E(data["created"][:10])} by Solicitation Analyzer with {E(data["model"])} in {data["seconds"]:.0f} seconds. '
        "Every item quotes the page it cites, and items whose quote could not be found were removed. "
        "Check deadlines and requirements against the solicitation before you submit.</footer></main></body></html>"
    )
    return "\n".join(out)
