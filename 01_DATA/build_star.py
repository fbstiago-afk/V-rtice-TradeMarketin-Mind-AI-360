"""Exporta o SQLite para CSVs do modelo estrela consumido pelo PBIP."""
import sqlite3, csv, os, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'base trademind'/'trademind_ai360.sqlite'
OUT=ROOT/'01_DATA'/'processed'; OUT.mkdir(parents=True,exist_ok=True)
c=sqlite3.connect(DB)
Q={
'dPDV':"select p.id pdv_id,p.nome pdv,p.cidade,p.uf,p.regiao,p.formato,r.nome rede from pdv p join rede r on r.id=p.rede_id",
'dProduto':"select p.id produto_id,p.sku,p.nome produto,p.categoria,i.nome industria,p.preco_referencia,p.custo_unitario from produto p join industria i on i.id=p.industria_id",
'dPromotor':"select id promotor_id,nome promotor,regiao regiao_promotor,ativo from promotor",
'dCampanha':"select c.id campanha_id,c.nome campanha,i.nome industria_campanha,c.inicio,c.fim,c.orcamento from campanha c join industria i on i.id=c.industria_id",
'fVenda':"select data,pdv_id,produto_id,unidades,receita from venda_diaria",
'fEstoque':"select data,pdv_id,produto_id,saldo,ruptura from estoque_semanal",
'fVisita':"select id visita_id,data,pdv_id,promotor_id,duracao_min,checklist_pct,observacao from visita",
'fAuditoria':"select a.id auditoria_id,v.data,v.pdv_id,v.promotor_id,a.produto_id,a.preco_gondola,a.preco_concorrente,a.facings,a.planograma_ok,a.material_pdv_ok from auditoria a join visita v on v.id=a.visita_id",
'fExecCampanha':"select campanha_id,pdv_id,data,custo,execucao_pct from execucao_campanha",
'fMeta':"select mes||'-01' data,pdv_id,meta_receita from meta_mensal",
'dUsuarioAcesso':"select u.login, u.login||'@vertice.demo' upn, u.perfil, coalesce(i.nome,'') industria_acesso, coalesce(u.regiao,'') regiao_acesso, (select max(permitido) from regra_acesso r where r.perfil=u.perfil and r.recurso='vendas') pode_vendas, (select max(permitido) from regra_acesso r where r.perfil=u.perfil and r.recurso='estoque') pode_estoque, (select max(permitido) from regra_acesso r where r.perfil=u.perfil and r.recurso='visitas') pode_visitas from usuario u left join industria i on i.id=u.industria_id",
'dDocumento':"select id documento_id,titulo,tipo,coalesce(industria_id,0) industria_id,versao,conteudo from documento",
}
issues=[]
for t,q in Q.items():
    cur=c.execute(q); cols=[d[0] for d in cur.description]; rows=cur.fetchall()
    with open(OUT/f'{t}.csv','w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(cols); w.writerows(rows)
# calendário
import datetime as dt
d=dt.date(2025,1,1); rows=[]
M=['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
while d<=dt.date(2026,12,31):
    rows.append([d.isoformat(),d.year,d.month,M[d.month-1],f"{M[d.month-1]}/{str(d.year)[2:]}",d.year*100+d.month,d.isocalendar()[1],(d-dt.timedelta(days=d.weekday())).isoformat(),'Simulado futuro' if d>dt.date(2026,11,14) else 'Simulado observado'])
    d+=dt.timedelta(1)
with open(OUT/'dCalendario.csv','w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['Data','Ano','MesNum','Mes','MesAno','AnoMes','Semana','InicioSemana','StatusPeriodo']); w.writerows(rows)
# qualidade
chk={
 'venda_pdv_orfao':"select count(*) from venda_diaria v left join pdv p on p.id=v.pdv_id where p.id is null",
 'venda_produto_orfao':"select count(*) from venda_diaria v left join produto p on p.id=v.produto_id where p.id is null",
 'venda_duplicada':"select count(*) from (select data,pdv_id,produto_id from venda_diaria group by 1,2,3 having count(*)>1)",
 'venda_receita_negativa':"select count(*) from venda_diaria where receita<0 or unidades<0",
 'estoque_saldo_negativo':"select count(*) from estoque_semanal where saldo<0",
 'estoque_ruptura_inconsistente':"select count(*) from estoque_semanal where (saldo=0)<>(ruptura=1)",
 'visita_checklist_fora_0_100':"select count(*) from visita where checklist_pct<0 or checklist_pct>100",
 'auditoria_visita_orfa':"select count(*) from auditoria a left join visita v on v.id=a.visita_id where v.id is null",
 'pdv_com_venda':"select count(distinct pdv_id) from venda_diaria",
 'skus_com_venda':"select count(distinct produto_id) from venda_diaria",
 'skus_auditados_estoque':"select count(distinct produto_id) from estoque_semanal",
}
res={k:c.execute(q).fetchone()[0] for k,q in chk.items()}
json.dump(res,open(ROOT/'01_DATA'/'quality'/'data_quality.json','w'),indent=2)
print(res)
