import sys, os, json, threading, urllib.request, time
from pathlib import Path
os.environ['TRADEMIND_DEMO'] = '0'
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '04_API'))
import api, auth
from http.server import HTTPServer
s = HTTPServer(('127.0.0.1', 0), api.H); port = s.server_port; threading.Thread(target=s.serve_forever, daemon=True).start()
def call(path, token, body, xuser=None):
    h = {'Content-Type': 'application/json'}
    if token: h['Authorization'] = 'Bearer ' + token
    if xuser: h['X-User'] = xuser
    r = urllib.request.Request(f'http://127.0.0.1:{port}{path}', json.dumps(body).encode(), h)
    try:
        with urllib.request.urlopen(r) as resp: return resp.status, json.load(resp)
    except urllib.error.HTTPError as e: return e.code, json.load(e)
g, p, a = auth.issue('gestor.demo'), auth.issue('promotor.sul'), auth.issue('admin.demo')
forged = g[:-4] + ('AAAA' if not g.endswith('AAAA') else 'BBBB')
expired = auth.issue('admin.demo', ttl=-10)
cases = [('/ask', g, {'question': 'Qual é a definição de ruptura?'}, None, 200, 'respondido'),
         ('/ask', g, {'question': 'SELECT * FROM usuario'}, None, 200, 'bloqueado'),
         ('/tool', p, {'name': 'get_metric', 'args': {'metric': 'sellout', 'start': '2026-01-01', 'end': '2026-01-31'}}, None, 403, None),
         ('/tool', a, {'name': 'exec_sql', 'args': {}}, None, 400, None),
         ('/tool', a, {'name': 'rank_dimensions', 'args': {'metric': 'ruptura', 'start': '2026-01-01', 'end': '2026-10-31', 'dim': 'regiao'}}, None, 200, None),
         ('/ask', None, {'question': 'oi'}, 'admin.demo', 403, None),   # X-User sem modo demo
         ('/ask', forged, {'question': 'oi'}, None, 403, None),
         ('/ask', expired, {'question': 'oi'}, None, 403, None),
         ('/ask', auth.issue('ninguem'), {'question': 'oi'}, None, 403, None)]
ok = 0
for path, tok, b, xu, exp, st in cases:
    c, out = call(path, tok, b, xu); good = c == exp and (st is None or out.get('status') == st); ok += good
    print('PASS' if good else 'FAIL', path, c, str(out)[:100])
print(f'{ok}/{len(cases)}'); sys.exit(ok != len(cases))
