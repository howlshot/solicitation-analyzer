"""The pipeline: extract, verify against the page, merge, apply amendments, summarize."""
from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import dates
from .extract import extract_items
from .llm import Provider
from .pdf import Page, blank_pages, extract_pages
from .schema import Item
from .textmatch import locate, similar

DEADLINE_KINDS = {"response_due", "questions_due", "conference"}


@dataclass
class Document:
    path: Path
    id: str
    title: str
    role: str = "base"  # base, amendment, attachment
    pages: list[Page] = field(default_factory=list)
    short: str = ""  # label for citations, e.g. "Addendum 2"


@dataclass
class Analysis:
    title: str
    documents: list[Document]
    items: list[Item]
    rejected: list[Item]
    errors: list[str]
    model: str
    provider: str
    seconds: float
    created: str

    @property
    def kept(self) -> list[Item]:
        return [i for i in self.items if not i.superseded_by]


def verify(items: list[Item], doc: Document) -> tuple[list[Item], list[Item]]:
    """Keep items whose quote is on the page; check dates and times against the quote."""
    page_text = {p.number: p.searchable for p in doc.pages}
    kept, rejected = [], []
    for item in items:
        match = locate(item.quote, page_text, item.cited_page)
        item.verification = match.status
        item.similarity = match.similarity
        if match.status == "missing":
            rejected.append(item)
            continue
        if match.page != item.cited_page and match.end_page != item.cited_page:
            item.warnings.append(f"Cited page {item.cited_page}; the quote is on page {match.page}.")
        item.page = match.page
        item.end_page = match.end_page
        if match.status == "assembled":
            item.warnings.append("The quoted words are all on this page, close together but in a different order, as happens with tables. Read the table to confirm.")
        check_dates(item)
        kept.append(item)
    return kept, rejected


def check_dates(item: Item) -> None:
    written = dates.find_dates(item.quote)
    claimed = dates.parse_iso(item.date)
    if item.date and not claimed:
        item.warnings.append(f"Unreadable date {item.date!r} removed.")
        item.date = ""
    elif claimed and claimed not in written:
        item.warnings.append(f"The quote does not contain the date {item.date}; check the page.")
    if item.kind in DEADLINE_KINDS and len(written) >= 2 and _adjacent_revision(item.quote):
        item.warnings.append("Two dates are written together, as amendments do when the old date is struck through. Confirm which one stands.")
    if item.time and item.time not in dates.find_times(item.quote):
        item.warnings.append(f"The quote does not contain the time {item.time}.")


def _adjacent_revision(quote: str) -> bool:
    return bool(dates.REVISED_NAMED.search(quote) or re.search(r"\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}/\d{1,2}/\d{2,4}", quote))


QUESTIONS = re.compile(r"\bquestions?\b", re.I)
RESPONSE_WORDS = re.compile(r"\b(proposals?|bids?|quotes?|quotations?|offers?|responses?|submissions?)\b", re.I)
CHANNEL_WORDS = re.compile(r"\b(e-?mail\w*|portal|dropbox|online form|upload\w*|electronic\w*|in person|mail(ed)?|hand[- ]deliver\w*)\b", re.I)
NOT_THE_RESPONSE = re.compile(r"\b(debrief\w*|protest\w*|questions?|invoic\w*|vendrep|vendor responsibility|reports?|disclosure|waiver|deficienc\w*)\b", re.I)


SET_ASIDE_WORDS = re.compile(r"\bset[- ]?aside\b|\bunrestricted\b", re.I)
NAICS_CODE = re.compile(r"\bnaics\b[^.]{0,40}?\b\d{6}\b", re.I)
GENERAL_KINDS = {"required_content", "work_requirement", "other_eligibility", "registration", "certification"}


def _text(item: Item) -> str:
    return f"{item.statement} {item.quote}"


def reclassify(items: list[Item]) -> None:
    """Fix the kinds a model most often confuses, using the item's own words.

    A "response due" that is about questions is the questions deadline, and one
    with no date at all is some other deadline (late-proposal rules, post-award reports).
    """
    for item in items:
        q, r = QUESTIONS.search(item.statement), RESPONSE_WORDS.search(item.statement)
        if item.kind == "response_due" and q and (not r or q.start() < r.start()):
            item.kind = "questions_due"
        if item.kind in ("response_due", "questions_due") and not item.date:
            item.kind = "other_deadline"
        # Set-aside and NAICS lines often land in a general bucket; their wording is unambiguous.
        if item.kind in GENERAL_KINDS and NAICS_CODE.search(item.statement):
            item.kind = "naics"
        elif item.kind in GENERAL_KINDS and SET_ASIDE_WORDS.search(item.statement):
            item.kind = "set_aside"
        # A participation goal is a contract requirement, not a scored factor.
        if item.kind == "evaluation_factor" and re.search(r"\bgoals?\b", item.statement, re.I):
            item.kind = "participation_goal"


