"""Tokens assinados HMAC-SHA256 (formato JWT HS256) com expiração. Segredo em TRADEMIND_SECRET (nunca no código/relatório).
Substituível por OIDC/Entra ID: basta trocar verify() por validação do token do provedor."""
import os, hmac, hashlib, base64, json, time, secrets
from pathlib import Path
SECRET_FILE = Path(__file__).parent / '.secret'
def _secret():
    s = os.environ.get('TRADEMIND_SECRET')
    if s: return s.encode()
    if not SECRET_FILE.exists(): SECRET_FILE.write_text(secrets.token_hex(32))
    return SECRET_FILE.read_text().strip().encode()
def _b64(b): return base64.urlsafe_b64encode(b).rstrip(b'=').decode()
def _unb64(s): return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))
def issue(login, ttl=3600):
    h = _b64(json.dumps({'alg': 'HS256', 'typ': 'JWT'}).encode())
    p = _b64(json.dumps({'sub': login, 'exp': int(time.time()) + ttl, 'iat': int(time.time())}).encode())
    sig = _b64(hmac.new(_secret(), f'{h}.{p}'.encode(), hashlib.sha256).digest())
    return f'{h}.{p}.{sig}'
def verify(token):
    try:
        h, p, sig = token.split('.')
        exp_sig = _b64(hmac.new(_secret(), f'{h}.{p}'.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, exp_sig): raise PermissionError('token_invalido')
        claims = json.loads(_unb64(p))
        if claims['exp'] < time.time(): raise PermissionError('token_expirado')
        return claims['sub']
    except PermissionError: raise
    except Exception: raise PermissionError('token_invalido')
if __name__ == '__main__':
    import sys; print(issue(sys.argv[1] if len(sys.argv) > 1 else 'gestor.demo', ttl=8 * 3600))
