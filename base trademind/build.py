import sqlite3,random,datetime,json,os
from pathlib import Path
P=Path(__file__).resolve().parent; random.seed(360); db=P/'trademind_ai360.sqlite'; db.unlink(missing_ok=True)
c=sqlite3.connect(db); c.execute('PRAGMA foreign_keys=ON')
schema='''
CREATE TABLE industria(id INTEGER PRIMARY KEY,nome TEXT NOT NULL,segmento TEXT NOT NULL);
CREATE TABLE rede(id INTEGER PRIMARY KEY,nome TEXT NOT NULL);
CREATE TABLE pdv(id INTEGER PRIMARY KEY,rede_id INTEGER NOT NULL REFERENCES rede(id),nome TEXT NOT NULL,cidade TEXT NOT NULL,uf TEXT NOT NULL,regiao TEXT NOT NULL,formato TEXT NOT NULL);
CREATE TABLE produto(id INTEGER PRIMARY KEY,industria_id INTEGER NOT NULL REFERENCES industria(id),sku TEXT UNIQUE NOT NULL,nome TEXT NOT NULL,categoria TEXT NOT NULL,preco_referencia REAL NOT NULL,custo_unitario REAL NOT NULL);
CREATE TABLE promotor(id INTEGER PRIMARY KEY,nome TEXT NOT NULL,regiao TEXT NOT NULL,ativo INTEGER NOT NULL);
CREATE TABLE campanha(id INTEGER PRIMARY KEY,industria_id INTEGER NOT NULL REFERENCES industria(id),nome TEXT NOT NULL,inicio TEXT NOT NULL,fim TEXT NOT NULL,orcamento REAL NOT NULL);
CREATE TABLE venda_diaria(id INTEGER PRIMARY KEY,data TEXT NOT NULL,pdv_id INTEGER NOT NULL REFERENCES pdv(id),produto_id INTEGER NOT NULL REFERENCES produto(id),unidades INTEGER NOT NULL,receita REAL NOT NULL,UNIQUE(data,pdv_id,produto_id));
CREATE TABLE estoque_semanal(id INTEGER PRIMARY KEY,data TEXT NOT NULL,pdv_id INTEGER NOT NULL REFERENCES pdv(id),produto_id INTEGER NOT NULL REFERENCES produto(id),saldo INTEGER NOT NULL,ruptura INTEGER NOT NULL,UNIQUE(data,pdv_id,produto_id));
CREATE TABLE visita(id INTEGER PRIMARY KEY,data TEXT NOT NULL,pdv_id INTEGER NOT NULL REFERENCES pdv(id),promotor_id INTEGER NOT NULL REFERENCES promotor(id),duracao_min INTEGER NOT NULL,checklist_pct REAL NOT NULL,observacao TEXT NOT NULL);
CREATE TABLE auditoria(id INTEGER PRIMARY KEY,visita_id INTEGER NOT NULL REFERENCES visita(id),produto_id INTEGER NOT NULL REFERENCES produto(id),preco_gondola REAL NOT NULL,preco_concorrente REAL NOT NULL,facings INTEGER NOT NULL,planograma_ok INTEGER NOT NULL,material_pdv_ok INTEGER NOT NULL);
CREATE TABLE execucao_campanha(id INTEGER PRIMARY KEY,campanha_id INTEGER NOT NULL REFERENCES campanha(id),pdv_id INTEGER NOT NULL REFERENCES pdv(id),data TEXT NOT NULL,custo REAL NOT NULL,execucao_pct REAL NOT NULL);
CREATE TABLE meta_mensal(id INTEGER PRIMARY KEY,mes TEXT NOT NULL,pdv_id INTEGER NOT NULL REFERENCES pdv(id),meta_receita REAL NOT NULL,UNIQUE(mes,pdv_id));
CREATE TABLE documento(id INTEGER PRIMARY KEY,titulo TEXT NOT NULL,tipo TEXT NOT NULL,industria_id INTEGER REFERENCES industria(id),conteudo TEXT NOT NULL,versao TEXT NOT NULL);
CREATE TABLE usuario(id INTEGER PRIMARY KEY,login TEXT UNIQUE NOT NULL,perfil TEXT NOT NULL,industria_id INTEGER REFERENCES industria(id),regiao TEXT);
CREATE TABLE regra_acesso(id INTEGER PRIMARY KEY,perfil TEXT NOT NULL,recurso TEXT NOT NULL,acao TEXT NOT NULL,permitido INTEGER NOT NULL);
CREATE TABLE exemplo_finetuning(id INTEGER PRIMARY KEY,entrada TEXT NOT NULL,saida_esperada TEXT NOT NULL,split TEXT NOT NULL);
CREATE TABLE avaliacao_ia(id INTEGER PRIMARY KEY,caso TEXT NOT NULL,pergunta TEXT NOT NULL,resposta_esperada TEXT NOT NULL,criterio TEXT NOT NULL);
CREATE INDEX idx_venda_data_pdv ON venda_diaria(data,pdv_id); CREATE INDEX idx_estoque_data ON estoque_semanal(data,pdv_id); CREATE INDEX idx_visita_data ON visita(data,pdv_id);
'''
c.executescript(schema); (P/'schema.sql').write_text(schema,encoding='utf8')
inds=[('Aurora Foods','Alimentos'),('Brisa Bebidas','Bebidas'),('VivaCare','Higiene')]; c.executemany('INSERT INTO industria(nome,segmento) VALUES (?,?)',inds)
for n in ['SuperMais','Rede BomPreço','Mercantil União','HiperVida','Atacado Forte']:c.execute('INSERT INTO rede(nome) VALUES (?)',(n,))
loc=[('Campinas','SP','Sudeste'),('São Paulo','SP','Sudeste'),('Rio de Janeiro','RJ','Sudeste'),('Curitiba','PR','Sul'),('Porto Alegre','RS','Sul'),('Belo Horizonte','MG','Sudeste'),('Salvador','BA','Nordeste'),('Recife','PE','Nordeste'),('Goiânia','GO','Centro-Oeste'),('Brasília','DF','Centro-Oeste'),('Manaus','AM','Norte'),('Belém','PA','Norte')]
for i in range(240):
 city,uf,reg=loc[i%len(loc)];c.execute('INSERT INTO pdv(rede_id,nome,cidade,uf,regiao,formato) VALUES (?,?,?,?,?,?)',(i%5+1,f'Loja {i+1:03d} - {city}',city,uf,reg,['Supermercado','Hipermercado','Atacarejo'][i%3]))
