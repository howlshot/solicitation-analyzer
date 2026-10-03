"""Scores a report against hand-written reference answers (eval/gold/*.json).

Three measures, each simple enough to check by hand:
- key facts: due dates and times exact; other facts by an accepted phrase; a fact
  the document does not state is right only when the report also leaves it out.
- evaluation factors: share of reference factors found, with the weight when one is stated.
- checklist: share of reference must-do items that some report item covers.
"""
from __future__ import annotations

FACT_KEYS = ["response_due", "questions_due", "submission_method", "page_limit", "basis_of_award", "set_aside", "naics"]


def _text(item: dict | None) -> str:
    return f"{item['statement']} {item['quote']}".lower() if item else ""


def score_fact(gold: dict | None, pred: dict | None) -> dict:
    if gold is None:
        return {"correct": pred is None, "expected": "not stated", "got": pred["statement"] if pred else "not stated"}
    if pred is None:
        return {"correct": False, "expected": gold.get("date") or "/".join(gold.get("any", [])), "got": "not found"}
    if "date" in gold:
        ok = pred.get("date") == gold["date"]
        result = {"correct": ok, "expected": gold["date"], "got": pred.get("date") or "no date"}
        if gold.get("time"):
            result["time_correct"] = pred.get("time") == gold["time"]
            result["expected_time"] = gold["time"]
            result["got_time"] = pred.get("time") or "no time"
        return result
    text = _text(pred)
    return {"correct": any(alt in text for alt in gold["any"]), "expected": " | ".join(gold["any"]), "got": pred["statement"]}


def covers(item: dict, groups: list[list[str]]) -> bool:
    text = _text(item)
    return all(any(alt in text for alt in group) for group in groups)


def score(gold: dict, report: dict) -> dict:
    facts = report["key_facts"]
    live = [i for i in report["items"] if not i.get("superseded_by")]
    fact_scores = {k: score_fact(gold["facts"].get(k), facts.get(k)) for k in FACT_KEYS}

    factors = facts.get("evaluation_factors") or []
    factor_hits = []
    for f in gold["evaluation_factors"]:
        hit = any(
            any(n in _text(p) for n in f["name"]) and (f["weight"] is None or f["weight"] in f"{p.get('weight', '')} {_text(p)}")
            for p in factors
        )
        factor_hits.append({"name": f["name"][0], "weight": f["weight"], "found": hit})

    checklist = [{"id": c["id"], "text": c["text"], "found": any(covers(i, c["all"]) for i in live)} for c in gold["checklist"]]
    times = [s for s in fact_scores.values() if "time_correct" in s]
    return {
        "facts": fact_scores,
        "facts_correct": sum(s["correct"] for s in fact_scores.values()),
        "facts_total": len(fact_scores),
        "times_correct": sum(s["time_correct"] for s in times),
        "times_total": len(times),
        "factors": factor_hits,
        "factors_found": sum(f["found"] for f in factor_hits),
        "factors_total": len(factor_hits),
        "checklist": checklist,
        "checklist_found": sum(c["found"] for c in checklist),
        "checklist_total": len(checklist),
        "items": len(live),
    }
