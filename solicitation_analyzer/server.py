"""A small local web interface: drop in a solicitation, get the checklist.

It binds to 127.0.0.1 only. Uploaded PDFs and reports stay in runs/uploads on
this machine, and with the default local model nothing leaves it at all.
"""
from __future__ import annotations

import base64
import json
import re
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .analyze import Document, analyze
from .llm import Provider
from .report import write_reports

UPLOADS = Path("runs/uploads")
MAX_BYTES = 60 * 1024 * 1024
ROLES = {"base", "amendment", "attachment"}

PAGE = (Path(__file__).parent / "static" / "index.html")


class Jobs:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.jobs: dict[str, dict] = {}

    def update(self, job_id: str, **fields) -> None:
        with self.lock:
            self.jobs.setdefault(job_id, {}).update(fields)

    def get(self, job_id: str) -> dict | None:
        with self.lock:
            job = self.jobs.get(job_id)
            return dict(job) if job else None


def _safe_name(name: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(name).stem).strip("-.")[:60] or "document"
    return f"{stem}.pdf"


def make_handler(provider: Provider, jobs: Jobs, redact_contacts: bool, parallel: int):
    def work(job_id: str, docs: list[Document], title: str) -> None:
        try:
            result = analyze(docs, provider, title or None, on_progress=lambda msg: jobs.update(job_id, progress=msg), parallel=parallel)
            write_reports(result, UPLOADS / job_id, redact_contacts=redact_contacts)
            jobs.update(job_id, status="done", progress=f"{len(result.kept)} items, {len(result.rejected)} removed", report=f"/jobs/{job_id}/report.html")
        except Exception as err:  # reported to the page rather than lost in a thread
            jobs.update(job_id, status="failed", error=str(err))

    class Handler(BaseHTTPRequestHandler):
        server_version = "SolicitationAnalyzer/0.1"

        def log_message(self, fmt: str, *args) -> None:
            pass

        def _send(self, code: int, body: bytes, content_type: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, data: dict) -> None:
            self._send(code, json.dumps(data).encode(), "application/json")

        def do_GET(self) -> None:
            if self.path in ("/", "/index.html"):
                return self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            if self.path == "/api/info":
                local = provider.name != "anthropic"
                return self._json(200, {"model": provider.model, "provider": provider.name, "local": local})
            m = re.fullmatch(r"/api/jobs/([0-9a-f]{32})", self.path)
            if m:
                job = jobs.get(m.group(1))
                return self._json(200, job) if job else self._json(404, {"error": "No such job"})
            m = re.fullmatch(r"/jobs/([0-9a-f]{32})/(report\.(?:html|md|json))", self.path)
            if m and (UPLOADS / m.group(1) / m.group(2)).exists():
                types = {"html": "text/html; charset=utf-8", "md": "text/markdown; charset=utf-8", "json": "application/json"}
                return self._send(200, (UPLOADS / m.group(1) / m.group(2)).read_bytes(), types[m.group(2).rsplit(".", 1)[1]])
            self._json(404, {"error": "Not found"})

        def do_POST(self) -> None:
            if self.path != "/api/jobs":
                return self._json(404, {"error": "Not found"})
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0 or length > MAX_BYTES * 1.4:
                return self._json(413, {"error": "Upload is empty or larger than 60 MB."})
            try:
                body = json.loads(self.rfile.read(length))
                files = body["files"]
            except (ValueError, KeyError):
                return self._json(400, {"error": "Expected JSON with a files list."})
            if not files or sum(1 for f in files if f.get("role") == "base") != 1:
                return self._json(400, {"error": "Mark exactly one file as the solicitation."})
            job_id = uuid.uuid4().hex
            folder = UPLOADS / job_id
            folder.mkdir(parents=True)
            docs = []
            for f in sorted(files, key=lambda f: f.get("role") != "base"):
                data = base64.b64decode(f.get("data", ""))
                if not data.startswith(b"%PDF"):
                    return self._json(400, {"error": f"{f.get('name')} is not a PDF."})
                role = f.get("role") if f.get("role") in ROLES else "attachment"
                path = folder / _safe_name(f.get("name", "document.pdf"))
                path.write_bytes(data)
                name = Path(f.get("name", "document")).stem
                docs.append(Document(path=path, id=path.stem, title=name, role=role, short=name))
            jobs.update(job_id, status="running", progress="Reading the PDF")
            threading.Thread(target=work, args=(job_id, docs, str(body.get("title", "")).strip()), daemon=True).start()
            self._json(202, {"job": job_id})

    return Handler


def serve(provider: Provider, port: int = 8765, redact_contacts: bool = False, parallel: int = 1) -> None:
    jobs = Jobs()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(provider, jobs, redact_contacts, parallel))
    print(f"Solicitation Analyzer on http://127.0.0.1:{port}  (model: {provider.model}; Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
