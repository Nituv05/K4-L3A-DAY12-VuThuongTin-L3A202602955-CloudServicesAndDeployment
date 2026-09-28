"""Small standard-library gateway for scaling local Compose agents."""

from __future__ import annotations

import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

UPSTREAM_HOST = os.getenv("PROXY_UPSTREAM_HOST", "agent")
UPSTREAM_PORT = os.getenv("PROXY_UPSTREAM_PORT", "8000")
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = int(os.getenv("PORT", "8000"))
UPSTREAM_TIMEOUT_SECONDS = 75

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


class ProxyHandler(BaseHTTPRequestHandler):
    def _forward(self) -> None:
        try:
            body_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400, "invalid Content-Length")
            return

        body = self.rfile.read(body_length) if body_length else None
        connection_tokens = {
            token.strip().lower()
            for token in self.headers.get("Connection", "").split(",")
            if token.strip()
        }
        excluded_headers = HOP_BY_HOP_HEADERS | connection_tokens | {"host", "content-length"}
        request_headers = {
            name: value
            for name, value in self.headers.items()
            if name.lower() not in excluded_headers
        }
        peer = self.client_address[0]
        previous_forwarded_for = self.headers.get("X-Forwarded-For")
        request_headers["X-Forwarded-For"] = (
            f"{previous_forwarded_for}, {peer}" if previous_forwarded_for else peer
        )

        target = f"http://{UPSTREAM_HOST}:{UPSTREAM_PORT}{self.path}"
        upstream_request = Request(
            target,
            data=body,
            headers=request_headers,
            method=self.command,
        )

        try:
            with urlopen(upstream_request, timeout=UPSTREAM_TIMEOUT_SECONDS) as response:
                status = response.status
                response_headers = response.headers.items()
                response_body = response.read()
        except HTTPError as response:
            status = response.code
            response_headers = response.headers.items()
            response_body = response.read()
        except (URLError, TimeoutError, OSError) as error:
            self.send_error(502, f"agent upstream unavailable: {error.reason if isinstance(error, URLError) else error}")
            return

        self.send_response(status)
        for name, value in response_headers:
            if name.lower() not in HOP_BY_HOP_HEADERS | {"content-length"}:
                self.send_header(name, value)
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        if self.command != "HEAD" and response_body:
            self.wfile.write(response_body)

    do_GET = _forward
    do_HEAD = _forward
    do_POST = _forward
    do_PUT = _forward
    do_PATCH = _forward
    do_DELETE = _forward
    do_OPTIONS = _forward

    def log_message(self, format_string: str, *args) -> None:
        print(f"gateway {self.address_string()} - {format_string % args}", file=sys.stderr, flush=True)


def main() -> None:
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), ProxyHandler)
    server.daemon_threads = True
    print(
        f"local gateway listening on {LISTEN_HOST}:{LISTEN_PORT}, "
        f"upstream={UPSTREAM_HOST}:{UPSTREAM_PORT}",
        flush=True,
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
