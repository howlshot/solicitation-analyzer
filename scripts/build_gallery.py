"""Build the static sample-report gallery for GitHub Pages into _site/.

    python3 scripts/build_gallery.py

No model runs here: the gallery shows the committed reports in reports/ and
the evaluation in eval/results.json, so visitors can see real output without
an API key or a local model.
"""
import html
import json
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
E = html.escape


def when(item: dict | None) -> str:
    if not item or not item.get("date"):
        return "Not stated"
    d = date.fromisoformat(item["date"])
    return f"{d:%b} {d.day}, {d.year}"


def main() -> None:
    manifest = json.loads((ROOT / "samples/manifest.json").read_text())
    results = json.loads((ROOT / "eval/results.json").read_text()) if (ROOT / "eval/results.json").exists() else None
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()
    cards = []
    for pkg in manifest["packages"]:
        src = ROOT / "reports" / pkg["id"]
        if not (src / "report.json").exists():
            continue
        shutil.copytree(src, OUT / pkg["id"])
        data = json.loads((src / "report.json").read_text())
        facts = data["key_facts"]
        s = data["stats"]
        docs = ", ".join(f"{d['pages']}-page {d['role'] if d['role'] != 'base' else 'solicitation'}" for d in data["documents"])
        cards.append(
            f'<a class="card" href="{E(pkg["id"])}/report.html"><span class="kind">{E(docs)}</span>'
            f"<h2>{E(pkg['title'])}</h2>"
            f'<dl><div><dt>Response due</dt><dd>{E(when(facts["response_due"]))}</dd></div>'
            f'<div><dt>Checklist items</dt><dd>{s["kept"]}</dd></div>'
            f'<div><dt>Removed as unverifiable</dt><dd>{s["rejected"]}</dd></div></dl></a>'
        )
    summary = ""
    if results:
        m, b = results["totals"]["model"], results["totals"]["baseline"]
        pct = lambda a, t: f"{round(100 * a / t)}%" if t else "n/a"  # noqa: E731
        summary = (
            '<table><thead><tr><th>Measure</th><th>Model</th><th>Keyword baseline</th></tr></thead><tbody>'
            f"<tr><td>Key facts right</td><td>{pct(m['facts_correct'], m['facts_total'])}</td><td>{pct(b['facts_correct'], b['facts_total'])}</td></tr>"
            f"<tr><td>Evaluation factors found</td><td>{pct(m['factors_found'], m['factors_total'])}</td><td>{pct(b['factors_found'], b['factors_total'])}</td></tr>"
            f"<tr><td>Must-do items covered</td><td>{pct(m['checklist_found'], m['checklist_total'])}</td><td>{pct(b['checklist_found'], b['checklist_total'])}</td></tr>"
            f"<tr><td>Items returned</td><td>{m['items']} checklist lines</td><td>{b['items']} raw sentences</td></tr>"
            "</tbody></table>"
        )
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Solicitation Analyzer samples</title>
<meta name="description" content="Compliance checklists generated from public RFPs, RFQs and RFIs, with every item quoted from the page it cites.">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Next:wght@400;600;700&family=Young+Serif&display=swap">
<style>
:root{{color-scheme:light;--page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--line:rgba(11,11,11,.1);--accent:#1c5cab}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--line:rgba(255,255,255,.1);--accent:#86b6ef}}}}
:root[data-theme=dark]{{color-scheme:dark;--page:#0d0d0d;--surface:#1a1a19;--ink:#fff;--ink2:#c3c2b7;--line:rgba(255,255,255,.1);--accent:#86b6ef}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--page);color:var(--ink);font:400 16px/1.55 "Atkinson Hyperlegible Next",system-ui,sans-serif}}
main{{max-width:1040px;margin:0 auto;padding:40px 16px 64px}}h1,h2{{font-family:"Young Serif",Georgia,serif;font-weight:400}}
h1{{font-size:clamp(2rem,5vw,2.8rem);line-height:1.1;margin:0 0 12px}}.lede{{font-size:1.1rem;max-width:66ch;margin:0 0 12px}}.note{{color:var(--ink2);max-width:66ch}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;margin:28px 0}}
.card{{display:block;background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px;color:inherit;text-decoration:none}}.card:hover{{border-color:var(--accent)}}
.card h2{{font-size:1.2rem;line-height:1.25;margin:6px 0 12px}}.kind{{font-size:.8rem;font-weight:700;color:var(--ink2);text-transform:uppercase;letter-spacing:.04em}}
dl{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:0}}dt{{font-size:.78rem;color:var(--ink2);font-weight:700}}dd{{margin:0;font-weight:700}}
table{{border-collapse:collapse;background:var(--surface);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-top:12px}}th,td{{padding:10px 14px;border-top:1px solid var(--line);text-align:left}}thead th{{border-top:0;font-size:.85rem;color:var(--ink2)}}
a{{color:var(--accent)}}footer{{margin-top:40px;color:var(--ink2);font-size:.9rem}}
</style></head><body><main>
<p class="note">Studio Chingie · Solicitation Analyzer</p>
<h1>Checklists from real solicitations</h1>
<p class="lede">Each report below was generated from a public RFP, RFQ or RFI by a model running on a local machine. Every item quotes the page it cites, and items whose quote could not be found in the PDF were removed.</p>
<p class="note">These are saved outputs, so nothing runs when you open them. Names, emails and phone numbers are replaced with placeholders.</p>
<div class="grid">{''.join(cards)}</div>
<h2>Measured against reference answers</h2>
{summary}
<footer>Source code, test set and method: <a href="https://github.com/howlshot/solicitation-analyzer">github.com/howlshot/solicitation-analyzer</a>. Built by <a href="https://studiochingie.com/services">Studio Chingie LLC</a>.</footer>
</main></body></html>"""
    (OUT / "index.html").write_text(page)
    print(f"_site: {len(cards)} reports")


if __name__ == "__main__":
    main()
