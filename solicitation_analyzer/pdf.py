"""PDF text by page, via poppler's pdftotext.

pdftotext separates pages with a form feed, which keeps page numbers exact:
every citation in a report points at the page a reader will see in the PDF.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Page:
    number: int
    text: str  # layout mode: what the model reads, with tables and columns kept in place
    reading: str = ""  # reading order: multi-column pages come out one column at a time

    @property
    def searchable(self) -> str:
        """Both renderings, so a quote read across columns still verifies. The marker stops a match spanning the join."""
        return f"{self.text}\nzzrenderingbreakzz\n{self.reading}" if self.reading else self.text


class PdfError(RuntimeError):
    pass


def _pdftotext(path: str | Path, *flags: str) -> str:
    result = subprocess.run(["pdftotext", *flags, "-enc", "UTF-8", str(path), "-"], capture_output=True)
    if result.returncode != 0:
        raise PdfError(f"pdftotext could not read {path}: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout.decode("utf-8", errors="replace")


def extract_pages(path: str | Path) -> list[Page]:
    if not shutil.which("pdftotext"):
        raise PdfError("pdftotext was not found. Install poppler (macOS: brew install poppler).")
    layout = split_pages(_pdftotext(path, "-layout"))
    reading = split_pages(_pdftotext(path))
    if len(reading) != len(layout):
        return layout
    return [Page(p.number, p.text, r.text) for p, r in zip(layout, reading)]


def split_pages(text: str) -> list[Page]:
    parts = text.split("\f")
    if parts and not parts[-1].strip():
        parts = parts[:-1]
    return [Page(i + 1, part) for i, part in enumerate(parts)]


def blank_pages(pages: list[Page], min_chars: int = 40) -> list[int]:
    """Pages with almost no text layer, usually scans. They need OCR first."""
    return [p.number for p in pages if len(p.text.strip()) < min_chars]
