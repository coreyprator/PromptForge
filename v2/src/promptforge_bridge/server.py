from __future__ import annotations
import json, http.server, socketserver, urllib.parse
from promptforge_core.builder import build_prompt
from promptforge_core.validator import validate_files_payload, ValidationError

class Handler(http.server.BaseHTTPRequestHandler):
    def _json(self, code:int, data:dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers.get("Content-Length","0"))
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        try:
            payload = json.loads(raw) if raw else {}
        except Exception:
            return self._json(400, {"error":"invalid JSON body"})
        if self.path == "/v1/prompt/build":
            task = payload.get("task","").strip()
            scenario = payload.get("scenario","default")
            if not task: return self._json(400, {"error":"task required"})
            prompt = build_prompt(task, scenario=scenario)
            return self._json(200, {"prompt": prompt})
        elif self.path == "/v1/prompt/validate":
            reply = payload.get("reply","")
            try:
                files = validate_files_payload(reply)
                return self._json(200, {"files": files})
            except ValidationError as e:
                return self._json(422, {"error": str(e)})
        else:
            return self._json(404, {"error":"not found"})

def run_server(host="127.0.0.1", port:int=8765):
    with socketserver.TCPServer((host, port), Handler) as httpd:
        print(f"pf_bridge listening on http://{host}:{port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
