"""API local do TradeMind AI (stdlib). Uso: python 04_API/api.py  -> http://127.0.0.1:8360
Autenticação: Authorization: Bearer <token HS256> (gere com: python 04_API/auth.py gestor.demo).
Modo demo opcional (TRADEMIND_DEMO=1): aceita header X-User — usado pelo visual de chat no Power BI Desktop local.
Endpoints: GET /health | POST /ask {"question"} | POST /tool {"name","args"}"""
import sys, os, json, csv, uuid, time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '03_AI')); sys.path.insert(0, str(Path(__file__).parent))
import trademind_ai as T, auth
RAG = T.RAG()
TOOLS = {'get_metric': T.get_metric, 'compare_periods': T.compare_periods, 'rank_dimensions': T.rank_dimensions, 'get_metadata': T.get_metadata}
LOG = Path(__file__).resolve().parents[1] / '03_AI' / 'mlops' / 'api_audit.csv'
DEMO = os.environ.get('TRADEMIND_DEMO') == '1'
RATE = {}
def audit(*row):
    LOG.parent.mkdir(exist_ok=True); new = not LOG.exists()
    with open(LOG, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f); new and w.writerow(['id', 'timestamp', 'usuario', 'endpoint', 'status', 'latencia_ms']); w.writerow(row)
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False, default=str).encode(); self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8'); self._cors(); self.end_headers(); self.wfile.write(b)
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-User')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    def do_OPTIONS(self): self.send_response(204); self._cors(); self.end_headers()
    def _login(self):
        a = self.headers.get('Authorization', '')
        if a.startswith('Bearer '): return auth.verify(a[7:])
        if DEMO and self.headers.get('X-User'): return self.headers['X-User']
        raise PermissionError('autenticacao_requerida')
    def do_GET(self): self._send(200, {'status': 'ok', 'demo': DEMO}) if self.path == '/health' else self._send(404, {})
    def do_POST(self):
        t0 = time.time(); login = '?'
        try:
            login = self._login(); user = T.get_user(login)
            now = time.time(); RATE[login] = [x for x in RATE.get(login, []) if now - x < 60] + [now]
            if len(RATE[login]) > 30: raise PermissionError('limite_de_requisicoes')
            n = int(self.headers.get('Content-Length', 0))
            if n > 4096: raise ValueError('payload grande demais')
            body = json.loads(self.rfile.read(n) or b'{}')
            if self.path == '/ask':
                out = RAG.answer(user, str(body.get('question', ''))[:500])
            elif self.path == '/tool':
                name = body.get('name')
                if name not in TOOLS: raise ValueError('ferramenta não autorizada')
                out = {'result': TOOLS[name](user, **(body.get('args') or {}))}
            else: return self._send(404, {})
            code = 200; st = out.get('status', 'ok')
        except PermissionError as e: code, out, st = 403, {'erro': str(e)}, 'negado'
        except (ValueError, TypeError) as e: code, out, st = 400, {'erro': str(e)}, 'invalido'
        audit(uuid.uuid4().hex[:10], T.now(), login, self.path, st, int((time.time() - t0) * 1000)); self._send(code, out)
if __name__ == '__main__':
    print(f'TradeMind API em http://127.0.0.1:8360 (demo={DEMO})'); ThreadingHTTPServer(('127.0.0.1', 8360), H).serve_forever()