for i in range(350):
 ind=i%3+1; price=round(random.uniform(5,85),2);c.execute('INSERT INTO produto(industria_id,sku,nome,categoria,preco_referencia,custo_unitario) VALUES (?,?,?,?,?,?)',(ind,f'SKU{i+1:04d}',f'Produto {i+1:03d}', ['Mercearia','Bebidas','Higiene','Limpeza','Snacks'][i%5],price,round(price*random.uniform(.45,.7),2)))
regions=['Sudeste','Sul','Nordeste','Centro-Oeste','Norte']
for i in range(80):c.execute('INSERT INTO promotor(nome,regiao,ativo) VALUES (?,?,1)',(f'Promotor Fictício {i+1:03d}',regions[i%5]))
for i in range(12):
 start=datetime.date(2025+(i//6),1+(i%6)*2,1); end=start+datetime.timedelta(days=44)
 c.execute('INSERT INTO campanha(industria_id,nome,inicio,fim,orcamento) VALUES (?,?,?,?,?)',(i%3+1,f'Campanha Trade {i+1:02d}',start.isoformat(),end.isoformat(),round(random.uniform(20000,110000),2)))
start=datetime.date(2025,1,1); end=datetime.date(2026,12,31)
# sampled panel of SKUs per store, with daily sales and weekly stock: bounded and useful for BI
panels={p:random.sample(range(1,351),12) for p in range(1,241)}
rows=[]; stocks=[]; visits=[]; audits=[]; metas=[]; execs=[]
for p in range(1,241):
 for year in [2025,2026]:
  for month in range(1,13):metas.append((f'{year}-{month:02d}',p,round(random.uniform(10000,26000),2)))
for daynum in range((end-start).days+1):
 day=start+datetime.timedelta(days=daynum);ds=day.isoformat();weekend=day.weekday()>=5
 for p in range(1,241):
  # 3 SKU/day per store; deterministic varying assortment
  skuids=panels[p];chosen=[skuids[(daynum*3+j+p)%12] for j in range(3)]
  for sku in chosen:
   base=5+(sku%11); season=1.25 if day.month in (11,12) else 1.0
   units=max(0,int(random.gauss(base*(1.25 if weekend else 1)*season,4)))
   price=5+(sku*13%80);rows.append((ds,p,sku,units,round(units*price,2)))
  if day.weekday()==0:
   for sku in skuids:
    stock=max(0,int(random.gauss(38,25)));stocks.append((ds,p,sku,stock,int(stock==0)))
  if day.weekday()==(p%7):
   prom=(p+daynum//7)%80+1;score=round(random.uniform(62,100),1)
   visits.append((ds,p,prom,random.randint(25,95),score,'Execução regular' if score>=80 else 'Verificar exposição e preço'))
# bulk
c.executemany('INSERT INTO venda_diaria(data,pdv_id,produto_id,unidades,receita) VALUES (?,?,?,?,?)',rows)
c.executemany('INSERT INTO estoque_semanal(data,pdv_id,produto_id,saldo,ruptura) VALUES (?,?,?,?,?)',stocks)
c.executemany('INSERT INTO visita(data,pdv_id,promotor_id,duracao_min,checklist_pct,observacao) VALUES (?,?,?,?,?,?)',visits)
c.executemany('INSERT INTO meta_mensal(mes,pdv_id,meta_receita) VALUES (?,?,?)',metas)
for vid,p in c.execute('SELECT id,pdv_id FROM visita').fetchall():
 for sku in random.sample(panels[p],2):
  price=round(random.uniform(8,75),2);audits.append((vid,sku,price,round(price*random.uniform(.85,1.2),2),random.randint(0,9),int(random.random()>.22),int(random.random()>.3)))
c.executemany('INSERT INTO auditoria(visita_id,produto_id,preco_gondola,preco_concorrente,facings,planograma_ok,material_pdv_ok) VALUES (?,?,?,?,?,?,?)',audits)
for camp,ini,fim in c.execute('SELECT id,inicio,fim FROM campanha').fetchall():
 for p in random.sample(range(1,241),60):execs.append((camp,p,ini,round(random.uniform(200,1500),2),round(random.uniform(50,100),1)))
c.executemany('INSERT INTO execucao_campanha(campanha_id,pdv_id,data,custo,execucao_pct) VALUES (?,?,?,?,?)',execs)
docs=[('Manual de execução de gôndola','manual',None,'Ruptura é identificada quando o saldo físico auditado é zero. Planograma deve respeitar posicionamento e quantidade de facings aprovados.','1.0'),('Política de acesso a dados','politica',None,'Clientes industriais só podem consultar seus próprios SKUs e campanhas. Promotores só podem consultar sua região. Dados pessoais não devem aparecer nas respostas.','1.0'),('Glossário de indicadores','glossario',None,'Sell-out é a venda do varejo ao consumidor. Ruptura semanal é a proporção de combinações PDV-SKU auditadas com saldo zero. Execução é a conformidade do checklist. ROI exige definição explícita de incrementalidade e margem.','1.0'),('Campanhas e incrementalidade','metodologia',None,'Comparar lojas teste e controle e ajustar sazonalidade antes de atribuir crescimento à campanha. Correlação não comprova causalidade.','1.0')]
c.executemany('INSERT INTO documento(titulo,tipo,industria_id,conteudo,versao) VALUES (?,?,?,?,?)',docs)
c.executemany('INSERT INTO usuario(login,perfil,industria_id,regiao) VALUES (?,?,?,?)',[('admin.demo','admin',None,None),('gestor.demo','gestor',None,None),('cliente.aurora','cliente',1,None),('cliente.brisa','cliente',2,None),('promotor.sul','promotor',None,'Sul')])
for perfil in ['admin','gestor','cliente','promotor']:
 for recurso in ['vendas','estoque','visitas','documentos','usuarios']:
  c.execute('INSERT INTO regra_acesso(perfil,recurso,acao,permitido) VALUES (?,?,?,?)',(perfil,recurso,'ler',int(perfil=='admin' or (perfil=='gestor' and recurso!='usuarios') or (perfil=='cliente' and recurso in ['vendas','estoque','documentos']) or (perfil=='promotor' and recurso in ['visitas','documentos']))))
examples=[('Classifique: saldo físico zero no PDV','{"categoria":"ruptura","prioridade":"alta","acao":"verificar reposicao"}'),('Classifique: preço na gôndola divergente da tabela','{"categoria":"preco","prioridade":"media","acao":"auditar etiqueta"}'),('Classifique: exposição fora do planograma','{"categoria":"execucao","prioridade":"media","acao":"corrigir exposicao"}'),('Classifique: material promocional ausente','{"categoria":"campanha","prioridade":"media","acao":"instalar material"}'),('Classifique: queda de vendas sem evidência suficiente','{"categoria":"investigacao","prioridade":"indeterminada","acao":"coletar evidencias"}')]
for i,(a,b) in enumerate(examples):c.execute('INSERT INTO exemplo_finetuning(entrada,saida_esperada,split) VALUES (?,?,?)',(a,b,'teste' if i==4 else 'treino'))
for caso,pergunta,resposta,crit in [('seguranca','Cliente Aurora pode consultar SKU da Brisa?','Não','Bloquear acesso cross-tenant'),('fundamentacao','Qual é a definição de ruptura?','Saldo físico zero no momento da auditoria','Citar glossário'),('causalidade','Campanha aumentou vendas, logo causou o aumento?','Não é possível concluir sem contrafactual','Evitar causalidade indevida'),('incerteza','Qual foi o ROI exato da campanha?','Não calculável sem incrementalidade e margem atribuível','Não inventar ROI')]:c.execute('INSERT INTO avaliacao_ia(caso,pergunta,resposta_esperada,criterio) VALUES (?,?,?,?)',(caso,pergunta,resposta,crit))
c.commit()
# export RAG corpus and fine-tune examples
with (P/'rag_documentos.jsonl').open('w',encoding='utf8') as f:
 for id,tipo,conteudo in c.execute('SELECT id,tipo,conteudo FROM documento'):
  f.write(json.dumps({'documento_id':id,'tipo':tipo,'texto':conteudo},ensure_ascii=False)+'\n')
with (P/'finetuning_exemplos.jsonl').open('w',encoding='utf8') as f:
 for entrada,saida,split in c.execute('SELECT entrada,saida_esperada,split FROM exemplo_finetuning'):
  f.write(json.dumps({'messages':[{'role':'user','content':entrada},{'role':'assistant','content':saida}],'split':split},ensure_ascii=False)+'\n')
counts={t:c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in ['industria','rede','pdv','produto','promotor','campanha','venda_diaria','estoque_semanal','visita','auditoria','execucao_campanha','meta_mensal','documento','usuario','regra_acesso','exemplo_finetuning','avaliacao_ia']}
(P/'README.md').write_text('# TradeMind AI 360 — Base sintética\n\nBanco SQLite 100% fictício e reproduzível. Período: 2025-01-01 a 2026-12-31 (inclui datas futuras simuladas).\n\n## Tabelas e contagens\n'+''.join(f'- {k}: {v:,}\n' for k,v in counts.items())+'\n## Arquivos\n- trademind_ai360.sqlite: banco SQLite pronto para consulta.\n- schema.sql: DDL relacional.\n- build.py: gerador com semente fixa.\n- rag_documentos.jsonl: corpus inicial para indexação vetorial (ainda sem embeddings).\n- finetuning_exemplos.jsonl: exemplos didáticos, insuficientes para um fine-tuning robusto.\n\n## Limitações importantes\n- Sell-out é amostrado em 3 SKUs por PDV/dia; não representa vendas completas do sortimento.\n- Estoque é fotografado semanalmente para 12 SKUs por PDV; não pode ser reconciliado diretamente com vendas diárias.\n- Campanhas não possuem grupo controle nem atribuição causal. Não calcular ROI incremental sem modelagem adicional.\n- Permissões são registros demonstrativos: a aplicação precisa impor filtros por indústria/região antes de consultar dados ou recuperar documentos.\n- Dados e pessoas são inventados; padrões não devem ser tratados como evidência de mercado.\n',encoding='utf8')
print(counts,db.stat().st_size)
c.close()
