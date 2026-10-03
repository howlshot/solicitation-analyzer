"""Command line.

    python -m solicitation_analyzer analyze RFP.pdf [--amendment A1.pdf] [--attachment SOW.pdf] --out reports/rfp
    python -m solicitation_analyzer serve
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .analyze import Document, analyze
from .llm import Cached, make_provider
from .report import write_reports


def _doc(path: str, role: str, title: str | None = None) -> Document:
    p = Path(path)
    name = p.stem.replace("-", " ").replace("_", " ")
    return Document(path=p, id=p.stem, title=title or name, role=role, short=name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="solicitation_analyzer", description="Turn a solicitation PDF into a cited compliance checklist.")
    sub = parser.add_subparsers(dest="command", required=True)

    a = sub.add_parser("analyze", help="Analyze one solicitation and its amendments and attachments.")
    a.add_argument("pdf", help="The solicitation PDF.")
    a.add_argument("--amendment", action="append", default=[], help="An amendment or addendum PDF. Repeatable.")
    a.add_argument("--attachment", action="append", default=[], help="An attachment PDF, such as a statement of work. Repeatable.")
    a.add_argument("--title", help="Title for the report.")
    a.add_argument("--out", required=True, help="Output directory for report.json, report.md and report.html.")
    _model_args(a)

    s = sub.add_parser("serve", help="Run the local web interface.")
    s.add_argument("--port", type=int, default=8765)
    _model_args(s)

    args = parser.parse_args(argv)
    provider = Cached(make_provider(args.provider, args.model, args.base_url), args.cache)

    if args.command == "serve":
        from .server import serve

        serve(provider, args.port, redact_contacts=args.redact_contacts, parallel=args.parallel)
        return 0

    docs = [_doc(args.pdf, "base", args.title)]
    docs += [_doc(p, "amendment") for p in args.amendment]
    docs += [_doc(p, "attachment") for p in args.attachment]
    result = analyze(docs, provider, args.title, on_progress=lambda msg: print(f"  {msg}", file=sys.stderr), parallel=args.parallel)
    paths = write_reports(result, Path(args.out), redact_contacts=args.redact_contacts)
    print(f"{len(result.kept)} items kept, {len(result.rejected)} rejected, {result.seconds}s. Wrote {', '.join(str(p) for p in paths)}")
    for err in result.errors:
        print(f"  warning: {err}", file=sys.stderr)
    return 0


def _model_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--provider", default="local", choices=["local", "anthropic"], help="local: any OpenAI-compatible server (default LM Studio). anthropic: needs ANTHROPIC_API_KEY.")
    p.add_argument("--model", help="Model id. Default qwen3.8-27b-mlx locally, claude-sonnet-5-5 on Anthropic.")
    p.add_argument("--base-url", help="Server URL for the local provider. Default http://localhost:1234/v1.")
    p.add_argument("--cache", default="runs/cache", help="Directory for cached model replies.")
    p.add_argument("--redact-contacts", action="store_true", help="Replace names, emails and phone numbers in the report.")
    p.add_argument("--parallel", type=int, default=1, help="Model requests to send at once. LM Studio serves up to 4.")


if __name__ == "__main__":
    raise SystemExit(main())
