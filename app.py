#!/usr/bin/env python3
"""Простое API: health, выделение памяти, нагрузка CPU."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from multiprocessing import Process
from urllib.parse import parse_qs, urlparse

HOST = "0.0.0.0"
PORT = 8080

# Куски памяти, которые нельзя отдавать сборщику мусора.
held_memory: list[bytearray] = []
burner: Process | None = None


def burn_cpu() -> None:
    n = 0
    while True:
        n += 1


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _send(self, code: int, body: str) -> None:
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            self._send(200, "ok")
            return

        if path == "/eat":
            query = parse_qs(parsed.query)
            try:
                mb = int(query.get("mb", ["0"])[0])
            except ValueError:
                self._send(400, "mb must be an integer")
                return
            if mb < 0:
                self._send(400, "mb must be >= 0")
                return

            held_memory.append(bytearray(mb * 1024 * 1024))
            total = sum(len(chunk) for chunk in held_memory) // (1024 * 1024)
            self._send(200, f"allocated {mb} MB, holding {total} MB")
            return

        if path == "/burn":
            global burner
            if burner is None or not burner.is_alive():
                burner = Process(target=burn_cpu, daemon=True)
                burner.start()
                self._send(200, "burning one CPU core")
            else:
                self._send(200, "already burning one CPU core")
            return

        self._send(404, "not found")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
