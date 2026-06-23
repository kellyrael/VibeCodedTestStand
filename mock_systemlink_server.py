#!/usr/bin/env python
"""Minimal HTTP server that captures SystemLink event POSTs and prints them.

Run this in one terminal, then run verify_systemlink_reporting.py in another.
"""
import json
import textwrap
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime


class EventHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body)
        except Exception:
            payload = {"raw": body.decode(errors="replace")}

        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        event_type = payload.get("event_type", "unknown")
        status = payload.get("status") or payload.get("state", "")
        label = payload.get("case_label") or payload.get("asset_id") or payload.get("run_id", "")[:8]

        print(f"  [{ts}] {self.path:<28} | {event_type:<22} | {status:<10} | {label}")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def log_message(self, fmt, *args):
        pass  # suppress default access log noise


def run(host="127.0.0.1", port=9876):
    server = HTTPServer((host, port), EventHandler)
    print(textwrap.dedent(f"""
    ┌─────────────────────────────────────────────────────────────┐
    │  Mock SystemLink server listening on http://{host}:{port}  │
    │  Press Ctrl-C to stop.                                      │
    └─────────────────────────────────────────────────────────────┘
    """))
    print(f"  {'Time':12} {'Path':<28} {'EventType':<22} {'Status':<10} Label/ID")
    print(f"  {'-'*12} {'-'*28} {'-'*22} {'-'*10} {'-'*36}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")


if __name__ == "__main__":
    run()

