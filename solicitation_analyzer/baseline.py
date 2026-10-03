"""A keyword baseline with no model, for comparison.

It answers the same questions with regular expressions, so the evaluation can
show what the model adds over the obvious approach instead of claiming it.
"""
from __future__ import annotations

import re

from . import dates
from .pdf import Page

OBLIGATION = re.compile(r"\b(shall|must|required|will not be (accepted|considered)|no later than|is due|are due)\b", re.I)
DUE = re.compile(r"\b(due|deadline|no later than|must be received|closing date|response date|submission deadline)\b", re.I)
RESPONSE = re.compile(r"\b(proposals?|quotes?|quotations?|responses?|offers?|submission|bids?|closing)\b", re.I)
SUBMIT = re.compile(r"\b(submit\w*|sent to|upload\w*|deliver\w*)\b", re.I)
CHANNEL = re.compile(r"(e-?mail|portal|dropbox|online form|@|upload)", re.I)
PAGE_LIMIT = re.compile(r"\b(\d+)\s+pages?\b", re.I)
LIMIT_WORD = re.compile(r"\b(limit\w*|not (to )?exceed|no more than|maximum)\b", re.I)
BASIS = re.compile(r"(best value|lowest price technically acceptable|\blpta\b|highest (aggregate|combined|total|overall)|lowest (evaluated )?price)", re.I)
SET_ASIDE = re.compile(r"\bset[- ]?aside\b", re.I)
NAICS = re.compile(r"naics[^0-9]{0,40}(\d{6})", re.I)
POINTS = re.compile(r"\(?(\d{1,3})\s*(points?|pts\.?|%)\)?", re.I)


def sentences(pages: list[Page]) -> list[tuple[int, str]]:
    out = []
    for page in pages:
        for block in re.split(r"\n\s*\n", page.text):
            text = re.sub(r"\s+", " ", block).strip()
            for sentence in re.split(r"(?<=[.;])\s+(?=[A-Z(])", text):
                if len(sentence) > 15:
                    out.append((page.number, sentence))
    return out


def _item(kind: str, page: int, text: str, document: str, **extra) -> dict:
    return {"kind": kind, "statement": text[:220], "quote": text[:400], "page": page, "document": document,
            "date": extra.get("date", ""), "time": extra.get("time", ""), "weight": extra.get("weight", ""),
            "superseded_by": None, "role": extra.get("role", "base")}


def run(documents: list[tuple[str, str, list[Page]]]) -> dict:
    """documents: (id, role, pages). Amendments are searched before the base for deadlines."""
    items: list[dict] = []
    facts: dict = {k: None for k in ["response_due", "questions_due", "submission_method", "page_limit", "basis_of_award", "set_aside", "naics"]}
    ordered = sorted(documents, key=lambda d: d[1] != "amendment")
    for doc_id, role, pages in ordered:
        for page, s in sentences(pages):
            found = dates.find_dates(s)
            when = {"date": found[0].isoformat() if found else "", "time": (dates.find_times(s) or [""])[0], "role": role}
            if found and re.search(r"\bquestions?\b", s, re.I) and DUE.search(s) and not facts["questions_due"]:
                facts["questions_due"] = _item("questions_due", page, s, doc_id, **when)
            elif found and DUE.search(s) and RESPONSE.search(s) and not facts["response_due"]:
                facts["response_due"] = _item("response_due", page, s, doc_id, **when)
            if SUBMIT.search(s) and CHANNEL.search(s) and not facts["submission_method"]:
                facts["submission_method"] = _item("submission_method", page, s, doc_id)
            if PAGE_LIMIT.search(s) and LIMIT_WORD.search(s) and not facts["page_limit"]:
                facts["page_limit"] = _item("page_limit", page, s, doc_id)
            if BASIS.search(s) and not facts["basis_of_award"]:
                facts["basis_of_award"] = _item("basis_of_award", page, s, doc_id)
            if SET_ASIDE.search(s) and not facts["set_aside"]:
                facts["set_aside"] = _item("set_aside", page, s, doc_id)
            if NAICS.search(s) and not facts["naics"]:
                facts["naics"] = _item("naics", page, s, doc_id)
            points = POINTS.search(s)
            if points and re.search(r"\b(evaluat|criteri|score|factor|points)\w*", s, re.I):
                items.append(_item("evaluation_factor", page, s, doc_id, weight=points.group(0)))
            elif OBLIGATION.search(s):
                items.append(_item("required_content", page, s, doc_id))
    facts["evaluation_factors"] = [i for i in items if i["kind"] == "evaluation_factor"]
    return {"key_facts": facts, "items": items + [f for k, f in facts.items() if f and k != "evaluation_factors"]}
