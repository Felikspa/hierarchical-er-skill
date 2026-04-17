from __future__ import annotations

import argparse
import json
import threading
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from capture_error_case import evaluate_capture, persist_case
from common import (
    ERROR_CASES_DIR,
    GRAPH_PATH,
    RUNS_DIR,
    SKILL_ROOT,
    active_entities,
    active_relations,
    calculate_review_summary,
    clone_run,
    find_run_path,
    load_json,
    list_base_run_paths,
    now_iso,
    summary_for_run,
    write_json,
    write_run,
)

WEB_ROOT = SKILL_ROOT / "webapp"


def build_state() -> dict:
    run_paths = list_base_run_paths()
    runs = [load_json(path) for path in run_paths]
    case_summaries = []
    for path in sorted(ERROR_CASES_DIR.glob("*.json"), reverse=True):
        payload = load_json(path)
        case_summaries.append(
            {
                "case_id": payload["case_id"],
                "run_id": payload["run_id"],
                "captured_at": payload["captured_at"],
                "reasons": payload["reasons"],
            }
        )

    return {
        "latest_run_id": runs[0]["run_id"] if runs else None,
        "runs": [summary_for_run(run) for run in runs],
        "graph_memory": load_json(GRAPH_PATH),
        "error_cases": case_summaries,
    }


def build_run_payload(run_id: str) -> dict:
    run_path = find_run_path(run_id)
    run = load_json(run_path)
    reviewed = None
    reviewed_path = run["review_status"]["revised_run_path"]
    if reviewed_path:
        reviewed = load_json(SKILL_ROOT / reviewed_path)
    return {
        "run": run,
        "reviewed_run": reviewed,
        "graph_memory": load_json(GRAPH_PATH),
    }


class ReviewHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def _send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/state.json":
            self._send_json(build_state())
            return
        if parsed.path == "/api/run.json":
            run_id = parse_qs(parsed.query).get("run_id", [None])[0]
            if run_id is None:
                self._send_json({"error": "missing run_id"}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json(build_run_payload(run_id))
            return
        if parsed.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/review":
            self._send_json({"error": "unknown endpoint"}, HTTPStatus.NOT_FOUND)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        payload = json.loads(body.decode("utf-8"))

        run_path = find_run_path(payload["run_id"])
        base_run = load_json(run_path)
        reviewed_run = clone_run(base_run)
        mode = payload["mode"]
        if mode == "coarse":
            reviewed_run["entities_coarse"] = payload["entities"]
            reviewed_run["relations_coarse"] = payload["relations"]
        elif mode in {"standard", "fine"}:
            reviewed_run["entities_fine"] = payload["entities"]
            reviewed_run["relations_fine"] = payload["relations"]
        else:
            self._send_json({"error": "unsupported mode"}, HTTPStatus.BAD_REQUEST)
            return

        review_summary = calculate_review_summary(base_run, reviewed_run)
        review_path = RUNS_DIR / f"{payload['run_id']}.review.json"
        relative_review_path = str(review_path.relative_to(SKILL_ROOT))

        reviewed_run["review_note"] = payload.get("review_note", "")
        reviewed_run["review_status"] = {
            "status": "reviewed",
            "substantive_edits": review_summary["substantive_edits"],
            "edit_ratio": review_summary["edit_ratio"],
            "revised_run_path": relative_review_path,
            "last_reviewed_at": now_iso(),
        }

        capture_payload, case_payload = evaluate_capture(base_run, reviewed_run)
        reviewed_run["error_capture"] = capture_payload
        write_json(review_path, reviewed_run)

        base_run["review_status"] = reviewed_run["review_status"]
        base_run["error_capture"] = capture_payload
        write_run(run_path, base_run)

        if case_payload is not None:
            persist_case(case_payload)

        self._send_json(
            {
                "saved": True,
                "review_status": reviewed_run["review_status"],
                "error_capture": capture_payload,
            }
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the hierarchical ER review app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--build-state", action="store_true")
    args = parser.parse_args()

    if args.build_state:
        print(json.dumps(build_state(), ensure_ascii=False, indent=2))
        return 0

    server = ThreadingHTTPServer((args.host, args.port), ReviewHandler)
    url = f"http://{args.host}:{args.port}/"

    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    print(f"serving review app at {url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
