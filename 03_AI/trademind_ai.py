"""TradeMind AI 360 — RAG, ferramentas analíticas tipadas, guardrails, especialização de classificador,
modelo de risco de ruptura e registro MLOps. Execução local, sem serviço externo de LLM.
Geração das respostas: EXTRATIVA (trechos recuperados), não generativa — não há LLM conectado."""
import sqlite3, json, re, time, csv, uuid, datetime as dt, random
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'base trademind'/'trademind_ai360.sqlite'
OUT=ROOT/'01_DATA'/'processed'
def now(): return dt.datetime.now().isoformat(timespec='seconds')
def db(): return sqlite3.connect(DB)

# ---------------- Identidade e autorização ----------------
def get_user(login):
    r=db().execute("select login,perfil,industria_id,regiao from usuario where login=?",(login,)).fetchone()
    if not r: raise PermissionError('usuario_desconhecido')
    return dict(zip(['login','perfil','industria_id','regiao'],r))
def allowed(user,recurso):
    r=db().execute("select permitido from regra_acesso where perfil=? and recurso=? and acao='ler'",(user['perfil'],recurso)).fetchone()
    return bool(r and r[0])

# ---------------- Guardrails ----------------
INJ=re.compile(r"(ignore|desconsidere|esque[çc]a).{0,40}(regras|instru[çc][õo]es|pol[ií]tica)|system prompt|revele.{0,20}(senha|segredo|token)",re.I)
PII=re.compile(r"(cpf|telefone|e-?mail|endere[çc]o|sal[aá]rio).{0,30}(promotor|usu[aá]rio|funcion)",re.I)
SQLRAW=re.compile(r"\b(select|drop|delete|update|insert|pragma|attach)\b.+\b(from|table|into|database)\b",re.I)
def guard_input(user,text):
    if SQLRAW.search(text): return 'bloqueado','consulta_arbitraria'
    if PII.search(text): return 'bloqueado','dados_pessoais'
    if INJ.search(text): return 'bloqueado','prompt_injection'
    return 'permitido','ok'
def sanitize_chunk(t):
    "Instruções dentro de documentos recuperados são tratadas como dados e removidas."
    return INJ.sub('[instrução removida pelo guardrail]',t)

# ---------------- Ferramentas analíticas tipadas ----------------
METRICS={'sellout':("select sum(v.receita) from venda_diaria v join pdv p on p.id=v.pdv_id join produto pr on pr.id=v.produto_id",'vendas'),
         'unidades':("select sum(v.unidades) from venda_diaria v join pdv p on p.id=v.pdv_id join produto pr on pr.id=v.produto_id",'vendas'),
         'ruptura':("select avg(v.ruptura) from estoque_semanal v join pdv p on p.id=v.pdv_id join produto pr on pr.id=v.produto_id",'estoque'),
         'checklist':("select avg(v.checklist_pct)/100.0 from visita v join pdv p on p.id=v.pdv_id",'visitas')}
DIMS={'regiao':'p.regiao','rede':'(select nome from rede where id=p.rede_id)','uf':'p.uf','categoria':'pr.categoria','pdv':'p.nome'}
DATE_RE=re.compile(r'^\d{4}-\d{2}-\d{2}$')
def _scope(user,metric,where,args):
    sql,rec=METRICS[metric]
    if not allowed(user,rec): raise PermissionError(f'perfil {user["perfil"]} sem acesso a {rec}')
    if user['industria_id'] and 'pr.' in sql: where.append('pr.industria_id=?'); args.append(user['industria_id'])
    if user['regiao']: where.append('p.regiao=?'); args.append(user['regiao'])
    return sql
def _validate(metric,start,end,filters):
    if metric not in METRICS: raise ValueError('metric invalida')
    for d in (start,end):
        if not DATE_RE.match(d): raise ValueError('data invalida')
    if start>end: raise ValueError('periodo invertido')
    for k in filters or {}:
        if k not in DIMS: raise ValueError(f'filtro nao permitido: {k}')
def get_metric(user,metric,start,end,filters=None):
    _validate(metric,start,end,filters); where=['v.data between ? and ?']; args=[start,end]
    sql=_scope(user,metric,where,args)
    for k,v in (filters or {}).items(): where.append(f'{DIMS[k]}=?'); args.append(v)
    return db().execute(sql+' where '+' and '.join(where),args).fetchone()[0]
def compare_periods(user,metric,a,b,filters=None):
    x=get_metric(user,metric,*a,filters); y=get_metric(user,metric,*b,filters)
    return {'atual':x,'anterior':y,'var':(x/y-1) if x and y else None}