def merge(items: list[Item]) -> list[Item]:
    """One item per fact. Repeats fold into the first occurrence.

    Amendments are read first, so when an amendment restates the solicitation
    the amendment's wording and page are the ones kept.
    """
    out: list[Item] = []
    for item in sorted(items, key=lambda i: (i.role != "amendment", i.role == "attachment", i.document, i.page or 0)):
        twin = next((o for o in out if o.kind == item.kind and _same(o, item)), None)
        if twin:
            if twin.document == item.document and item.page and item.page != twin.page and item.page not in twin.also_on:
                twin.also_on.append(item.page)
            continue
        out.append(item)
    return out


def _same(a: Item, b: Item) -> bool:
    if a.date and b.date and a.date != b.date:
        return False
    if a.weight and b.weight and a.weight != b.weight:
        return False
    # Similar checklist lines alone are not enough: "Include the SAM UEI" and
    # "Include the GSA number" read alike but are different obligations.
    quotes = similar(a.quote, b.quote)
    return quotes > 0.8 or (quotes > 0.5 and similar(a.statement, b.statement) > 0.9)


def apply_amendments(items: list[Item]) -> None:
    """A deadline restated in an amendment replaces the base document's version."""
    for kind in DEADLINE_KINDS:
        amended = [i for i in items if i.kind == kind and i.role == "amendment" and i.date]
        if not amended:
            continue
        latest = max(amended, key=lambda i: i.date)
        for item in items:
            if item.kind == kind and item.role == "base" and item.date and item.date != latest.date:
                item.superseded_by = latest.document


def analyze(
    documents: list[Document],
    provider: Provider,
    title: str | None = None,
    on_progress: Callable[[str], None] | None = None,
    parallel: int = 1,
) -> Analysis:
    started = time.monotonic()
    items: list[Item] = []
    rejected: list[Item] = []
    errors: list[str] = []
    for doc in documents:
        doc.pages = extract_pages(doc.path)
        scans = blank_pages(doc.pages)
        if scans:
            errors.append(f"{doc.id}: pages {scans} have no text layer and were skipped (scanned images need OCR first).")

        def progress(done: int, total: int, doc: Document = doc) -> None:
            if on_progress:
                on_progress(f"{doc.title}: {done} of {total} parts read")

        raw, errs = extract_items(provider, doc.pages, doc.id, doc.title, doc.role, progress, parallel=parallel)
        errors.extend(f"{doc.id}: {e}" for e in errs)
        kept, bad = verify(raw, doc)
        items.extend(kept)
        rejected.extend(bad)
    reclassify(items)
    items = merge(items)
    apply_amendments(items)
    return Analysis(
        title=title or documents[0].title,
        documents=documents,
        items=items,
        rejected=rejected,
        errors=errors,
        model=provider.model,
        provider=provider.name,
        seconds=round(time.monotonic() - started, 1),
        created=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def key_facts(analysis: Analysis) -> dict:
    """The fields a bid/no-bid decision starts from, taken from verified items only."""
    live = analysis.kept

    def first(kind: str, prefer_latest_date: bool = False) -> Item | None:
        found = [i for i in live if i.kind == kind]
        if prefer_latest_date:
            dated = [i for i in found if i.date]
            if dated:
                # An amendment's date wins; otherwise the date the most items agree on.
                amended = [i for i in dated if i.role == "amendment"]
                if amended:
                    return max(amended, key=lambda i: i.date)
                counts: dict[str, int] = {}
                for i in dated:
                    counts[i.date] = counts.get(i.date, 0) + 1
                best = max(counts, key=lambda d: (counts[d], d))
                return next(i for i in dated if i.date == best)
        return found[0] if found else None

    def submission_rank(item: Item) -> int:
        text = _text(item)
        score = 2 * bool(CHANNEL_WORDS.search(text)) + 2 * bool(RESPONSE_WORDS.search(text)) + (item.kind == "submission_method")
        return score - 4 * bool(NOT_THE_RESPONSE.search(item.statement))

    def award_rank(item: Item) -> int:
        text = _text(item).lower()
        return 2 * ("award" in text) + bool(re.search(r"best value|lowest price|technically acceptable|lpta|highest", text))

    def best(candidates: list[Item], rank, floor: int) -> Item | None:
        ranked = [(rank(i), -n, i) for n, i in enumerate(candidates)]
        ranked = [r for r in ranked if r[0] >= floor]
        return max(ranked, key=lambda r: r[:2])[2] if ranked else None

    return {
        "response_due": first("response_due", True),
        "questions_due": first("questions_due", True),
        "submission_method": best([i for i in live if i.kind in ("submission_method", "response_due")], submission_rank, 3),
        "page_limit": first("page_limit"),
        "basis_of_award": best([i for i in live if i.kind == "basis_of_award"], award_rank, 0),
        "set_aside": first("set_aside"),
        "naics": first("naics"),
        "evaluation_factors": [i for i in live if i.kind == "evaluation_factor"],
    }
