"""Download the public test-set PDFs listed in samples/manifest.json.

    python3 scripts/fetch_samples.py

Files land in samples/ (git-ignored). A file already present is skipped, and
each file's SHA-256 is recorded in samples/checksums.json so a re-fetch that
returns a different document is visible.
"""
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"


def main() -> None:
    manifest = json.loads((SAMPLES / "manifest.json").read_text())
    sums_path = SAMPLES / "checksums.json"
    sums = json.loads(sums_path.read_text()) if sums_path.exists() else {}
    for doc in manifest["documents"]:
        target = SAMPLES / doc["file"]
        if not target.exists():
            # curl, not urllib: some state sites send an incomplete certificate
            # chain that curl completes from the system store and Python rejects.
            data = subprocess.run(
                ["curl", "-fsSL", "--max-time", "60", "-A", "solicitation-analyzer (public test set)", doc["url"]],
                check=True, capture_output=True,
            ).stdout
            if not data.startswith(b"%PDF"):
                raise SystemExit(f"{doc['id']}: response is not a PDF")
            target.write_bytes(data)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if doc["id"] in sums and sums[doc["id"]] != digest:
            print(f"{doc['id']}: checksum changed since the last fetch")
        sums[doc["id"]] = digest
        print(f"{doc['id']:24} {target.stat().st_size // 1024:>5} KB")
    sums_path.write_text(json.dumps(sums, indent=2) + "\n")


if __name__ == "__main__":
    main()