def rank_dimensions(user,metric,start,end,dim,top=5,filters=None):
    _validate(metric,start,end,filters)
    if dim not in DIMS: raise ValueError('dim invalida')
    if not 1<=int(top)<=50: raise ValueError('top fora do limite')
    where=['v.data between ? and ?']; args=[start,end]; sql=_scope(user,metric,where,args)
    if 'pr.' in DIMS[dim] and 'pr.' not in sql: raise ValueError('dimensao incompativel')
    for k,v in (filters or {}).items(): where.append(f'{DIMS[k]}=?'); args.append(v)
    sql=sql.replace('select ',f'select {DIMS[dim]} d, ',1)+' where '+' and '.join(where)+f' group by 1 order by 2 desc limit {int(top)}'
    return db().execute(sql,args).fetchall()
def get_metadata(_user=None): return {'metricas':list(METRICS),'dimensoes':list(DIMS),'periodo':['2025-01-01','2026-12-31'],'natureza':'dados fictícios simulados'}

# ---------------- RAG ----------------
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
def _norm(t):
    import unicodedata; return ''.join(ch for ch in unicodedata.normalize('NFD',t.lower()) if unicodedata.category(ch)!='Mn')
class RAG:
    def __init__(self):
        rows=[r+('original',) for r in db().execute("select id,titulo,tipo,industria_id,versao,conteudo from documento").fetchall()]
        comp=Path(__file__).parent/'rag'/'corpus_complementar.jsonl'
        if comp.exists():
            for l in open(comp,encoding='utf-8'):
                d=json.loads(l); rows.append((d['id'],d['titulo'],d['tipo'],d['industria_id'],d['versao'],d['conteudo'],'complementar-projeto'))
        self.chunks=[]
        for i,ti,tp,ind,ver,txt,orig in rows:
            for j,s in enumerate([s.strip() for s in re.split(r'(?<=[.!?])\s+',txt) if s.strip()]):
                self.chunks.append(dict(doc_id=i,titulo=ti,tipo=tp,industria_id=ind,versao=ver,origem=orig,chunk=j,texto=s))
        SW='a o e de da do das dos para por com sem em no na nos nas um uma uns umas que qual quais como e ou se ser sao foi utilizada utilizado pela pelo amanha devo empresa definicao define significa conceito exato exata o que'.split()
        self.vec=TfidfVectorizer(preprocessor=_norm,ngram_range=(1,2),sublinear_tf=True,stop_words=SW)
        corpus=[c['titulo']+' '+c['texto'] for c in self.chunks]
        self.M=self.vec.fit_transform(corpus)
        self.vc=TfidfVectorizer(preprocessor=_norm,analyzer='char_wb',ngram_range=(3,5),sublinear_tf=True)
        self.C=self.vc.fit_transform(corpus)
        an=self.vec.build_analyzer(); self.toks=[set(an(c)) for c in corpus]
    def retrieve(self,user,q,k=3,min_score=0.08):
        if not allowed(user,'documentos'): raise PermissionError('sem acesso a documentos')
        sw=cosine_similarity(self.vec.transform([q]),self.M)[0]; sc=cosine_similarity(self.vc.transform([q]),self.C)[0]
        # cobertura ponderada por IDF dos termos da pergunta (re-ranking lexical)
        an=self.vec.build_analyzer(); qt={t for t in an(q) if ' ' not in t and t in self.vec.vocabulary_}
        idf=self.vec.idf_; tot=sum(idf[self.vec.vocabulary_[t]] for t in qt) or 1
        cov=np.array([sum(idf[self.vec.vocabulary_[t]] for t in qt if t in self.toks[i])/tot for i in range(len(self.chunks))])
        s=(0.45*sw+0.15*sc+0.40*cov)*(sw>0)
        idx=[i for i in s.argsort()[::-1] if s[i]>=min_score and (self.chunks[i]['industria_id'] in (None,user['industria_id']) or user['perfil'] in('admin','gestor'))][:k]
        return [dict(self.chunks[i],texto=sanitize_chunk(self.chunks[i]['texto']),score=round(float(s[i]),4)) for i in idx]
    def answer(self,user,q):
        t0=time.time(); st,rule=guard_input(user,q)
        if st=='bloqueado': return dict(status='bloqueado',regra=rule,resposta=None,evidencias=[],latencia_ms=int((time.time()-t0)*1000))
        ev=self.retrieve(user,q,k=5)
        if not ev: return dict(status='sem_evidencia',regra='ok',resposta='Não encontrei evidência documental suficiente para responder.',evidencias=[],latencia_ms=int((time.time()-t0)*1000))
        same=[e for e in ev[1:] if e['doc_id']==ev[0]['doc_id']][:1]; other=[e for e in ev[1:] if e['doc_id']!=ev[0]['doc_id']][:1]
        top=[ev[0]]+same+other
        resp=' '.join(e['texto'] for e in top)+' [Fontes: '+'; '.join(dict.fromkeys(f"{e['titulo']} v{e['versao']}" for e in top))+']'
        return dict(status='respondido',regra='ok',resposta=resp,evidencias=ev,latencia_ms=int((time.time()-t0)*1000))
