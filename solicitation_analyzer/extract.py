"""Model extraction: pages go in with page markers, checklist items come out."""
from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from .llm import ModelError, Provider, TooLong
from .pdf import Page
from .schema import ITEM_SCHEMA, KINDS, Item

SYSTEM_PROMPT = """You read government solicitations (RFPs, RFQs, RFIs, statements of work and amendments) and pull out what a company must know and do to respond. Work only from the text you are given.

Return JSON matching the schema. Each item is one fact or one obligation.

Rules:
1. quote: copy 8 to 35 consecutive words exactly as they appear in the text, including numbers and punctuation. Never reword, shorten or fix anything inside quote.
2. page: the number from the <<<PAGE n>>> marker above the quoted words.
3. statement: one short plain-English checklist line, at most 25 words.
4. date: YYYY-MM-DD and time: 24-hour HH:MM, only when they are written in the quote. Otherwise use empty strings.
5. weight: the points or percentage an evaluation factor is worth, as written ("40%", "30 points"). Otherwise an empty string.
6. kind:
   - response_due: when proposals, quotes or RFI responses are due. questions_due: the last day to submit questions.
   - submission_method: where and how to send the response (email address, portal, upload link, mail), and channels that are refused.
   - submission_contents: forms, copies, volumes or separate files to send with the response.
   - page_limit: any page or length limit. formatting: file type, font, margins, file naming, email subject line.
   - evaluation_factor: each scored criterion. basis_of_award: how the winner is chosen (best value, lowest price technically acceptable).
   - required_content: what the response itself must say or contain. work_requirement: work the contractor must perform after award.
7. Extract: deadlines, how and where to submit, page limits and formatting rules, eligibility (set-asides, NAICS codes, required registrations, certifications, insurance, M/WBE or SDVOB participation goals), evaluation factors and the basis of award, required response content, and the main work requirements.
8. Skip background, definitions, tables of contents, and standard contract clauses that ask nothing of the company when it responds.
9. Extract each fact once. If nothing in the text qualifies, return an empty list."""


@dataclass
class Chunk:
    pages: list[int]
    text: str


def chunk_pages(pages: list[Page], max_chars: int = 9000) -> list[Chunk]:
    """Group whole pages under a size budget. A page is never split from its marker."""
    chunks: list[Chunk] = []
    current: list[Page] = []
    size = 0
    for page in pages:
        body = page.text.strip()
        if not body:
            continue
        block = len(body) + 20
        if current and size + block > max_chars:
            chunks.append(_join(current))
            current, size = [], 0
        current.append(page)
        size += block
    if current:
        chunks.append(_join(current))
    return chunks


def _join(pages: list[Page]) -> Chunk:
    return Chunk([p.number for p in pages], "\n\n".join(f"<<<PAGE {p.number}>>>\n{p.text.strip()}" for p in pages))


def extract_items(
    provider: Provider,
    pages: list[Page],
    document: str,
    title: str,
    role: str = "base",
    on_progress: Callable[[int, int], None] | None = None,
    max_tokens: int = 4000,
    parallel: int = 1,
) -> tuple[list[Item], list[str]]:
    """Run every chunk through the model. Returns the raw items and any chunk-level errors.

    parallel > 1 sends that many chunks at once, for servers that batch requests
    (LM Studio and llama-server both can). Results keep document order either way.
    """
    chunks = chunk_pages(pages)
    done = 0

    by_number = {p.number: p for p in pages}

    def ask(chunk: Chunk, budget: int) -> list[Item]:
        user = f"Document: {title}\nPages {chunk.pages[0]} to {chunk.pages[-1]}\n\n{chunk.text}"
        result = provider.complete_json(SYSTEM_PROMPT, user, ITEM_SCHEMA, budget)
        return [i for i in (to_item(raw, document, role) for raw in result.get("items", [])) if i]

    def run(chunk: Chunk) -> tuple[list[Item], str | None]:
        nonlocal done
        found, error = [], None
        try:
            found = ask(chunk, max_tokens)
        except TooLong:
            # Dense pages (price tables, clause lists) can overflow the reply.
            # Retry one page at a time with twice the room before giving up.
            for number in chunk.pages:
                try:
                    found += ask(_join([by_number[number]]), max_tokens * 2)
                except ModelError as err:
                    error = f"page {number}: {err}"
        except ModelError as err:
            error = f"pages {chunk.pages[0]}-{chunk.pages[-1]}: {err}"
        done += 1
        if on_progress:
            on_progress(done, len(chunks))
        return found, error

    if on_progress:
        on_progress(0, len(chunks))
    with ThreadPoolExecutor(max_workers=max(1, parallel)) as pool:
        results = list(pool.map(run, chunks))
    items = [i for found, _ in results for i in found]
    errors = [e for _, e in results if e]
    return items, errors


def to_item(raw: dict, document: str, role: str) -> Item | None:
    kind = raw.get("kind")
    quote = str(raw.get("quote", "")).strip()
    if kind not in KINDS or not quote:
        return None
    page = raw.get("page")
    return Item(
        kind=kind,
        statement=str(raw.get("statement", "")).strip(),
        quote=quote,
        page=page if isinstance(page, int) else None,
        cited_page=page if isinstance(page, int) else None,
        document=document,
        role=role,
        date=str(raw.get("date", "")).strip(),
        time=str(raw.get("time", "")).strip(),
        weight=str(raw.get("weight", "")).strip(),
    )
