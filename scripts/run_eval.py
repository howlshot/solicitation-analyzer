"""Score the sample reports and the keyword baseline against eval/gold.

    python3 scripts/run_eval.py

Writes eval/results.json and eval/RESULTS.md. Needs the sample PDFs (for the
baseline) and the reports from scripts/run_samples.py.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from solicitation_analyzer import baseline  # noqa: E402
from solicitation_analyzer.pdf import extract_pages  # noqa: E402
from solicitation_analyzer.redact import contact_names, redact  # noqa: E402
from solicitation_analyzer.scoring import FACT_KEYS, score  # noqa: E402

LABELS = {
    "response_due": "Response due date", "questions_due": "Questions due date", "submission_method": "How to submit",
    "page_limit": "Page limit", "basis_of_award": "Basis of award", "set_aside": "Set-aside", "naics": "NAICS code",
}


def main() -> None:
    manifest = json.loads((ROOT / "samples/manifest.json").read_text())
    docs = {d["id"]: d for d in manifest["documents"]}
    results = []
    for pkg in manifest["packages"]:
        gold = json.loads((ROOT / f"eval/gold/{pkg['id']}.json").read_text())
        report_path = ROOT / f"reports/{pkg['id']}/report.json"
        if not report_path.exists():
            print(f"skip {pkg['id']}: no report yet")
            continue
        report = json.loads(report_path.read_text())
        roles = [(pkg["base"], "base")] + [(a, "amendment") for a in pkg["amendments"]] + [(a, "attachment") for a in pkg["attachments"]]
        pages = {i: extract_pages(ROOT / "samples" / docs[i]["file"]) for i, _ in roles}
        base = baseline.run([(i, r, pages[i]) for i, r in roles])
        # Score first, then redact what gets written out, so redaction cannot move a score.
        base_score = score(gold, base)
        names = contact_names([p.searchable for ps in pages.values() for p in ps])
        for fact in base_score["facts"].values():
            fact["got"] = redact(fact["got"], names)
        results.append({
            "package": pkg["id"],
            "title": pkg["title"],
            "model": score(gold, report),
            "baseline": base_score,
            "verification": report["stats"],
            "seconds": report["seconds"],
        })
    totals = {}
    for who in ("model", "baseline"):
        totals[who] = {k: sum(r[who][k] for r in results) for k in ["facts_correct", "facts_total", "times_correct", "times_total", "factors_found", "factors_total", "checklist_found", "checklist_total", "items"]}
    totals["verification"] = {k: sum(r["verification"].get(k, 0) for r in results) for k in ["kept", "rejected", "exact", "fuzzy", "assembled", "warnings", "superseded"]}
    out = {"model": json.loads(report_path.read_text())["model"], "packages": results, "totals": totals}
    (ROOT / "eval/results.json").write_text(json.dumps(out, indent=2) + "\n")
    (ROOT / "eval/RESULTS.md").write_text(markdown(out))
    print(markdown(out))


def pct(a: int, b: int) -> str:
    return f"{a}/{b} ({round(100 * a / b) if b else 0}%)"


def markdown(out: dict) -> str:
    t = out["totals"]
    m, b, v = t["model"], t["baseline"], t["verification"]
    lines = [
        "# Evaluation results",
        "",
        f"Model: `{out['model']}`, run locally. Baseline: keyword rules with no model (`solicitation_analyzer/baseline.py`).",
        f"Reference answers: `eval/gold/`, written by reading each solicitation. {len(out['packages'])} packages, "
        f"{sum(r['verification']['kept'] + r['verification']['rejected'] for r in out['packages'])} model items checked.",
        "",
        "| Measure | Model | Keyword baseline |",
        "|---|---:|---:|",
        f"| Key facts right (7 per package) | {pct(m['facts_correct'], m['facts_total'])} | {pct(b['facts_correct'], b['facts_total'])} |",
        f"| Deadline times right | {pct(m['times_correct'], m['times_total'])} | {pct(b['times_correct'], b['times_total'])} |",
        f"| Evaluation factors found | {pct(m['factors_found'], m['factors_total'])} | {pct(b['factors_found'], b['factors_total'])} |",
        f"| Must-do checklist items covered | {pct(m['checklist_found'], m['checklist_total'])} | {pct(b['checklist_found'], b['checklist_total'])} |",
        f"| Items returned | {m['items']} checklist lines | {b['items']} raw sentences |",
        "",
        "## Quote verification",
        "",
        f"Every model item must quote the page it cites. Of {v['kept'] + v['rejected']} items, {v['exact']} quotes were found word for word, "
        f"{v['fuzzy']} were close matches (90% or more), {v.get('assembled', 0)} were read across table cells, "
        f"and {v['rejected']} were removed because the words are not in the document. "
        f"{v['warnings']} items carry a warning for a person to check, and {v['superseded']} deadlines were replaced by an amendment.",
        "",
        "## By package",
        "",
    ]
    for r in out["packages"]:
        s = r["model"]
        lines += [f"### {r['title']}", "", f"Items: {r['verification']['kept']} kept, {r['verification']['rejected']} removed.", "",
                  "| Fact | Expected | Model | Right |", "|---|---|---|:-:|"]
        for k in FACT_KEYS:
            f = s["facts"][k]
            got = f["got"] + (f" {f['got_time']}" if "got_time" in f else "")
            exp = f["expected"] + (f" {f['expected_time']}" if "expected_time" in f else "")
            ok = "yes" if f["correct"] and f.get("time_correct", True) else ("date only" if f["correct"] else "no")
            lines.append(f"| {LABELS[k]} | {exp} | {got[:90]} | {ok} |")
        missed = [c["text"] for c in s["checklist"] if not c["found"]]
        lines += ["", f"Checklist coverage {pct(s['checklist_found'], s['checklist_total'])}; factors {pct(s['factors_found'], s['factors_total'])}."]
        if missed:
            lines += ["Missed: " + "; ".join(missed) + "."]
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
