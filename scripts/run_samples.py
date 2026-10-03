"""Analyze every package in samples/manifest.json and write the sample reports.

    python3 scripts/run_samples.py [--only af-tdl] [--provider local] [--model ...]

Reports go to reports/<package>/ with contact details redacted, because these
are published in the repository. Model replies are cached in runs/cache, so a
re-run after a pipeline change only pays for prompts that changed.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from solicitation_analyzer.analyze import Document, analyze  # noqa: E402
from solicitation_analyzer.llm import Cached, make_provider  # noqa: E402
from solicitation_analyzer.report import write_reports  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--provider", default="local")
    parser.add_argument("--model")
    parser.add_argument("--base-url")
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--out", default="reports", help="Folder for the reports; default reports/.")
    args = parser.parse_args()

    manifest = json.loads((ROOT / "samples/manifest.json").read_text())
    docs = {d["id"]: d for d in manifest["documents"]}
    provider = Cached(make_provider(args.provider, args.model, args.base_url), ROOT / "runs/cache")

    def doc(doc_id: str, role: str) -> Document:
        d = docs[doc_id]
        return Document(path=ROOT / "samples" / d["file"], id=doc_id, title=d["title"], role=role, short=d.get("short", ""))

    for pkg in manifest["packages"]:
        if args.only and pkg["id"] not in args.only:
            continue
        started = time.monotonic()
        package = [doc(pkg["base"], "base")] + [doc(a, "amendment") for a in pkg["amendments"]] + [doc(a, "attachment") for a in pkg["attachments"]]
        result = analyze(package, provider, pkg["title"], on_progress=lambda msg: print(f"  {msg}", flush=True), parallel=args.parallel)
        write_reports(result, ROOT / args.out / pkg["id"], redact_contacts=True)
        print(f"{pkg['id']}: {len(result.kept)} kept, {len(result.rejected)} rejected, {len(result.errors)} errors, {time.monotonic() - started:.0f}s", flush=True)
        for err in result.errors:
            print(f"  ! {err}", flush=True)
    print(f"cache: {provider.hits} hits, {provider.misses} model calls")


if __name__ == "__main__":
    main()
