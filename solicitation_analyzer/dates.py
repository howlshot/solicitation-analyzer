"""Dates and times as solicitations write them.

Used to check a model's normalized date against the words it quoted, and to
spot the struck-through revisions amendments use ("August 7 13, 2026"), which
lose their strikethrough when the PDF becomes text.
"""
from __future__ import annotations

import re
from datetime import date

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
MONTH = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sept?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?"

# "August 7 13, 2026": two day numbers before one year. The first is usually struck through.
REVISED_NAMED = re.compile(MONTH + r"\s+(\d{1,2})(?:st|nd|rd|th)?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})", re.I)
NAMED = re.compile(MONTH + r"\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})", re.I)
DAY_FIRST = re.compile(r"\b(\d{1,2})\s+" + MONTH + r",?\s+(\d{4})", re.I)
NUMERIC = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})\b")
ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")

TIME = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*(a\.?\s?m\.?|p\.?\s?m\.?)(?![a-z])", re.I)
TIME_24 = re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)\b(?!\s*(?:a\.?m|p\.?m))", re.I)
NOON = re.compile(r"\bnoon\b", re.I)
# Federal forms write "1700 CD" or "1400 hrs".
MILITARY = re.compile(r"\b([01]\d|2[0-3])([0-5]\d)\s*(?:hrs\b|hours\b|[ECMP][SD]?T?\b)")


def _make(y: int, m: int, d: int) -> date | None:
    if y < 100:
        y += 2000
    try:
        return date(y, m, d)
    except ValueError:
        return None


def find_dates(text: str) -> list[date]:
    """Every calendar date written in the text, in reading order, without repeats."""
    found: list[tuple[int, date]] = []
    taken: list[range] = []

    def add(pos: int, span: tuple[int, int], value: date | None) -> None:
        if value and not any(pos in r for r in taken):
            found.append((pos, value))
            taken.append(range(*span))

    for m in REVISED_NAMED.finditer(text):
        month = MONTHS[m.group(1)[:3].lower()]
        add(m.start(), m.span(), _make(int(m.group(4)), month, int(m.group(2))))
        found.append((m.start() + 1, _make(int(m.group(4)), month, int(m.group(3)))))
    for m in NAMED.finditer(text):
        add(m.start(), m.span(), _make(int(m.group(3)), MONTHS[m.group(1)[:3].lower()], int(m.group(2))))
    for m in DAY_FIRST.finditer(text):
        add(m.start(), m.span(), _make(int(m.group(3)), MONTHS[m.group(2)[:3].lower()], int(m.group(1))))
    for m in NUMERIC.finditer(text):
        add(m.start(), m.span(), _make(int(m.group(3)), int(m.group(1)), int(m.group(2))))
    for m in ISO.finditer(text):
        add(m.start(), m.span(), _make(int(m.group(1)), int(m.group(2)), int(m.group(3))))
    out: list[date] = []
    for _, value in sorted((f for f in found if f[1]), key=lambda f: f[0]):
        if value not in out:
            out.append(value)
    return out


def find_times(text: str) -> list[str]:
    """Clock times as 24-hour HH:MM."""
    out: list[str] = []
    for m in TIME.finditer(text):
        hour, minute = int(m.group(1)), int(m.group(2) or 0)
        if not 1 <= hour <= 12:
            continue
        pm = m.group(3).lower().startswith("p")
        hour = (hour % 12) + (12 if pm else 0)
        out.append(f"{hour:02d}:{minute:02d}")
    for m in TIME_24.finditer(text):
        out.append(f"{int(m.group(1)):02d}:{m.group(2)}")
    for m in MILITARY.finditer(text):
        out.append(f"{m.group(1)}:{m.group(2)}")
    if NOON.search(text):
        out.append("12:00")
    return list(dict.fromkeys(out))


def parse_iso(value: str) -> date | None:
    m = ISO.fullmatch(value.strip()) if value else None
    return _make(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None
