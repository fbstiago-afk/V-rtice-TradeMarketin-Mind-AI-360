"""Gera o projeto PBIP (TMDL + PBIR) do Vértice TradeMind AI 360 a partir dos CSVs processados."""
import csv, json, shutil, hashlib, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIN_DATA = r"E:\Projetos BI\20 - TradeMind AI 360\01_DATA\processed" + "\\"
DATA = ROOT / '01_DATA' / 'processed'
PB = ROOT / '02_POWER_BI'
NAME = 'TradeMind_AI360'
SM = PB / f'{NAME}.SemanticModel'; RP = PB / f'{NAME}.Report'
for d in (SM, RP):
    if d.exists(): shutil.rmtree(d)
SCH = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition'

def lt(s): h = hashlib.md5(s.encode()).hexdigest(); return f'{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}'
def wj(p, o): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding='utf-8')
def wt(p, s): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s, encoding='utf-8')
def q(n): return f"'{n}'" if re.search(r'[^A-Za-z0-9_]', n) else n

# ============================ SEMANTIC MODEL ============================
TABLES = ['dCalendario', 'dPDV', 'dProduto', 'dPromotor', 'dCampanha', 'fVenda', 'fEstoque', 'fVisita', 'fAuditoria', 'fExecCampanha', 'fMeta',
          'dDocumento', 'dModelosIA', 'fExperimentosML', 'fTestesGuardrails', 'fAvaliacoesLLM', 'fRecuperacaoRAG', 'fInteracoesIA',
          'fComparadorModelos', 'fOcorrenciasPDV', 'fMonitorRuptura', 'dUsuarioAcesso']
DATES = {'data', 'Data', 'InicioSemana', 'inicio', 'fim', 'mes'}
INTS = {'unidades', 'saldo', 'ruptura', 'Ano', 'MesNum', 'AnoMes', 'Semana', 'duracao_min', 'facings', 'planograma_ok', 'material_pdv_ok', 'ativo',
        'aprovado', 'n_evidencias', 'n_trechos', 'pode_vendas', 'pode_estoque', 'pode_visitas', 'latencia_ms', 'rank', 'acerto_base', 'acerto_especializado', 'sintetico', 'ocorrencia_id', 'visita_id', 'auditoria_id', 'industria_id'}
DBL = {'receita', 'preco_referencia', 'custo_unitario', 'orcamento', 'checklist_pct', 'execucao_pct', 'meta_receita', 'score', 'valor', 'prob_media_prevista',
       'taxa_observada', 'confianca', 'custo', 'preco_gondola', 'preco_concorrente'}
def ctype(c):
    if c in DATES: return 'dateTime', 'type date'
    if c in INTS or (c.endswith('_id') and c != 'interacao_id'): return 'int64', 'Int64.Type'
    if c in DBL: return 'double', 'type number'
    return 'string', 'type text'
HIDE = {'dUsuarioAcesso', 'fVenda', 'fEstoque', 'fVisita', 'fAuditoria', 'fExecCampanha', 'fMeta'}

tbl_files = {}
for t in TABLES:
    cols = next(csv.reader(open(DATA / f'{t}.csv', encoding='utf-8')))
    L = [f'table {t}', f'\tlineageTag: {lt(t)}']
    if t == 'dCalendario': L.insert(1, '\tdataCategory: Time')
    L.append('')
    for c in cols:
        dt_, _ = ctype(c)
        L += [f'\tcolumn {q(c)}', f'\t\tdataType: {dt_}']
        if dt_ == 'dateTime': L.append('\t\tformatString: dd/mm/yyyy')
        if dt_ == 'double': L.append('\t\tformatString: #,0.00')
        if t == 'dCalendario' and c == 'Data': L.append('\t\tisKey')
        if t == 'dCalendario' and c == 'MesAno': L.append('\t\tsortByColumn: AnoMes')
        if t in HIDE or c.endswith('_id'): L.append('\t\tisHidden')
        L += [f'\t\tlineageTag: {lt(t + c)}', '\t\tsummarizeBy: none', f'\t\tsourceColumn: {c}', '']
    types = ', '.join('{"%s", %s}' % (c, ctype(c)[1]) for c in cols)
    L += [f'\tpartition {t} = m', '\t\tmode: import', '\t\tsource =', '\t\t\t\tlet',
          f'\t\t\t\t    Fonte = Csv.Document(File.Contents(PastaDados & "{t}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
          '\t\t\t\t    Cab = Table.PromoteHeaders(Fonte, [PromoteAllScalars=true]),',
          f'\t\t\t\t    Tipos = Table.TransformColumnTypes(Cab, {{{types}}}, "en-US")',
          '\t\t\t\tin', '\t\t\t\t    Tipos', '']
    tbl_files[t] = '\n'.join(L)

# ---------------- Measures ----------------
M = []  # (folder, name, expr, fmt, imageurl)
def ms(folder, name, expr, fmt=None, img=False): M.append((folder, name, expr.strip('\n'), fmt, img))
SY = "SAMEPERIODLASTYEAR(dCalendario[Data])"
ms('01 Vendas', 'Sell-out', 'SUM(fVenda[receita])', '"R$" #,0')
ms('01 Vendas', 'Unidades', 'SUM(fVenda[unidades])', '#,0')
ms('01 Vendas', 'Preço Médio', 'DIVIDE([Sell-out], [Unidades])', '"R$" #,0.00')
ms('01 Vendas', 'Sell-out AA', f'CALCULATE([Sell-out], {SY})', '"R$" #,0')
ms('01 Vendas', 'Sell-out Var %', 'VAR c = CALCULATE([Sell-out], KEEPFILTERS(FILTER(ALL(dCalendario[Data]), dCalendario[Data] >= EDATE(CALCULATE(MIN(fVenda[data]), REMOVEFILTERS()), 12)))) VAR a = CALCULATE([Sell-out AA], KEEPFILTERS(FILTER(ALL(dCalendario[Data]), dCalendario[Data] >= EDATE(CALCULATE(MIN(fVenda[data]), REMOVEFILTERS()), 12)))) RETURN IF(NOT ISBLANK(a) && NOT ISBLANK(c), DIVIDE(c - a, a))', '+0.0%;-0.0%;0.0%')
ms('01 Vendas', 'Unidades AA', f'CALCULATE([Unidades], {SY})', '#,0')
ms('01 Vendas', 'Unidades Var %', 'VAR c = CALCULATE([Unidades], KEEPFILTERS(FILTER(ALL(dCalendario[Data]), dCalendario[Data] >= EDATE(CALCULATE(MIN(fVenda[data]), REMOVEFILTERS()), 12)))) VAR a = CALCULATE([Unidades AA], KEEPFILTERS(FILTER(ALL(dCalendario[Data]), dCalendario[Data] >= EDATE(CALCULATE(MIN(fVenda[data]), REMOVEFILTERS()), 12)))) RETURN IF(NOT ISBLANK(a) && NOT ISBLANK(c), DIVIDE(c - a, a))', '+0.0%;-0.0%;0.0%')
ms('01 Vendas', 'PDVs Monitorados', 'DISTINCTCOUNT(fVenda[pdv_id])', '#,0')
ms('01 Vendas', 'PDVs Cadastrados', 'COUNTROWS(dPDV)', '#,0')
ms('01 Vendas', 'Meta Receita (amostra)', 'SUM(fMeta[meta_receita])', '"R$" #,0')
ms('01 Vendas', 'Atingimento Meta (amostra) %', 'DIVIDE([Sell-out], [Meta Receita (amostra)])', '0.0%')
ms('02 Ruptura', 'Ruptura %', 'AVERAGE(fEstoque[ruptura])', '0.0%')
ms('02 Ruptura', 'Observações Estoque', 'COUNTROWS(fEstoque)', '#,0')
ms('02 Ruptura', 'Observações com Ruptura', 'SUM(fEstoque[ruptura])', '#,0')
ms('02 Ruptura', 'Ruptura AA', f'CALCULATE([Ruptura %], {SY})', '0.0%')
ms('02 Ruptura', 'Ruptura Var pp', 'VAR c = CALCULATE([Ruptura %], KEEPFILTERS(FILTER(ALL(dCalendario[Data]), dCalendario[Data] >= EDATE(CALCULATE(MIN(fVenda[data]), REMOVEFILTERS()), 12)))) VAR a = CALCULATE([Ruptura AA], KEEPFILTERS(FILTER(ALL(dCalendario[Data]), dCalendario[Data] >= EDATE(CALCULATE(MIN(fVenda[data]), REMOVEFILTERS()), 12)))) RETURN IF(NOT ISBLANK(a) && NOT ISBLANK(c), c - a)', '+0.00%;-0.00%')
ms('02 Ruptura', 'SKUs com Ruptura', 'CALCULATE(DISTINCTCOUNT(fEstoque[produto_id]), fEstoque[ruptura] = 1)', '#,0')
ms('03 Execução', 'Conformidade Checklist %', 'DIVIDE(AVERAGE(fVisita[checklist_pct]), 100)', '0.0%')
ms('03 Execução', 'Conformidade AA', f'CALCULATE([Conformidade Checklist %], {SY})', '0.0%')
ms('03 Execução', 'Conformidade Var pp', 'VAR c = CALCULATE([Conformidade Checklist %], KEEPFILTERS(FILTER(ALL(dCalendario[Data]), dCalendario[Data] >= EDATE(CALCULATE(MIN(fVenda[data]), REMOVEFILTERS()), 12)))) VAR a = CALCULATE([Conformidade AA], KEEPFILTERS(FILTER(ALL(dCalendario[Data]), dCalendario[Data] >= EDATE(CALCULATE(MIN(fVenda[data]), REMOVEFILTERS()), 12)))) RETURN IF(NOT ISBLANK(a) && NOT ISBLANK(c), c - a)', '+0.00%;-0.00%')
ms('03 Execução', 'Visitas', 'COUNTROWS(fVisita)', '#,0')
ms('03 Execução', 'Duração Média Visita (min)', 'AVERAGE(fVisita[duracao_min])', '0.0')
ms('03 Execução', 'Planograma OK %', 'AVERAGE(fAuditoria[planograma_ok])', '0.0%')
ms('03 Execução', 'Material PDV OK %', 'AVERAGE(fAuditoria[material_pdv_ok])', '0.0%')
ms('03 Execução', 'Índice Preço vs Concorrente', 'DIVIDE(SUM(fAuditoria[preco_gondola]), SUM(fAuditoria[preco_concorrente]))', '0.00')
ms('03 Execução', 'Auditorias', 'COUNTROWS(fAuditoria)', '#,0')
ms('04 Campanhas', 'Execução Campanha %', 'DIVIDE(AVERAGE(fExecCampanha[execucao_pct]), 100)', '0.0%')
ms('04 Campanhas', 'Custo Campanhas', 'SUM(fExecCampanha[custo])', '"R$" #,0')
ms('04 Campanhas', 'Orçamento Campanhas', 'SUM(dCampanha[orcamento])', '"R$" #,0')
ms('04 Campanhas', 'Custo por p.p. Execução', 'DIVIDE([Custo Campanhas], [Execução Campanha %] * 100)', '"R$" #,0')
ms('04 Campanhas', 'PDVs com Campanha', 'DISTINCTCOUNT(fExecCampanha[pdv_id])', '#,0')
# priorização
ms('05 Priorização', 'Índice Atenção', 'IF(NOT ISBLANK([Ruptura %]), [Ruptura %] * (1 - COALESCE([Conformidade Checklist %], 0.8)))', '0.0000')
ms('05 Priorização', 'Score Atenção', 'IF(NOT ISBLANK([Índice Atenção]), [Índice Atenção] * 1000)', '0.0')
ms('05 Priorização', 'Ruptura Média Geral', 'CALCULATE([Ruptura %], ALLSELECTED(dPDV))', '0.0%')
ms('05 Priorização', 'Prioridade', '''
VAR r = RANKX(ALLSELECTED(dPDV[pdv]), [Índice Atenção], , DESC)
RETURN IF(ISBLANK([Índice Atenção]), BLANK(), IF(r <= 10, "P1 · Alta", IF(r <= 40, "P2 · Média", "P3 · Monitorar")))''')
ms('05 Priorização', 'Ação Investigativa (hipótese)', '''
VAR ru = [Ruptura %] VAR ck = [Conformidade Checklist %] VAR mg = [Ruptura Média Geral]
RETURN IF(ISBLANK(ru), BLANK(),
    IF(ru > mg * 1.15, "Checar reposição e pedido",
    IF(ck < 0.8, "Revisar checklist com promotor",
    IF([Planograma OK %] < 0.6, "Auditar planograma", "Monitorar"))))''')

# ---------- SVG helpers ----------
def enc(svgvar): return f'"data:image/svg+xml;utf8," & SUBSTITUTE(SUBSTITUTE({svgvar}, "%", "%25"), "#", "%23")'
ICON = {
 'sales': "<path d='M8 26 L16 18 L22 22 L32 12' fill='none' stroke='COL' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><path d='M26 12 H32 V18' fill='none' stroke='COL' stroke-width='3' stroke-linecap='round'/>",
 'box': "<rect x='10' y='12' width='20' height='18' rx='3' fill='none' stroke='COL' stroke-width='3'/><path d='M10 18 H30' stroke='COL' stroke-width='3'/>",
 'check': "<path d='M10 21 L17 28 L30 13' fill='none' stroke='COL' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round'/>",
 'store': "<path d='M9 17 L12 10 H28 L31 17 Z' fill='none' stroke='COL' stroke-width='3' stroke-linejoin='round'/><rect x='11' y='17' width='18' height='13' fill='none' stroke='COL' stroke-width='3'/>",
 'units': "<rect x='9' y='9' width='10' height='10' rx='2' fill='none' stroke='COL' stroke-width='3'/><rect x='21' y='21' width='10' height='10' rx='2' fill='none' stroke='COL' stroke-width='3'/>",
 'doc': "<path d='M13 9 H24 L29 14 V31 H13 Z' fill='none' stroke='COL' stroke-width='3' stroke-linejoin='round'/><path d='M17 20 H25 M17 25 H25' stroke='COL' stroke-width='2.5'/>",
 'brain': "<circle cx='20' cy='20' r='10' fill='none' stroke='COL' stroke-width='3'/><circle cx='20' cy='20' r='3' fill='COL'/><path d='M20 6 V10 M20 30 V34 M6 20 H10 M30 20 H34' stroke='COL' stroke-width='3'/>",
 'shield': "<path d='M20 8 L30 12 V20 C30 26 25 30 20 32 C15 30 10 26 10 20 V12 Z' fill='none' stroke='COL' stroke-width='3' stroke-linejoin='round'/><path d='M15 20 L19 24 L25 16' fill='none' stroke='COL' stroke-width='3' stroke-linecap='round'/>",
 'pulse': "<path d='M6 20 H13 L16 12 L22 28 L25 20 H34' fill='none' stroke='COL' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>",
 'clock': "<circle cx='20' cy='20' r='11' fill='none' stroke='COL' stroke-width='3'/><path d='M20 14 V20 L24 23' stroke='COL' stroke-width='3' stroke-linecap='round'/>",
}
def icon(name, col, x, y): return f"<g transform='translate({x},{y})'><rect width='40' height='40' rx='12' fill='{col}' fill-opacity='0.12'/>" + ICON[name].replace('COL', col) + "</g>"

def kpi_svg(name, label, meas, valfmt, sub, delta, dfmt, higher_good, ic, col):
    good = '_d >= 0' if higher_good else '_d <= 0'
    expr = f'''
VAR _v = [{meas}]
VAR _txt = {valfmt}
VAR _d = {delta}
VAR _dtxt = IF(ISBLANK(_d), "sem base comparável", IF(_d >= 0, "▲ ", "▼ ") & {dfmt} & " vs ano ant.")
VAR _dcol = IF(ISBLANK(_d), "#64748B", IF({good}, "#16856A", "#C85B60"))
VAR _t = FILTER(TOPN(12, ADDCOLUMNS(VALUES(dCalendario[AnoMes]), "@v", [{meas}]), dCalendario[AnoMes], DESC), NOT ISBLANK([@v]))
VAR _n = COUNTROWS(_t) VAR _mn = MINX(_t, [@v]) VAR _mx = MAXX(_t, [@v])
VAR _pts = CONCATENATEX(_t,
    VAR i = RANKX(_t, dCalendario[AnoMes], , ASC)
    RETURN FORMAT(300 + (i - 1) * 150 / MAX(_n - 1, 1), "0") & "," & FORMAT(118 - DIVIDE([@v] - _mn, _mx - _mn, 0.5) * 46, "0"), " ", dCalendario[AnoMes], ASC)
VAR _spark = IF(_n >= 2, "<polyline points='" & _pts & "' fill='none' stroke='{col}' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/><text x='450' y='146' text-anchor='end' font-size='12' fill='#64748B'>últimos " & _n & " meses</text>", "")
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='470' height='160' viewBox='0 0 470 160' font-family='Segoe UI, sans-serif'>"
    & "<rect x='1' y='1' width='468' height='158' rx='16' fill='#FFFFFF' stroke='#E6EDF3'/>"
    & "{icon(ic, col, 20, 20)}"
    & "<text x='72' y='38' font-size='16' font-weight='600' fill='#1B3044'>{label}</text>"
    & "<text x='72' y='56' font-size='13' fill='#64748B'>" & {sub} & "</text>"
    & "<text x='22' y='112' font-size='38' font-weight='700' fill='#082746'>" & _txt & "</text>"
    & "<text x='22' y='142' font-size='14' font-weight='600' fill='" & _dcol & "'>" & _dtxt & "</text>"
    & _spark & "</svg>"
VAR _empty = "<svg xmlns='http://www.w3.org/2000/svg' width='470' height='160'><rect x='1' y='1' width='468' height='158' rx='16' fill='#F1F5F9' stroke='#E6EDF3'/><text x='235' y='86' text-anchor='middle' font-family='Segoe UI' font-size='16' fill='#64748B'>{label}: sem dados no contexto</text></svg>"
RETURN IF(ISBLANK(_v), {enc('_empty')}, {enc('_svg')})'''
    ms('90 SVG', name, expr, img=True)

kpi_svg('SVG KPI Sell-out', 'Sell-out monitorado', 'Sell-out', 'FORMAT(DIVIDE(_v, 1000000), "R$ #,0.00") & " mi"', '"amostra de SKUs monitorados"',
        '[Sell-out Var %]', 'FORMAT(ABS(_d), "0.0%")', True, 'sales', '#06436E')
kpi_svg('SVG KPI Unidades', 'Unidades na amostra', 'Unidades', 'FORMAT(DIVIDE(_v, 1000), "#,0.0") & " mil"', '"unidades vendidas (amostra)"',
        '[Unidades Var %]', 'FORMAT(ABS(_d), "0.0%")', True, 'units', '#4387AD')
kpi_svg('SVG KPI Ruptura', 'Ruptura semanal observada', 'Ruptura %', 'FORMAT(_v, "0.0%")', 'FORMAT([Observações Estoque], "#,0") & " obs. PDV×SKU"',
        '[Ruptura Var pp]', 'FORMAT(ABS(_d) * 100, "0.00") & " p.p."', False, 'box', '#F58200')
kpi_svg('SVG KPI Conformidade', 'Conformidade de execução', 'Conformidade Checklist %', 'FORMAT(_v, "0.0%")', 'FORMAT([Visitas], "#,0") & " visitas com checklist"',
        '[Conformidade Var pp]', 'FORMAT(ABS(_d) * 100, "0.00") & " p.p."', True, 'check', '#16856A')
kpi_svg('SVG KPI PDVs', 'PDVs monitorados', 'PDVs Monitorados', 'FORMAT(_v, "#,0")', '"de " & FORMAT([PDVs Cadastrados], "#,0") & " PDVs cadastrados"',
        'BLANK()', '""', True, 'store', '#082746')

def mini_svg(name, label, valexpr, subexpr, ic, col, w=440, h=120):
    expr = f'''
VAR _txt = {valexpr}
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}' font-family='Segoe UI, sans-serif'>"
    & "<rect x='1' y='1' width='{w-2}' height='{h-2}' rx='16' fill='#FFFFFF' stroke='#E6EDF3'/>"
    & "{icon(ic, col, 18, 18)}"
    & "<text x='70' y='36' font-size='15' font-weight='600' fill='#1B3044'>{label}</text>"
    & "<text x='70' y='{h-46}' font-size='32' font-weight='700' fill='#082746'>" & COALESCE(_txt, "—") & "</text>"
    & "<text x='70' y='{h-20}' font-size='13' fill='#64748B'>" & {subexpr} & "</text></svg>"
RETURN {enc('_svg')}'''
    ms('90 SVG', name, expr, img=True)

# contexto de filtros (barra) ------------------------------------------
FIELDS = [('PERÍODO', None), ('INDÚSTRIA', 'dProduto[industria]'), ('REDE', 'dPDV[rede]'), ('REGIÃO', 'dPDV[regiao]'), ('ESTADO', 'dPDV[uf]'),
          ('PDV', 'dPDV[pdv]'), ('CATEGORIA', 'dProduto[categoria]'), ('PRODUTO', 'dProduto[produto]'), ('PROMOTOR', 'dPromotor[promotor]'), ('CAMPANHA', 'dCampanha[campanha]')]
def fx(col):
    return (f'IF(ISFILTERED({col}), VAR n = COUNTROWS(VALUES({col})) RETURN IF(n = 1, SELECTEDVALUE({col}), FORMAT(n, "0") & " selecionados"), '
            f'IF(ISCROSSFILTERED({col}) && COUNTROWS(VALUES({col})) < CALCULATE(COUNTROWS(VALUES({col})), ALL({col})), FORMAT(COUNTROWS(VALUES({col})), "0") & " (via filtros)", "Todos"))')
ms('00 Contexto', 'Filtros Ativos', ' + '.join(f'INT(ISFILTERED({c}))' for _, c in FIELDS if c) + ' + INT(ISFILTERED(dCalendario[Data]) || ISFILTERED(dCalendario[Ano]) || ISFILTERED(dCalendario[MesAno]))', '0')
per = 'IF(ISBLANK(MIN(dCalendario[Data])), "Sem período", FORMAT(MIN(dCalendario[Data]), "dd/mm/yy") & " – " & FORMAT(MAX(dCalendario[Data]), "dd/mm/yy"))'
vars_ = [f'VAR v0 = {per}'] + [f'VAR v{i} = {fx(c)}' for i, (_, c) in enumerate(FIELDS) if c]
chips = []
slots = [(16, 230), (256, 160), (426, 150), (586, 150), (746, 120), (876, 170), (1056, 150), (1216, 170), (1396, 160), (1566, 170)]
for i, ((lab, _), (x, wd)) in enumerate(zip(FIELDS, slots)):
    maxc = int((wd - 14 - len(lab) * 7.2) / 7.4)
    chips.append(f'''"<g><rect x='{x}' y='7' width='{wd - 8}' height='30' rx='15' fill='" & IF(v{i} = "Todos", "#F1F5F9", "#FFF4E5") & "' stroke='" & IF(v{i} = "Todos", "#E6EDF3", "#FFA51B") & "'/>"
    & "<text x='{x + 12}' y='27' font-size='11' font-weight='700' fill='#64748B' letter-spacing='0.6'>{lab}</text>"
    & "<text x='{x + 18 + int(len(lab) * 7.4)}' y='27' font-size='13' font-weight='600' fill='#1B3044'>" & IF(LEN(v{i}) > {maxc}, LEFT(v{i}, {maxc - 1}) & "…", v{i}) & "</text></g>"''')
ctx = '\n'.join(vars_) + f'''
VAR nf = [Filtros Ativos]
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='1872' height='44' viewBox='0 0 1872 44' font-family='Segoe UI, sans-serif'>"
    & "<rect x='0.5' y='0.5' width='1871' height='43' rx='14' fill='#FFFFFF' fill-opacity='0.92' stroke='#E6EDF3'/>"
    & {' & '.join(chips)}
    & "<rect x='1748' y='7' width='112' height='30' rx='15' fill='" & IF(nf > 0, "#082746", "#E6EDF3") & "'/>"
    & "<text x='1804' y='27' text-anchor='middle' font-size='13' font-weight='700' fill='" & IF(nf > 0, "#FFFFFF", "#64748B") & "'>" & IF(nf = 0, "Sem filtros", nf & IF(nf = 1, " filtro", " filtros")) & "</text></svg>"
RETURN {enc('_svg')}'''
ms('90 SVG', 'SVG Barra Contexto', ctx, img=True)
ms('00 Contexto', 'Atualização Dados', '"Dados até " & FORMAT(CALCULATE(MAX(fVenda[data]), ALL(fVenda), ALL(dCalendario)), "dd/mm/yyyy") & " · simulado"')
ms('00 Contexto', 'Período Selecionado', per)
ms('00 Contexto', 'Contexto Texto', 'VAR p = ' + per + ' VAR r = ' + fx('dPDV[regiao]') + ' VAR d = ' + fx('dPDV[rede]') + ' VAR i = ' + fx('dProduto[industria]') + ' VAR c = ' + fx('dProduto[categoria]') + ' VAR pd = ' + fx('dPDV[pdv]') + ' RETURN "Período " & p & " · Região " & r & " · Rede " & d & " · Indústria " & i & " · Categoria " & c & " · PDV " & pd')
ms('00 Contexto', 'Título Detalhe PDV', 'IF(HASONEVALUE(dPDV[pdv]), SELECTEDVALUE(dPDV[pdv]) & " · " & SELECTEDVALUE(dPDV[rede]) & " · " & SELECTEDVALUE(dPDV[cidade]) & "/" & SELECTEDVALUE(dPDV[uf]), "Selecione um PDV (botão direito › Detalhar › Detalhe do PDV)")')
ms('07 IA', 'Ocorrências PDV (sintéticas)', 'COUNTROWS(fOcorrenciasPDV)', '#,0')
ms('90 SVG', 'SVG Usuário RLS', '''
VAR upn = USERPRINCIPALNAME()
VAR pf = LOOKUPVALUE(dUsuarioAcesso[perfil], dUsuarioAcesso[upn], upn)
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='600' height='40' viewBox='0 0 600 40' font-family='Segoe UI'><rect x='0' y='4' width='590' height='32' rx='16' fill='#082746' fill-opacity='0.06'/><text x='16' y='25' font-size='13' fill='#1B3044'><tspan font-weight='700'>Identidade no modelo: </tspan>" & upn & " · perfil RLS: " & COALESCE(pf, "não mapeado (sem papel aplicado no Desktop)") & "</text></svg>"
RETURN ''' + enc('_svg'), img=True)

# células SVG ---------------------------------------------------------
ms('90 SVG', 'SVG Barra Ruptura', '''
VAR r = [Ruptura %] VAR mg = [Ruptura Média Geral]
VAR w = MIN(DIVIDE(r, 0.15) * 150, 150)
VAR c = IF(r > mg * 1.15, "#C85B60", IF(r > mg, "#D99528", "#16856A"))
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='230' height='28' font-family='Segoe UI'><rect x='0' y='9' width='150' height='10' rx='5' fill='#F1F5F9'/><rect x='0' y='9' width='" & FORMAT(w, "0") & "' height='10' rx='5' fill='" & c & "'/><text x='160' y='19' font-size='13' font-weight='600' fill='#1B3044'>" & FORMAT(r, "0.0%") & "</text></svg>"
RETURN IF(ISBLANK(r), BLANK(), ''' + enc('_svg') + ')', img=True)
ms('90 SVG', 'SVG Barra Conformidade', '''
VAR r = [Conformidade Checklist %]
VAR c = IF(r < 0.8, "#C85B60", IF(r < 0.88, "#D99528", "#16856A"))
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='230' height='28' font-family='Segoe UI'><rect x='0' y='9' width='150' height='10' rx='5' fill='#F1F5F9'/><rect x='0' y='9' width='" & FORMAT(r * 150, "0") & "' height='10' rx='5' fill='" & c & "'/><text x='160' y='19' font-size='13' font-weight='600' fill='#1B3044'>" & FORMAT(r, "0.0%") & "</text></svg>"
RETURN IF(ISBLANK(r), BLANK(), ''' + enc('_svg') + ')', img=True)
ms('90 SVG', 'SVG Status Atenção', '''
VAR r = [Ruptura %] VAR mg = [Ruptura Média Geral]
VAR s = IF(r > mg * 1.15, "Crítico", IF(r > mg, "Atenção", "Normal"))
VAR c = SWITCH(s, "Crítico", "#C85B60", "Atenção", "#D99528", "#16856A")
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='120' height='28' font-family='Segoe UI'><rect x='1' y='3' width='112' height='22' rx='11' fill='" & c & "' fill-opacity='0.14'/><circle cx='16' cy='14' r='5' fill='" & c & "'/><text x='28' y='19' font-size='13' font-weight='600' fill='" & c & "'>" & s & "</text></svg>"
RETURN IF(ISBLANK(r), BLANK(), ''' + enc('_svg') + ')', img=True)
ms('90 SVG', 'SVG Tendência Ruptura', '''
VAR d = [Ruptura Var pp]
VAR c = IF(d > 0, "#C85B60", "#16856A")
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='120' height='28' font-family='Segoe UI'><text x='0' y='19' font-size='13' font-weight='700' fill='" & c & "'>" & IF(d > 0, "▲ ", "▼ ") & FORMAT(ABS(d) * 100, "0.00") & " p.p.</text></svg>"
RETURN IF(ISBLANK(d), BLANK(), ''' + enc('_svg') + ')', img=True)
ms('90 SVG', 'SVG Sparkline Sell-out', '''
VAR _t = FILTER(TOPN(12, ADDCOLUMNS(VALUES(dCalendario[AnoMes]), "@v", [Sell-out]), dCalendario[AnoMes], DESC), NOT ISBLANK([@v]))
VAR _n = COUNTROWS(_t) VAR _mn = MINX(_t, [@v]) VAR _mx = MAXX(_t, [@v])
VAR _pts = CONCATENATEX(_t, VAR i = RANKX(_t, dCalendario[AnoMes], , ASC) RETURN FORMAT(4 + (i - 1) * 152 / MAX(_n - 1, 1), "0") & "," & FORMAT(30 - DIVIDE([@v] - _mn, _mx - _mn, 0.5) * 24, "0"), " ", dCalendario[AnoMes], ASC)
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='160' height='34'><polyline points='" & _pts & "' fill='none' stroke='#06436E' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'/></svg>"
RETURN IF(_n < 2, BLANK(), ''' + enc('_svg') + ')', img=True)
ms('90 SVG', 'SVG Variação Sell-out', '''
VAR d = [Sell-out Var %]
VAR c = IF(d >= 0, "#16856A", "#C85B60")
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='110' height='28' font-family='Segoe UI'><rect x='1' y='3' width='100' height='22' rx='11' fill='" & c & "' fill-opacity='0.12'/><text x='51' y='19' text-anchor='middle' font-size='13' font-weight='700' fill='" & c & "'>" & IF(d >= 0, "▲ ", "▼ ") & FORMAT(ABS(d), "0.0%") & "</text></svg>"
RETURN IF(ISBLANK(d), BLANK(), ''' + enc('_svg') + ')', img=True)
ms('90 SVG', 'SVG Heat Ruptura', '''
VAR r = [Ruptura %] VAR mg = [Ruptura Média Geral]
VAR k = DIVIDE(r - mg * 0.85, mg * 0.3)
VAR op = FORMAT(MAX(MIN(k, 1), 0.08) * 0.85, "0.00", "en-US")
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='150' height='34' font-family='Segoe UI'><rect x='2' y='2' width='146' height='30' rx='8' fill='#F58200' fill-opacity='" & op & "'/><text x='75' y='22' text-anchor='middle' font-size='13' font-weight='700' fill='#1B3044'>" & FORMAT(r, "0.0%") & "</text></svg>"
RETURN IF(ISBLANK(r), BLANK(), ''' + enc('_svg') + ')', img=True)

# insight calculado ---------------------------------------------------
ms('06 Insight', 'Insight Região Crítica', '''
VAR t = ADDCOLUMNS(FILTER(VALUES(dPDV[regiao]), NOT ISBLANK([Ruptura %])), "@r", [Ruptura %])
RETURN MAXX(TOPN(1, t, [@r], DESC), dPDV[regiao])''')
ms('90 SVG', 'SVG Insight', '''
VAR reg = [Insight Região Crítica]
VAR t = ADDCOLUMNS(FILTER(VALUES(dPDV[regiao]), NOT ISBLANK([Ruptura %])), "@r", [Ruptura %])
VAR rr = MAXX(TOPN(1, t, [@r], DESC), [@r]) VAR av = [Ruptura %]
VAR tc = ADDCOLUMNS(FILTER(VALUES(dProduto[categoria]), NOT ISBLANK([Ruptura %])), "@r", [Ruptura %])
VAR cat = MAXX(TOPN(1, tc, [@r], DESC), dProduto[categoria]) VAR cr = MAXX(TOPN(1, tc, [@r], DESC), [@r])
VAR np = CALCULATE(COUNTROWS(FILTER(VALUES(dPDV[pdv]), [Ruptura %] > av * 1.15)))
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='740' height='300' viewBox='0 0 740 300' font-family='Segoe UI, sans-serif'>"
 & "<rect x='1' y='1' width='738' height='298' rx='18' fill='#082746'/>"
 & "<circle cx='690' cy='40' r='120' fill='#06436E' fill-opacity='0.55'/><circle cx='700' cy='260' r='70' fill='#F58200' fill-opacity='0.18'/>"
 & "<text x='32' y='46' font-size='13' font-weight='700' fill='#FFA51B' letter-spacing='1.6'>INSIGHT DO PERÍODO · REGRA DAX AUDITÁVEL</text>"
 & "<text x='32' y='96' font-size='26' font-weight='700' fill='#FFFFFF'>Maior ruptura observada: " & reg & "</text>"
 & "<text x='32' y='136' font-size='17' fill='#DCE6F0'>" & FORMAT(rr, "0.0%") & " na região vs " & FORMAT(av, "0.0%") & " na média do contexto</text>"
 & "<text x='32' y='170' font-size='17' fill='#DCE6F0'>Categoria mais afetada: " & cat & " (" & FORMAT(cr, "0.0%") & ")</text>"
 & "<text x='32' y='204' font-size='17' fill='#DCE6F0'>" & FORMAT(np, "0") & " PDVs acima de 115% da média — candidatos a investigação</text>"
 & "<text x='32' y='262' font-size='13' fill='#9FB3C8'>Hipóteses, não causas comprovadas. Dados simulados.</text></svg>"
RETURN IF(ISBLANK(av), BLANK(), ''' + enc('_svg') + ')', img=True)

# IA ---------------------------------------------------------------------
ms('07 IA', 'RAG Taxa Aprovação', 'AVERAGE(fAvaliacoesLLM[aprovado])', '0.0%')
ms('07 IA', 'RAG Avaliações', 'COUNTROWS(fAvaliacoesLLM)', '0')
ms('07 IA', 'RAG Latência Média (ms)', 'AVERAGE(fAvaliacoesLLM[latencia_ms])', '0.0')
ms('07 IA', 'RAG Documentos Indexados', 'COUNTROWS(dDocumento)', '0')
ms('07 IA', 'RAG Sem Evidência', 'CALCULATE(COUNTROWS(fAvaliacoesLLM), fAvaliacoesLLM[status] = "sem_evidencia")', '0')
ms('07 IA', 'GR Testes', 'COUNTROWS(fTestesGuardrails)', '0')
ms('07 IA', 'GR Bloqueados', 'CALCULATE(COUNTROWS(fTestesGuardrails), fTestesGuardrails[resultado_obtido] <> "permitido")', '0')
ms('07 IA', 'GR Falhas', 'CALCULATE(COUNTROWS(fTestesGuardrails), fTestesGuardrails[status] = "Falha de segurança")', '0')
ms('07 IA', 'GR Taxa Bloqueio', 'DIVIDE([GR Bloqueados], [GR Testes])', '0.0%')
ms('07 IA', 'GR Taxa Sucesso', 'DIVIDE([GR Testes] - [GR Falhas], [GR Testes])', '0.0%')
def expv(model, metric): return f'VAR ts = CALCULATE(MAX(fExperimentosML[timestamp]), ALL(fExperimentosML)) RETURN CALCULATE(MAX(fExperimentosML[valor]), fExperimentosML[modelo] = "{model}", fExperimentosML[metrica] = "{metric}", fExperimentosML[timestamp] = ts)'
ms('07 IA', 'FT Macro F1 Especializado', expv('classificador-ocorrencias-tfidf-lr', 'macro_f1'), '0.000')
ms('07 IA', 'FT Macro F1 Base', expv('baseline-regras-palavra-chave', 'macro_f1'), '0.000')
ms('07 IA', 'FT Accuracy Especializado', expv('classificador-ocorrencias-tfidf-lr', 'accuracy'), '0.0%')
ms('07 IA', 'FT Accuracy Base', expv('baseline-regras-palavra-chave', 'accuracy'), '0.0%')
ms('07 IA', 'FT Casos Teste', 'COUNTROWS(fComparadorModelos)', '0')
ms('07 IA', 'Métrica Experimento', 'IF(HASONEVALUE(fExperimentosML[metrica]), MAX(fExperimentosML[valor]))', '0.000')
ms('07 IA', 'ML AUC Ruptura', expv('risco-ruptura-logreg', 'auc'), '0.000')
ms('07 IA', 'ML Experimentos', 'DISTINCTCOUNT(fExperimentosML[experimento])', '0')
ms('07 IA', 'ML Registros Métricas', 'COUNTROWS(fExperimentosML)', '0')
ms('07 IA', 'ML Última Execução', 'FORMAT(MAX(fExperimentosML[timestamp]), "")')
ms('07 IA', 'ML Modelos Registrados', 'COUNTROWS(dModelosIA)', '0')
ms('07 IA', 'Prob Prevista Média', 'AVERAGE(fMonitorRuptura[prob_media_prevista])', '0.0%')
ms('07 IA', 'Taxa Observada Teste', 'AVERAGE(fMonitorRuptura[taxa_observada])', '0.0%')
ms('07 IA', 'Ocorrências Sintéticas', 'COUNTROWS(fOcorrenciasPDV)', '#,0')
ms('90 SVG', 'SVG Status Teste', '''
VAR s = SELECTEDVALUE(fTestesGuardrails[status], "Não executado")
VAR c = SWITCH(s, "Aprovado", "#16856A", "Bloqueado corretamente", "#4387AD", "Falha de segurança", "#C85B60", "#64748B")
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='220' height='28' font-family='Segoe UI'><rect x='1' y='3' width='210' height='22' rx='11' fill='" & c & "' fill-opacity='0.14'/><circle cx='16' cy='14' r='5' fill='" & c & "'/><text x='28' y='19' font-size='13' font-weight='600' fill='" & c & "'>" & s & "</text></svg>"
RETURN ''' + enc('_svg'), img=True)
def _tt(): pass
def okicon(name, col):
    ms('90 SVG', name, f'''
VAR v = MAX({col})
VAR c = IF(v = 1, "#16856A", "#C85B60")
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='110' height='28' font-family='Segoe UI'><circle cx='14' cy='14' r='10' fill='" & c & "' fill-opacity='0.15'/><text x='14' y='19' text-anchor='middle' font-size='13' font-weight='700' fill='" & c & "'>" & IF(v = 1, "✓", "✕") & "</text><text x='32' y='19' font-size='13' fill='" & c & "'>" & IF(v = 1, "Correto", "Incorreto") & "</text></svg>"
RETURN IF(ISBLANK(v), BLANK(), ''' + enc('_svg') + ')', img=True)
okicon('SVG Acerto Base', 'fComparadorModelos[acerto_base]')
okicon('SVG Acerto Especializado', 'fComparadorModelos[acerto_especializado]')
okicon('SVG Aprovado RAG', 'fAvaliacoesLLM[aprovado]')
ms('90 SVG', 'SVG Status Modelo', '''
VAR s = SELECTEDVALUE(dModelosIA[status])
VAR c = SWITCH(s, "Ativo", "#16856A", "Treinado", "#16856A", "Referência", "#4387AD", "Rejeitado", "#C85B60", "#D99528")
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='200' height='28' font-family='Segoe UI'><rect x='1' y='3' width='190' height='22' rx='11' fill='" & c & "' fill-opacity='0.14'/><circle cx='16' cy='14' r='5' fill='" & c & "'/><text x='28' y='19' font-size='13' font-weight='600' fill='" & c & "'>" & s & "</text></svg>"
RETURN IF(ISBLANK(s), BLANK(), ''' + enc('_svg') + ')', img=True)

def aicard(name, title, sub, statusexpr, metricexpr, ic, col):
    ms('90 SVG', name, f'''
VAR st = {statusexpr}
VAR mt = {metricexpr}
VAR sc = IF(CONTAINSSTRING(st, "pendente") || CONTAINSSTRING(st, "Rejeitado"), "#D99528", "#16856A")
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='440' height='170' viewBox='0 0 440 170' font-family='Segoe UI, sans-serif'>"
 & "<rect x='1' y='1' width='438' height='168' rx='16' fill='#FFFFFF' stroke='#E6EDF3'/>"
 & "{icon(ic, col, 20, 20)}"
 & "<text x='72' y='38' font-size='18' font-weight='700' fill='#082746'>{title}</text>"
 & "<text x='72' y='58' font-size='13' fill='#64748B'>{sub}</text>"
 & "<rect x='20' y='78' width='" & FORMAT(LEN(st) * 7.4 + 30, "0") & "' height='26' rx='13' fill='" & sc & "' fill-opacity='0.13'/><circle cx='34' cy='91' r='4.5' fill='" & sc & "'/>"
 & "<text x='46' y='96' font-size='13' font-weight='600' fill='" & sc & "'>" & st & "</text>"
 & "<text x='20' y='136' font-size='15' font-weight='600' fill='#1B3044'>" & mt & "</text>"
 & "<text x='420' y='156' text-anchor='end' font-size='13' font-weight='700' fill='#F58200'>Abrir módulo →</text></svg>"
RETURN {enc('_svg')}''', img=True)
aicard('SVG Card RAG', 'RAG', 'Conhecimento e evidências', '"Ativo · API local"',
       '"Aprovação nas avaliações: " & FORMAT([RAG Taxa Aprovação], "0%") & " · " & [RAG Documentos Indexados] & " docs"', 'doc', '#06436E')
aicard('SVG Card FT', 'FINE-TUNING', 'Especialização e classificação', '"Classificador treinado · LLM pendente"',
       '"Macro-F1: " & FORMAT([FT Macro F1 Especializado], "0.00") & " vs base " & FORMAT([FT Macro F1 Base], "0.00")', 'brain', '#F58200')
aicard('SVG Card GR', 'GUARDRAILS', 'Segurança e governança', '"Ativo · " & [GR Testes] & " testes executados"',
       '"Sucesso nos testes: " & FORMAT([GR Taxa Sucesso], "0%") & " · " & ([GR Falhas] + 0) & " falhas"', 'shield', '#16856A')
aicard('SVG Card ML', 'MLOPS / LLMOPS', 'Qualidade e monitoramento', '"Ativo · " & [ML Modelos Registrados] & " modelos registrados"',
       '[ML Registros Métricas] & " métricas · " & [ML Experimentos] & " experimentos"', 'pulse', '#4387AD')
mini_svg('SVG RAG Aprovação', 'Aprovação nas avaliações', 'FORMAT([RAG Taxa Aprovação], "0.0%")', '[RAG Avaliações] & " perguntas de teste"', 'check', '#16856A')
mini_svg('SVG RAG Latência', 'Latência média', 'FORMAT([RAG Latência Média (ms)], "0.0") & " ms"', '"recuperação local TF-IDF"', 'clock', '#4387AD')
mini_svg('SVG RAG Docs', 'Documentos indexados', 'FORMAT([RAG Documentos Indexados], "0")', 'FORMAT(CALCULATE(COUNTROWS(dDocumento), dDocumento[origem] = "original"), "0") & " originais + " & FORMAT(CALCULATE(COUNTROWS(dDocumento), dDocumento[origem] = "complementar-projeto"), "0") & " complementares do projeto"', 'doc', '#06436E')
mini_svg('SVG RAG SemEv', 'Sem evidência declarada', 'FORMAT([RAG Sem Evidência] + 0, "0")', '"respostas recusadas por falta de fonte"', 'shield', '#F58200')
mini_svg('SVG FT F1', 'Macro-F1 especializado', 'FORMAT([FT Macro F1 Especializado], "0.000")', '"base por regras: " & FORMAT([FT Macro F1 Base], "0.000")', 'brain', '#F58200')
mini_svg('SVG FT Acc', 'Accuracy especializado', 'FORMAT([FT Accuracy Especializado], "0.0%")', '"base por regras: " & FORMAT([FT Accuracy Base], "0.0%")', 'check', '#16856A')
mini_svg('SVG FT Casos', 'Casos de teste', 'FORMAT([FT Casos Teste], "0")', '"split por template, sem vazamento"', 'units', '#4387AD')
mini_svg('SVG FT LLM', 'Fine-tuning de LLM', '"Pendente"', '"dataset JSONL pronto; sem infraestrutura"', 'clock', '#D99528')
mini_svg('SVG GR Testes', 'Requisições avaliadas', 'FORMAT([GR Testes], "0")', '"cenários executados no backend"', 'shield', '#06436E')
mini_svg('SVG GR Bloq', 'Bloqueadas / restritas', 'FORMAT([GR Bloqueados], "0")', '"taxa de bloqueio " & FORMAT([GR Taxa Bloqueio], "0%")', 'box', '#F58200')
mini_svg('SVG GR Sucesso', 'Testes bem-sucedidos', 'FORMAT([GR Taxa Sucesso], "0%")', 'FORMAT([GR Falhas] + 0, "0") & " falhas de segurança"', 'check', '#16856A')
mini_svg('SVG GR Lat', 'Última execução', 'FORMAT(MAX(fTestesGuardrails[timestamp]), "")', '"03_AI/run_pipeline.py"', 'clock', '#4387AD')
mini_svg('SVG ML Modelos', 'Modelos registrados', 'FORMAT([ML Modelos Registrados], "0")', '"inclui referência e pendentes"', 'brain', '#06436E')
mini_svg('SVG ML Exp', 'Métricas registradas', 'FORMAT([ML Registros Métricas], "0")', '[ML Experimentos] & " experimentos"', 'pulse', '#4387AD')
mini_svg('SVG ML AUC', 'AUC risco de ruptura', 'FORMAT([ML AUC Ruptura], "0.000")', '"≈0,50: sem sinal · modelo rejeitado"', 'box', '#C85B60')
mini_svg('SVG ML Ult', 'Última execução', '[ML Última Execução]', '"pipeline local, sem agendamento"', 'clock', '#F58200')

# measure table
L = ['table _Medidas', f'\tlineageTag: {lt("_Medidas")}', '']
for folder, name, expr, fmt, img in M:
    L.append(f"\tmeasure {q(name)} = ```")
    for line in expr.split('\n'): L.append('\t\t\t' + line)
    L.append('\t\t\t```')
    if fmt: L.append(f'\t\tformatString: {fmt}')
    if img: L.append('\t\tdataCategory: ImageUrl')
    L += [f'\t\tdisplayFolder: {folder}', f'\t\tlineageTag: {lt("m" + name)}', '']
L += ['\tcolumn Coluna', '\t\tdataType: string', '\t\tisHidden', f'\t\tlineageTag: {lt("mcol")}', '\t\tsummarizeBy: none', '\t\tsourceColumn: Coluna', '',
      '\tpartition _Medidas = m', '\t\tmode: import', '\t\tsource = #table(type table [Coluna = text], {})', '']
tbl_files['_Medidas'] = '\n'.join(L)

REL = []
for f in ['fVenda', 'fEstoque', 'fVisita', 'fAuditoria', 'fExecCampanha', 'fMeta', 'fOcorrenciasPDV']:
    REL += [(f, 'data', 'dCalendario', 'Data'), (f, 'pdv_id', 'dPDV', 'pdv_id')]
for f in ['fVenda', 'fEstoque', 'fAuditoria']: REL.append((f, 'produto_id', 'dProduto', 'produto_id'))
for f in ['fVisita', 'fAuditoria']: REL.append((f, 'promotor_id', 'dPromotor', 'promotor_id'))
REL.append(('fExecCampanha', 'campanha_id', 'dCampanha', 'campanha_id'))
REL.append(('fRecuperacaoRAG', 'interacao_id', 'fAvaliacoesLLM', 'interacao_id'))
rel = '\n'.join(f'relationship {lt(a + b + c)}\n\tfromColumn: {a}.{b}\n\ttoColumn: {c}.{d}\n' for a, b, c, d in REL)

D = SM / 'definition'
wt(D / 'database.tmdl', 'database\n\tcompatibilityLevel: 1600\n')
wt(D / 'model.tmdl', 'model Model\n\tculture: pt-BR\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tdiscourageImplicitMeasures\n\tsourceQueryCulture: pt-BR\n\n'
   + '\n'.join(f'ref table {q(t)}' for t in ['_Medidas'] + TABLES) + '\n')
wt(D / 'expressions.tmdl', f'expression PastaDados = "{WIN_DATA.replace(chr(92), chr(92))}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n\tlineageTag: {lt("PastaDados")}\n')
wt(D / 'relationships.tmdl', rel)
for t, s in tbl_files.items(): wt(D / 'tables' / f'{t}.tmdl', s)
wj(SM / 'definition.pbism', {'version': '4.0', 'settings': {}})
wj(SM / '.platform', {'$schema': 'https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json',
                      'metadata': {'type': 'SemanticModel', 'displayName': NAME}, 'config': {'version': '2.0', 'logicalId': lt('sm')}})

# ============================ REPORT ============================
NAVY, BLUE, ORANGE, LORANGE, GRAPH = '#082746', '#06436E', '#F58200', '#FFA51B', '#464646'
TP, TS, BORDER, SURF = '#1B3044', '#64748B', '#E6EDF3', '#FFFFFF'
def L_(v):
    if isinstance(v, bool): return {'expr': {'Literal': {'Value': 'true' if v else 'false'}}}
    if isinstance(v, (int, float)): return {'expr': {'Literal': {'Value': f'{v}D'}}}
    return {'expr': {'Literal': {'Value': "'" + v.replace("'", "''") + "'"}}}
def C_(hexc): return {'solid': {'color': L_(hexc)}}
def fld(ref):
    t, n = ref.split('.', 1)
    if t == 'M': return {'Measure': {'Expression': {'SourceRef': {'Entity': '_Medidas'}}, 'Property': n}}, f'_Medidas.{n}', n
    return {'Column': {'Expression': {'SourceRef': {'Entity': t}}, 'Property': n}}, f'{t}.{n}', n
def proj(ref, name=None):
    f, qr, nq = fld(ref); p = {'field': f, 'queryRef': qr, 'nativeQueryRef': nq}
    if name is not None: p['displayName'] = name
    return p
def container(title=None, bg=None, border=False, radius=14, pad=0):
    o = {'background': [{'properties': {'show': L_(bg is not None)} | ({'color': C_(bg), 'transparency': L_(0)} if bg else {})}],
         'border': [{'properties': {'show': L_(border)} | ({'color': C_(BORDER), 'radius': L_(radius)} if border else {})}],
         'dropShadow': [{'properties': {'show': L_(False)}}],
         'padding': [{'properties': {'top': L_(pad), 'bottom': L_(pad), 'left': L_(pad), 'right': L_(pad)}}],
         'visualHeader': [{'properties': {'show': L_(False)}}]}
    o['title'] = [{'properties': {'show': L_(bool(title))} | ({'text': L_(title), 'fontColor': C_(TP), 'fontSize': L_(14), 'bold': L_(True), 'fontFamily': L_('Segoe UI Semibold')} if title else {})}]
    return o

class Page:
    def __init__(s, name, disp, bg=None, w=1920, h=1080, hidden=False, tooltip=False):
        s.name, s.disp, s.bg, s.w, s.h, s.hidden, s.tooltip = name, disp, bg, w, h, hidden, tooltip; s.v = {}; s.z = 0
    def add(s, vid, x, y, w, h, visual, hidden=False, cobj=None):
        s.z += 1
        vc = {'$schema': f'{SCH}/visualContainer/2.0.0/schema.json', 'name': vid,
              'position': {'x': x, 'y': y, 'z': s.z * 1000, 'width': w, 'height': h, 'tabOrder': s.z * 1000}, 'visual': visual}
        visual.setdefault('visualContainerObjects', container())
        if cobj: visual['visualContainerObjects'].update(cobj)
        visual.setdefault('drillFilterOtherVisuals', True)
        if hidden: vc['isHidden'] = True
        s.v[vid] = vc; return vid
PAGES = []

def DEF(objs):
    for k, lst in objs.items():
        extra = []
        for e in lst:
            if 'selector' in e: continue
            e['selector'] = {'id': 'default'}
            if 'show' in e['properties']: extra.append({'properties': {'show': e['properties'].pop('show')}})
        lst.extend(extra)
    return objs
def shape(p, vid, x, y, w, h, fill=SURF, alpha=0, radius=18, stroke=BORDER, hidden=False):
    return p.add(vid, x, y, w, h, {'visualType': 'shape', 'objects': DEF({
        'shape': [{'properties': {'tileShape': L_('rectangleRounded'), 'roundEdge': L_(radius)}}],
        'fill': [{'properties': {'show': L_(True), 'fillColor': C_(fill), 'transparency': L_(alpha)}}],
        'outline': [{'properties': {'show': L_(stroke is not None)} | ({'lineColor': C_(stroke), 'weight': L_(1)} if stroke else {})}]})}, hidden)
def text(p, vid, x, y, w, h, runs, align='left', hidden=False):
    paras = []
    for r in runs:
        t, size, col, bold = (list(r) + [False])[:4]
        paras.append({'textRuns': [{'value': t, 'textStyle': {'fontFamily': 'Segoe UI', 'fontSize': f'{size}pt', 'color': col} | ({'fontWeight': 'bold'} if bold else {})}],
                      'horizontalTextAlignment': align})
    return p.add(vid, x, y, w, h, {'visualType': 'textbox', 'objects': {'general': [{'properties': {'paragraphs': paras}}]}}, hidden)
def image(p, vid, x, y, w, h, item):
    return p.add(vid, x, y, w, h, {'visualType': 'image', 'objects': {
        'general': [{'properties': {'imageUrl': {'expr': {'ResourcePackageItem': {'PackageName': 'RegisteredResources', 'PackageType': 1, 'ItemName': item}}}}}],
        'imageScaling': [{'properties': {'imageScalingType': L_('Fit')}}]}})
def button(p, vid, x, y, w, h, label, action, target, style='ghost', hidden=False, size=12, tooltip=None):
    fill, fc, line, alpha = {'primary': (ORANGE, SURF, ORANGE, 0), 'navy': (NAVY, SURF, NAVY, 0), 'ghost': (SURF, NAVY, BORDER, 0),
                             'active': (NAVY, SURF, NAVY, 0), 'soft': ('#FFF4E5', NAVY, LORANGE, 0), 'clear': (SURF, NAVY, None, 100)}[style]
    link = {'show': L_(True), 'type': L_(action)}
    if action == 'PageNavigation': link['navigationSection'] = L_(target)
    elif action == 'Back': pass
    elif action == 'Bookmark': link['bookmark'] = L_(target)
    if tooltip: link['tooltip'] = L_(tooltip)
    objs = {'icon': [{'properties': {'show': L_(False)}}],
            'text': [{'properties': {'show': L_(bool(label))} | ({'text': L_(label), 'fontColor': C_(fc), 'fontSize': L_(size), 'bold': L_(True), 'fontFamily': L_('Segoe UI Semibold')} if label else {})}],
            'fill': [{'properties': {'show': L_(True), 'fillColor': C_(fill), 'transparency': L_(alpha)}}],
            'outline': [{'properties': {'show': L_(line is not None), 'roundEdge': L_(12)} | ({'lineColor': C_(line)} if line else {})}],
            'shape': [{'properties': {'tileShape': L_('rectangleRounded'), 'roundEdge': L_(12)}}]}
    DEF(objs)
    if style != 'clear':
        objs['fill'].append({'properties': {'fillColor': C_(BLUE if style in ('navy', 'active') else (LORANGE if style == 'primary' else '#F1F5F9'))}, 'selector': {'id': 'hover'}})
    return p.add(vid, x, y, w, h, {'visualType': 'actionButton', 'objects': objs}, hidden,
                 cobj={'visualLink': [{'properties': link}]})
def svgcell(p, vid, x, y, w, h, meas, imgh, hidden=False, tooltip_page='tt_kpi'):
    imgh = min(imgh, h - 16)
    v = {'visualType': 'tableEx', 'query': {'queryState': {'Values': {'projections': [proj('M.' + meas, ' ')]}}},
         'objects': {'grid': [{'properties': {'gridVertical': L_(False), 'gridHorizontal': L_(False), 'outlineWeight': L_(0), 'rowPadding': L_(0), 'imageHeight': L_(imgh), 'imageWidth': L_(w - 30), 'textSize': L_(8)}}],
                     'columnHeaders': [{'properties': {'fontColor': C_(SURF), 'backColor': C_(SURF), 'fontSize': L_(1)}}],
                     'values': [{'properties': {'backColor': C_(SURF), 'backColorSecondary': C_(SURF)}}],
                     'total': [{'properties': {'totals': L_(False)}}]},
         'visualContainerObjects': container()}
    cobj = {'visualTooltip': [{'properties': {'show': L_(True), 'type': L_('ReportPage'), 'section': L_(tooltip_page)}}]} if tooltip_page else {'visualTooltip': [{'properties': {'show': L_(False)}}]}
    return p.add(vid, x, y, w, h, v, hidden, cobj)
def table(p, vid, x, y, w, h, cols, title=None, sort=None, hidden=False, imgh=28, tooltip_page=None, desc=True, size=12, imgw=230):
    v = {'visualType': 'tableEx', 'query': {'queryState': {'Values': {'projections': [proj(c, n) for c, n in cols]}}},
         'objects': {'grid': [{'properties': {'gridVertical': L_(False), 'gridHorizontal': L_(True), 'gridHorizontalColor': C_(BORDER), 'rowPadding': L_(6), 'imageHeight': L_(imgh), 'imageWidth': L_(imgw), 'textSize': L_(size), 'outlineColor': C_(BORDER)}}],
                     'columnHeaders': [{'properties': {'fontColor': C_(TS), 'backColor': C_(SURF), 'bold': L_(True), 'fontSize': L_(11), 'outline': L_('BottomOnly'), 'wordWrap': L_(True)}}],
                     'values': [{'properties': {'fontColorPrimary': C_(TP), 'backColorPrimary': C_(SURF), 'backColorSecondary': C_('#FAFCFE'), 'fontSize': L_(size)}}],
                     'total': [{'properties': {'totals': L_(False)}}]},
         'visualContainerObjects': container(title, SURF, True, 16, 12)}
    if sort:
        f, _, _ = fld(sort); v['query']['sortDefinition'] = {'sort': [{'field': f, 'direction': 'Descending' if desc else 'Ascending'}], 'isDefaultSort': True}
    cobj = {'visualTooltip': [{'properties': {'show': L_(True), 'type': L_('ReportPage'), 'section': L_(tooltip_page)}}]} if tooltip_page else None
    return p.add(vid, x, y, w, h, v, hidden, cobj)
def chart(p, vid, x, y, w, h, vtype, cat, vals, title, hidden=False, colors=None, tooltip_page=None, labels=False, fmt_pct=False):
    v = {'visualType': vtype, 'query': {'queryState': {'Category': {'projections': [proj(cat)]}, 'Y': {'projections': [proj(m, n) for m, n in vals]}}},
         'objects': {'categoryAxis': [{'properties': {'fontSize': L_(12), 'labelColor': C_(TS), 'showAxisTitle': L_(False)}}],
                     'valueAxis': [{'properties': {'fontSize': L_(12), 'labelColor': C_(TS), 'showAxisTitle': L_(False), 'gridlineColor': C_('#EEF2F6')}}],
                     'legend': [{'properties': {'show': L_(len(vals) > 1), 'position': L_('Top'), 'fontSize': L_(12), 'labelColor': C_(TS)}}],
                     'labels': [{'properties': {'show': L_(labels), 'fontSize': L_(11), 'color': C_(TP)}}],
                     'dataPoint': [{'properties': {'fill': C_(c)}, 'selector': {'metadata': fld(m)[1]}} for (m, _), c in zip(vals, colors or [BLUE, LORANGE, ORANGE])]},
         'visualContainerObjects': container(title, SURF, True, 16, 14)}
    if vtype == 'lineChart':
        v['objects']['lineStyles'] = [{'properties': {'strokeWidth': L_(3), 'showMarker': L_(True), 'markerSize': L_(4)}}]
    if vtype in ('clusteredBarChart',):
        f, _, _ = fld(vals[0][0]); v['query']['sortDefinition'] = {'sort': [{'field': f, 'direction': 'Descending'}], 'isDefaultSort': True}
    cobj = {'visualTooltip': [{'properties': {'show': L_(True), 'type': L_('ReportPage'), 'section': L_(tooltip_page)}}]} if tooltip_page else None
    return p.add(vid, x, y, w, h, v, hidden, cobj)
def matrix(p, vid, x, y, w, h, row, col, val, title, hidden=False):
    v = {'visualType': 'pivotTable', 'query': {'queryState': {'Rows': {'projections': [proj(row)]}, 'Columns': {'projections': [proj(col)]}, 'Values': {'projections': [proj(val, ' ')]}}},
         'objects': {'grid': [{'properties': {'gridVertical': L_(False), 'gridHorizontal': L_(False), 'imageHeight': L_(34), 'imageWidth': L_(150), 'rowPadding': L_(2), 'textSize': L_(12)}}],
                     'columnHeaders': [{'properties': {'fontColor': C_(TS), 'bold': L_(True), 'fontSize': L_(12), 'backColor': C_(SURF)}}],
                     'rowHeaders': [{'properties': {'fontColor': C_(TP), 'fontSize': L_(12), 'backColor': C_(SURF)}}],
                     'values': [{'properties': {'backColorPrimary': C_(SURF), 'backColorSecondary': C_(SURF)}}],
                     'subTotals': [{'properties': {'rowSubtotals': L_(False), 'columnSubtotals': L_(False)}}]},
         'visualContainerObjects': container(title, SURF, True, 16, 14)}
    return p.add(vid, x, y, w, h, v, hidden)
def slicer(p, vid, x, y, w, h, col, title, mode='Dropdown', hidden=True, group=None):
    v = {'visualType': 'slicer', 'query': {'queryState': {'Values': {'projections': [proj(col)]}}},
         'objects': {'data': [{'properties': {'mode': L_(mode)}}],
                     'header': [{'properties': {'show': L_(True), 'text': L_(title), 'fontColor': C_(TS), 'textSize': L_(11), 'bold': L_(True), 'outline': L_('None')}}],
                     'items': [{'properties': {'fontColor': C_(TP), 'textSize': L_(12), 'background': C_(SURF), 'outlineColor': C_(BORDER)}}],
                     'selection': [{'properties': {'selectAllCheckboxEnabled': L_(True)}}] if mode == 'Dropdown' else []},
         'visualContainerObjects': container(),
         'syncGroup': {'groupName': group or col.split('.')[1], 'fieldChanges': True, 'filterChanges': True}}
    if not v['objects']['selection']: del v['objects']['selection']
    return p.add(vid, x, y, w, h, v, hidden)

NAVP = [('home', 'Home'), ('performance', 'Trade Performance'), ('ailab', 'AI Intelligence Lab')]
BOOK = []  # bookmark dicts
FILTER_FIELDS = {'home': [('dCalendario.Data', 'PERÍODO', 'Between'), ('dProduto.industria', 'INDÚSTRIA'), ('dPDV.rede', 'REDE'), ('dPDV.regiao', 'REGIÃO'), ('dPDV.uf', 'ESTADO'), ('dProduto.categoria', 'CATEGORIA')],
                 'performance': [('dCalendario.Data', 'PERÍODO', 'Between'), ('dProduto.industria', 'INDÚSTRIA'), ('dPDV.rede', 'REDE'), ('dPDV.regiao', 'REGIÃO'), ('dPDV.uf', 'ESTADO'),
                                 ('dPDV.pdv', 'PDV'), ('dProduto.categoria', 'CATEGORIA'), ('dProduto.produto', 'PRODUTO'), ('dPromotor.promotor', 'PROMOTOR'), ('dCampanha.campanha', 'CAMPANHA')],
                 'ailab': [('dCalendario.Data', 'PERÍODO', 'Between'), ('dPDV.regiao', 'REGIÃO'), ('dProduto.industria', 'INDÚSTRIA')]}

def chrome(p):
    shape(p, 'nav_bar', 24, 14, 1872, 64, SURF, 0, 16)
    image(p, 'nav_logo', 40, 20, 190, 52, 'logo.png')
    x = 690
    for pid, lab in NAVP:
        w = 130 if pid == 'home' else 200
        button(p, f'nav_{pid}', x, 24, w, 44, lab, 'PageNavigation', pid, 'active' if pid == p.name else 'clear', size=13)
        x += w + 12
    button(p, 'nav_filtros', 1420, 24, 130, 44, '⚲  Filtros', 'Bookmark', f'bm_filtros_open_{p.name}', 'soft', size=12, tooltip='Abrir painel de filtros')
    button(p, 'nav_reset', 1560, 24, 110, 44, '↺  Limpar', 'Bookmark', f'bm_reset_{p.name}', 'ghost', size=12, tooltip='Limpar filtros desta página')
    button(p, 'nav_ajuda', 1680, 24, 44, 44, '?', 'PageNavigation', 'ajuda', 'ghost', size=14, tooltip='Central de ajuda')
    p.add('nav_update', 1732, 28, 156, 36, {'visualType': 'card', 'query': {'queryState': {'Values': {'projections': [proj('M.Atualização Dados')]}}},
          'objects': {'labels': [{'properties': {'fontSize': L_(9), 'color': C_(TS), 'fontFamily': L_('Segoe UI')}}], 'categoryLabels': [{'properties': {'show': L_(False)}}],
                      'wordWrap': [{'properties': {'show': L_(True)}}]}})
    svgcell(p, 'ctx_bar', 24, 82, 1872, 62, 'SVG Barra Contexto', 44)
    # painel de filtros oculto
    ids = [shape(p, 'flt_scrim', 0, 0, 1920, 1080, NAVY, 82, 0, None, hidden=True),
           shape(p, 'flt_panel', 1452, 14, 444, 1052, SURF, 0, 22, BORDER, hidden=True),
           text(p, 'flt_title', 1476, 30, 300, 44, [('Filtros', 20, NAVY, True), ('Aplicados a todas as páginas (sincronizados)', 10, TS)], hidden=True),
           button(p, 'flt_close', 1820, 34, 52, 40, '✕', 'Bookmark', f'bm_filtros_close_{p.name}', 'ghost', hidden=True, size=14, tooltip='Fechar painel')]
    y = 100
    for i, f in enumerate(FILTER_FIELDS[p.name]):
        col, lab = f[0], f[1]; mode = f[2] if len(f) > 2 else 'Dropdown'
        h = 96 if mode == 'Between' else 74
        ids.append(slicer(p, f'flt_s{i}', 1476, y, 396, h, col, lab, mode)); y += h + 10
    ids.append(button(p, 'flt_apply', 1476, 990, 396, 50, 'Aplicar e fechar', 'Bookmark', f'bm_filtros_close_{p.name}', 'navy', hidden=True, size=13))
    BOOK.append(selective(f'bm_filtros_open_{p.name}', f'Filtros · abrir · {p.disp}', p, show=ids, hide=[]))
    BOOK.append(selective(f'bm_filtros_close_{p.name}', f'Filtros · fechar · {p.disp}', p, show=[], hide=ids))
    BOOK.append({'$schema': f'{SCH}/bookmark/1.4.0/schema.json', 'name': f'bm_reset_{p.name}', 'displayName': f'Reset · {p.disp}',
                 'explorationState': {'version': '1.3', 'activeSection': p.name, 'filters': {}, 'sections': {p.name: {'filters': {}, 'visualContainers': {}}}},
                 'options': {'suppressDisplay': True}})

def selective(name, disp, p, show, hide, section=None):
    vcs = {}
    for v in show + hide:
        sv = {'visualType': p.v[v]['visual']['visualType'], 'objects': {}}
        if v in hide: sv['display'] = {'mode': 'hidden'}
        vcs[v] = {'singleVisual': sv}
    return {'$schema': f'{SCH}/bookmark/1.4.0/schema.json', 'name': name, 'displayName': disp,
            'explorationState': {'version': '1.3', 'activeSection': section or p.name, 'sections': {p.name: {'visualContainers': vcs}}},
            'options': {'applyOnlyToTargetVisuals': True, 'targetVisualNames': show + hide, 'suppressData': True}}

# ---------------- HOME ----------------
home = Page('home', 'Home', 'bg_home.png'); PAGES.append(home)
shape(home, 'hero_card', 24, 150, 1872, 230, SURF, 12, 22)
text(home, 'hero_title', 56, 172, 900, 70, [('TradeMind AI 360', 34, NAVY, True)])
text(home, 'hero_sub', 56, 236, 900, 40, [('Trade Intelligence. Powered by Data & AI.', 17, BLUE)])
svgcell(home, 'hero_ctx', 56, 292, 640, 70, 'SVG Hero Contexto', 60)
button(home, 'hero_btn_perf', 1340, 210, 250, 56, 'Explorar Performance  →', 'PageNavigation', 'performance', 'primary', size=14)
button(home, 'hero_btn_lab', 1610, 210, 250, 56, 'Abrir AI Lab', 'PageNavigation', 'ailab', 'ghost', size=14)
ms('90 SVG', 'SVG Hero Contexto', '''
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='640' height='60' viewBox='0 0 640 60' font-family='Segoe UI'>"
 & "<rect x='0' y='8' width='300' height='40' rx='20' fill='#082746' fill-opacity='0.06'/><text x='18' y='34' font-size='14' fill='#1B3044'><tspan font-weight='700'>Período </tspan>" & [Período Selecionado] & "</text>"
 & "<rect x='312' y='8' width='320' height='40' rx='20' fill='#16856A' fill-opacity='0.10'/><circle cx='332' cy='28' r='5' fill='#16856A'/><text x='346' y='34' font-size='14' fill='#16856A' font-weight='600'>" & [Atualização Dados] & "</text></svg>"
RETURN ''' + enc('_svg'), img=True)
# rede de pontos decorativa (SVG estático, discreto) no hero
ms('90 SVG', 'SVG Hero Rede', '''
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='360' height='200' viewBox='0 0 360 200'><g stroke='#06436E' stroke-opacity='0.25' stroke-width='1.5'><line x1='20' y1='150' x2='90' y2='70'/><line x1='90' y1='70' x2='170' y2='120'/><line x1='170' y1='120' x2='250' y2='40'/><line x1='250' y1='40' x2='330' y2='100'/><line x1='90' y1='70' x2='250' y2='40'/><line x1='170' y1='120' x2='330' y2='100'/><line x1='170' y1='120' x2='210' y2='180'/></g>"
 & "<g fill='#06436E'><circle cx='20' cy='150' r='5'/><circle cx='90' cy='70' r='7'/><circle cx='170' cy='120' r='6'/><circle cx='330' cy='100' r='6'/><circle cx='210' cy='180' r='4'/></g><circle cx='250' cy='40' r='9' fill='#F58200'/></svg>"
RETURN ''' + enc('_svg'), img=True)
svgcell(home, 'hero_net', 940, 166, 370, 204, 'SVG Hero Rede', 200)
kp = ['SVG KPI Sell-out', 'SVG KPI Ruptura', 'SVG KPI Conformidade', 'SVG KPI PDVs']
for i, k in enumerate(kp): svgcell(home, f'home_kpi{i}', 24 + i * 474, 396, 456, 172, k, 160, tooltip_page='tt_kpi')
table(home, 'home_radar', 24, 584, 1100, 476, [('dPDV.pdv', 'PDV'), ('dPDV.rede', 'Rede'), ('M.Prioridade', 'Prioridade'),
      ('M.SVG Status Atenção', 'Status'), ('M.SVG Barra Ruptura', 'Ruptura observada'), ('M.SVG Tendência Ruptura', 'Tendência vs AA'), ('M.Score Atenção', 'Score'), ('M.Ação Investigativa (hipótese)', 'Ação (hipótese)')],
      'Radar de atenção · PDVs por score de atenção (ruptura × não conformidade) · botão direito › Detalhar', sort='M.Score Atenção', tooltip_page='tt_kpi')
cards = [('SVG Card RAG', 'bm_mod_rag'), ('SVG Card FT', 'bm_mod_ft'), ('SVG Card GR', 'bm_mod_gr'), ('SVG Card ML', 'bm_mod_ml')]
for i, (c, bm) in enumerate(cards):
    x = 1140 + (i % 2) * 382; y = 584 + (i // 2) * 182
    svgcell(home, f'home_ai{i}', x, y, 374, 172, c, 145, tooltip_page='tt_ia')
    button(home, f'home_ai_btn{i}', x, y, 374, 172, '', 'Bookmark', bm, 'clear', tooltip='Abrir módulo no AI Lab')
svgcell(home, 'home_insight', 1140, 948, 756, 112, 'SVG Insight Compacto', 104)
button(home, 'home_insight_btn', 1720, 1010, 160, 40, 'Explorar diagnóstico →', 'PageNavigation', 'performance', 'primary', size=10)
ms('90 SVG', 'SVG Insight Compacto', '''
VAR reg = [Insight Região Crítica] VAR av = [Ruptura %]
VAR t = ADDCOLUMNS(FILTER(VALUES(dPDV[regiao]), NOT ISBLANK([Ruptura %])), "@r", [Ruptura %])
VAR rr = MAXX(TOPN(1, t, [@r], DESC), [@r])
VAR np = COUNTROWS(FILTER(VALUES(dPDV[pdv]), [Ruptura %] > av * 1.15))
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='740' height='104' viewBox='0 0 740 104' font-family='Segoe UI, sans-serif'>"
 & "<rect x='1' y='1' width='738' height='102' rx='16' fill='#082746'/><circle cx='700' cy='10' r='70' fill='#06436E' fill-opacity='0.6'/>"
 & "<text x='22' y='28' font-size='12' font-weight='700' fill='#FFA51B' letter-spacing='1.4'>INSIGHT DO PERÍODO · REGRA DAX AUDITÁVEL</text>"
 & "<text x='22' y='58' font-size='19' font-weight='700' fill='#FFFFFF'>Maior ruptura: " & reg & " · " & FORMAT(rr, "0.0%") & " vs " & FORMAT(av, "0.0%") & " média</text>"
 & "<text x='22' y='86' font-size='14' fill='#C9D6E3'>" & FORMAT(np, "0") & " PDVs acima de 115% da média · hipótese, não causa comprovada</text></svg>"
RETURN IF(ISBLANK(av), BLANK(), ''' + enc('_svg') + ')', img=True)
chrome(home)

# ---------------- PERFORMANCE ----------------
perf = Page('performance', 'Trade Performance', 'bg_pages.png'); PAGES.append(perf)
kp = ['SVG KPI Sell-out', 'SVG KPI Unidades', 'SVG KPI Ruptura', 'SVG KPI Conformidade']
for i, k in enumerate(kp): svgcell(perf, f'perf_kpi{i}', 24 + i * 474, 148, 456, 172, k, 160, tooltip_page='tt_kpi')
PERS = [('sell', 'Sell-out'), ('rup', 'Ruptura'), ('exe', 'Execução'), ('cmp', 'Campanhas')]
groups = {}
groups['sell'] = [chart(perf, 'p_sell_line', 24, 400, 1140, 404, 'lineChart', 'dCalendario.MesAno', [('M.Sell-out', 'Sell-out'), ('M.Sell-out AA', 'Ano anterior')], 'Evolução do sell-out monitorado (amostra) · R$', tooltip_page='tt_kpi'),
                  chart(perf, 'p_sell_rank', 1180, 400, 716, 404, 'clusteredBarChart', 'dPDV.rede', [('M.Sell-out', 'Sell-out')], 'Ranking de redes · sell-out monitorado', labels=True, tooltip_page='tt_kpi')]
groups['rup'] = [chart(perf, 'p_rup_line', 24, 400, 1140, 404, 'lineChart', 'dCalendario.InicioSemana', [('M.Ruptura %', 'Ruptura observada')], 'Ruptura semanal observada · % das combinações PDV×SKU auditadas com saldo zero', hidden=True, colors=[ORANGE], tooltip_page='tt_kpi'),
                 matrix(perf, 'p_rup_heat', 1180, 400, 716, 404, 'dPDV.rede', 'dProduto.categoria', 'M.SVG Heat Ruptura', 'Matriz de risco · rede × categoria (intensidade relativa à média)', hidden=True)]
groups['exe'] = [chart(perf, 'p_exe_bar', 24, 400, 1140, 404, 'clusteredColumnChart', 'dPDV.regiao', [('M.Conformidade Checklist %', 'Checklist'), ('M.Planograma OK %', 'Planograma'), ('M.Material PDV OK %', 'Material PDV')], 'Conformidade de execução por região', hidden=True, colors=[BLUE, '#4387AD', LORANGE], labels=True),
                 table(perf, 'p_exe_rank', 1180, 400, 716, 404, [('dPromotor.promotor', 'Promotor'), ('M.Visitas', 'Visitas'), ('M.SVG Barra Conformidade', 'Checklist'), ('M.Duração Média Visita (min)', 'Min/visita')], 'Promotores · conformidade de checklist', sort='M.Conformidade Checklist %', hidden=True, desc=False)]
groups['cmp'] = [chart(perf, 'p_cmp_bar', 24, 400, 1140, 404, 'clusteredBarChart', 'dCampanha.campanha', [('M.Execução Campanha %', 'Execução')], 'Execução média das campanhas · % (sem inferência causal)', hidden=True, colors=[BLUE], labels=True),
                 table(perf, 'p_cmp_tab', 1180, 400, 716, 404, [('dCampanha.campanha', 'Campanha'), ('dCampanha.industria_campanha', 'Indústria'), ('M.Custo Campanhas', 'Custo executado'), ('M.Execução Campanha %', 'Execução'), ('M.Custo por p.p. Execução', 'Custo / p.p.')], 'Custo × execução · ROI incremental não calculável sem grupo controle', sort='M.Custo Campanhas', hidden=True)]
for i, (k, lab) in enumerate(PERS):
    button(perf, f'pers_{k}', 24 + i * 176, 340, 166, 44, lab, 'Bookmark', f'bm_pers_{k}', 'ghost', size=12)
    # estado ativo: botão "on" sobreposto
for i, (k, lab) in enumerate(PERS):
    button(perf, f'pers_on_{k}', 24 + i * 176, 340, 166, 44, lab, 'Bookmark', f'bm_pers_{k}', 'active', hidden=(k != 'sell'), size=12)
text(perf, 'pers_hint', 740, 344, 560, 36, [('Selecione a perspectiva analítica · dados de vendas são amostrados', 11, TS)])
button(perf, 'perf_ia', 1676, 338, 220, 48, '✦  Investigar com IA', 'PageNavigation', 'ailab', 'primary', size=13, tooltip='Leva ao AI Lab com os mesmos filtros (slicers sincronizados)')
table(perf, 'perf_smart', 24, 820, 1872, 240, [('dPDV.rede', 'Rede'), ('M.Sell-out', 'Sell-out'), ('M.Sell-out AA', 'Ano anterior'), ('M.SVG Variação Sell-out', 'Variação'),
      ('M.SVG Sparkline Sell-out', 'Tendência 12m'), ('M.SVG Barra Ruptura', 'Ruptura'), ('M.SVG Status Atenção', 'Status'), ('M.Prioridade', 'Prioridade')],
      'Tabela inteligente · redes', sort='M.Sell-out', tooltip_page='tt_kpi', imgh=30)
allg = [v for g in groups.values() for v in g]
for k, lab in PERS:
    BOOK.append(selective(f'bm_pers_{k}', f'Perspectiva · {lab}', perf, show=groups[k] + [f'pers_on_{k}'],
                          hide=[v for v in allg if v not in groups[k]] + [f'pers_on_{o}' for o, _ in PERS if o != k]))
chrome(perf)

# ---------------- AI LAB ----------------
lab = Page('ailab', 'AI Intelligence Lab', 'bg_pages.png'); PAGES.append(lab)
MODS = [('rag', 'RAG'), ('ft', 'FINE-TUNING'), ('gr', 'GUARDRAILS'), ('ml', 'MLOPS')]
mg = {}
H = lambda k: k != 'rag'
mg['rag'] = [svgcell(lab, f'rag_k{i}', 24 + i * 474, 214, 456, 124, k, 120, hidden=H('rag'), tooltip_page='tt_ia') for i, k in enumerate(['SVG RAG Aprovação', 'SVG RAG Latência', 'SVG RAG Docs', 'SVG RAG SemEv'])]
mg['rag'] += [lab.add('rag_chat', 1040, 352, 856, 708, {'visualType': 'tradeMindChatRAG7F3A2C', 'query': {'queryState': {'contexto': {'projections': [proj('M.Contexto Texto')]}}},
                   'objects': {'api': [{'properties': {'url': L_('http://127.0.0.1:8360'), 'usuario': L_('gestor.demo')}}]}, 'visualContainerObjects': container()}, hidden=False),
              table(lab, 'rag_eval', 24, 352, 1000, 340, [('fAvaliacoesLLM.caso', 'Caso'), ('fAvaliacoesLLM.pergunta', 'Pergunta'), ('fAvaliacoesLLM.status', 'Estado'), ('M.SVG Aprovado RAG', 'Avaliação'), ('fAvaliacoesLLM.n_evidencias', 'Evid.'), ('fAvaliacoesLLM.latencia_ms', 'ms')], 'Avaliações de fundamentação executadas (pipeline)', hidden=True),
              table(lab, 'rag_evid', 24, 706, 1000, 354, [('fRecuperacaoRAG.documento', 'Documento'), ('fRecuperacaoRAG.versao', 'Versão'), ('fRecuperacaoRAG.trecho', 'Trecho recuperado'), ('fRecuperacaoRAG.score', 'Relevância')], 'Evidências recuperadas (clique numa avaliação para filtrar)', sort='fRecuperacaoRAG.score', hidden=True, size=11)]
mg['ft'] = [svgcell(lab, f'ft_k{i}', 24 + i * 474, 214, 456, 124, k, 120, hidden=True, tooltip_page='tt_ia') for i, k in enumerate(['SVG FT F1', 'SVG FT Acc', 'SVG FT Casos', 'SVG FT LLM'])]
mg['ft'] += [table(lab, 'ft_models', 24, 352, 760, 300, [('dModelosIA.modelo', 'Modelo'), ('dModelosIA.versao', 'Versão'), ('dModelosIA.modulo', 'Tipo'), ('M.SVG Status Modelo', 'Status')], 'Registro de modelos', hidden=True),
             chart(lab, 'ft_cmp', 24, 668, 760, 392, 'clusteredBarChart', 'fExperimentosML.metrica', [('M.FT Valor Base', 'Base (regras)'), ('M.FT Valor Especializado', 'Especializado')], 'Base × especializado · conjunto de teste', hidden=True, colors=['#94A3B8', ORANGE], labels=True),
             table(lab, 'ft_side', 800, 352, 1096, 708, [('fComparadorModelos.entrada', 'Entrada de teste'), ('fComparadorModelos.esperado', 'Esperado'), ('fComparadorModelos.base', 'Modelo base'), ('M.SVG Acerto Base', ' '), ('fComparadorModelos.especializado', 'Especializado'), ('M.SVG Acerto Especializado', ' ')], 'Comparador lado a lado · dados sintéticos · classificador supervisionado (não é fine-tuning de LLM)', hidden=True, size=11)]
ms('07 IA', 'FT Valor Base', 'CALCULATE(MAX(fExperimentosML[valor]), fExperimentosML[modelo] = "baseline-regras-palavra-chave", fExperimentosML[experimento] = "EXP-CLS-001")', '0.000')
ms('07 IA', 'FT Valor Especializado', 'CALCULATE(MAX(fExperimentosML[valor]), fExperimentosML[modelo] = "classificador-ocorrencias-tfidf-lr", fExperimentosML[experimento] = "EXP-CLS-001")', '0.000')
mg['gr'] = [svgcell(lab, f'gr_k{i}', 24 + i * 474, 214, 456, 124, k, 120, hidden=True, tooltip_page='tt_ia') for i, k in enumerate(['SVG GR Testes', 'SVG GR Bloq', 'SVG GR Sucesso', 'SVG GR Lat'])]
mg['gr'] += [svgcell(lab, 'gr_rls', 24, 350, 640, 58, 'SVG Usuário RLS', 40, hidden=True, tooltip_page='tt_ia'),
             text(lab, 'gr_rls_t', 680, 356, 1216, 48, [('RLS no modelo: papel dinâmico por USERPRINCIPALNAME() (dUsuarioAcesso ← regra_acesso) + papéis demo. Teste em Modelagem › Exibir como. A API aplica as mesmas regras no backend.', 11, TS)], hidden=True),
             table(lab, 'gr_tab', 24, 416, 1872, 644, [('fTestesGuardrails.cenario', 'Cenário'), ('fTestesGuardrails.perfil', 'Perfil'), ('fTestesGuardrails.regra_aplicada', 'Regra aplicada'),
              ('fTestesGuardrails.resultado_esperado', 'Esperado'), ('fTestesGuardrails.resultado_obtido', 'Obtido'), ('M.SVG Status Teste', 'Status'), ('fTestesGuardrails.timestamp', 'Timestamp')],
              'Laboratório de segurança · testes executados contra o backend (RBAC + RLS + validação + detecção de injeção)', hidden=True)]
mg['ml'] = [svgcell(lab, f'ml_k{i}', 24 + i * 474, 214, 456, 124, k, 120, hidden=True, tooltip_page='tt_ia') for i, k in enumerate(['SVG ML Modelos', 'SVG ML Exp', 'SVG ML AUC', 'SVG ML Ult'])]
mg['ml'] += [chart(lab, 'ml_mon', 24, 352, 900, 330, 'lineChart', 'fMonitorRuptura.mes', [('M.Prob Prevista Média', 'Prob. prevista'), ('M.Taxa Observada Teste', 'Taxa observada')], 'Calibração mensal no período de teste · risco de ruptura (modelo rejeitado)', hidden=True, colors=[BLUE, ORANGE]),
             table(lab, 'ml_models', 940, 352, 956, 330, [('dModelosIA.modelo', 'Modelo'), ('dModelosIA.modulo', 'Módulo'), ('dModelosIA.descricao', 'Descrição'), ('M.SVG Status Modelo', 'Status')], 'Catálogo de modelos', hidden=True, size=11),
             table(lab, 'ml_exp', 24, 698, 1872, 362, [('fExperimentosML.experimento', 'Experimento'), ('fExperimentosML.modelo', 'Modelo'), ('fExperimentosML.versao', 'Versão'), ('fExperimentosML.timestamp', 'Data'), ('fExperimentosML.metrica', 'Métrica'), ('fExperimentosML.valor', 'Resultado'), ('fExperimentosML.status', 'Status')], 'Registro de experimentos (fExperimentosML · append a cada execução)', hidden=True)]
for i, (k, l_) in enumerate(MODS):
    button(lab, f'mod_{k}', 24 + i * 200, 152, 188, 48, l_, 'Bookmark', f'bm_mod_{k}', 'ghost', size=13)
for i, (k, l_) in enumerate(MODS):
    button(lab, f'mod_on_{k}', 24 + i * 200, 152, 188, 48, l_, 'Bookmark', f'bm_mod_{k}', 'active', hidden=(k != 'rag'), size=13)
text(lab, 'mod_hint', 850, 158, 1040, 40, [('Módulos executados localmente · métricas lidas da telemetria real do pipeline (03_AI/run_pipeline.py)', 11, TS)], align='right')
allm = [v for g in mg.values() for v in g]
for v in mg['rag']: lab.v[v].pop('isHidden', None)
for k, l_ in MODS:
    BOOK.append(selective(f'bm_mod_{k}', f'Módulo · {l_}', lab, show=mg[k] + [f'mod_on_{k}'],
                          hide=[v for v in allm if v not in mg[k]] + [f'mod_on_{o}' for o, _ in MODS if o != k]))
chrome(lab)

# ---------------- páginas ocultas ----------------
tt = Page('tt_kpi', 'Tooltip · Investigação', None, 640, 400, hidden=True, tooltip=True); PAGES.append(tt)
shape(tt, 'tt_bg', 0, 0, 640, 400, SURF, 0, 16)
text(tt, 'tt_t', 20, 12, 600, 40, [('Investigação do contexto', 15, NAVY, True)])
svgcell(tt, 'tt_ctx', 16, 56, 608, 60, 'SVG Tooltip Resumo', 56, tooltip_page=None)
chart(tt, 'tt_line', 16, 122, 608, 200, 'lineChart', 'dCalendario.MesAno', [('M.Ruptura %', 'Ruptura'), ('M.Conformidade Checklist %', 'Checklist')], None, colors=[ORANGE, BLUE])
text(tt, 'tt_def', 20, 326, 600, 70, [('Ruptura = obs. PDV×SKU com saldo zero ÷ obs. auditadas (amostra semanal). Ausência de observação não é estoque zero. Sell-out = amostra de SKUs monitorados.', 10, TS)])
ms('90 SVG', 'SVG Tooltip Resumo', '''
VAR _svg = "<svg xmlns='http://www.w3.org/2000/svg' width='608' height='56' viewBox='0 0 608 56' font-family='Segoe UI'>"
 & "<text x='4' y='20' font-size='12' fill='#64748B'>Sell-out atual · AA · var</text><text x='4' y='44' font-size='16' font-weight='700' fill='#082746'>" & FORMAT([Sell-out], "R$ #,0") & " · " & FORMAT([Sell-out AA], "R$ #,0") & " · " & FORMAT([Sell-out Var %], "+0.0%;-0.0%") & "</text>"
 & "<text x='390' y='20' font-size='12' fill='#64748B'>Ruptura · cobertura</text><text x='390' y='44' font-size='16' font-weight='700' fill='#F58200'>" & FORMAT([Ruptura %], "0.0%") & " · " & FORMAT([Observações Estoque], "#,0") & " obs.</text></svg>"
RETURN ''' + enc('_svg'), img=True)
tti = Page('tt_ia', 'Tooltip · IA', None, 640, 400, hidden=True, tooltip=True); PAGES.append(tti)
shape(tti, 'tti_bg', 0, 0, 640, 400, SURF, 0, 16)
text(tti, 'tti_t', 20, 12, 600, 40, [('Estado real dos módulos de IA', 15, NAVY, True)])
table(tti, 'tti_tab', 12, 56, 616, 250, [('dModelosIA.modulo', 'Módulo'), ('dModelosIA.modelo', 'Modelo'), ('M.SVG Status Modelo', 'Status')], None, size=10, imgw=190)
text(tti, 'tti_lim', 20, 312, 600, 84, [('Limitações: RAG extrativo (sem LLM generativo); classificador treinado com dados sintéticos; fine-tuning de LLM pendente (sem infraestrutura); modelos de ruptura rejeitados (AUC≈0,50). Fonte: telemetria de 03_AI/run_pipeline.py.', 10, TS)])
ajuda = Page('ajuda', 'Central de Ajuda', 'bg_pages.png', hidden=True); PAGES.append(ajuda)
shape(ajuda, 'aj_card', 160, 120, 1600, 860, SURF, 0, 24)
text(ajuda, 'aj_txt', 200, 150, 1520, 760, [
    ('Central de ajuda · indicadores e navegação', 24, NAVY, True), ('', 10, TS),
    ('Sell-out monitorado — soma da receita da amostra de SKUs monitorados; não representa o faturamento total da rede.', 13, TP),
    ('Ruptura semanal observada — combinações PDV×SKU auditadas com saldo zero ÷ combinações auditadas. Ausência de observação não é estoque zero.', 13, TP),
    ('Conformidade de execução — média do checklist das visitas (0–100%). Planograma e material PDV vêm das auditorias de produto.', 13, TP),
    ('Campanhas — execução e custo observados. Não há grupo controle: crescimento de vendas não é atribuído às campanhas e ROI incremental não é calculado.', 13, TP),
    ('Índice de atenção — ruptura × (1 − conformidade). Ações sugeridas são hipóteses investigativas, não causas comprovadas.', 13, TP),
    ('Metas mensais — comparáveis apenas com a amostra; atingimento é indicativo.', 13, TP), ('', 10, TS),
    ('Navegação — barra superior troca de página; “Filtros” abre o painel lateral (filtros sincronizados entre páginas); “Limpar” remove os filtros da página.', 13, TP),
    ('AI Lab — RAG, classificador de ocorrências, guardrails e MLOps exibem telemetria real de execuções locais. Fine-tuning de LLM está pendente (sem infraestrutura).', 13, TP),
    ('Dados — banco SQLite fictício (2025–2026). Datas após 14/11/2026 são simuladas futuras. Ocorrências de PDV são sintéticas.', 13, TP)])
button(ajuda, 'aj_back', 200, 900, 220, 50, '←  Voltar para Home', 'PageNavigation', 'home', 'navy', size=13)

dt = Page('detalhe_pdv', 'Detalhe do PDV', 'bg_pages.png', hidden=True); dt.drill = 'dPDV.pdv'; PAGES.append(dt)
shape(dt, 'dt_head', 24, 14, 1872, 92, SURF, 0, 18)
button(dt, 'dt_back', 44, 34, 140, 52, '←  Voltar', 'Back', None, 'navy', size=13)
dt.add('dt_title', 204, 26, 1400, 70, {'visualType': 'card', 'query': {'queryState': {'Values': {'projections': [proj('M.Título Detalhe PDV')]}}},
       'objects': {'labels': [{'properties': {'fontSize': L_(22), 'color': C_(NAVY), 'fontFamily': L_('Segoe UI Semibold')}}], 'categoryLabels': [{'properties': {'show': L_(False)}}], 'wordWrap': [{'properties': {'show': L_(True)}}]}})
text(dt, 'dt_tag', 1560, 40, 320, 40, [('Drillthrough · contexto do PDV', 11, TS)], align='right')
for i, k in enumerate(['SVG KPI Sell-out', 'SVG KPI Ruptura', 'SVG KPI Conformidade', 'SVG KPI Unidades']): svgcell(dt, f'dt_kpi{i}', 24 + i * 474, 122, 456, 172, k, 160)
chart(dt, 'dt_line', 24, 310, 1140, 380, 'lineChart', 'dCalendario.InicioSemana', [('M.Ruptura %', 'Ruptura observada')], 'Ruptura semanal observada no PDV', colors=[ORANGE])
table(dt, 'dt_cat', 1180, 310, 716, 380, [('dProduto.categoria', 'Categoria'), ('M.SVG Barra Ruptura', 'Ruptura'), ('M.SKUs com Ruptura', 'SKUs c/ ruptura'), ('M.Planograma OK %', 'Planograma')], 'Categorias · ruptura e execução', sort='M.Ruptura %')
table(dt, 'dt_prom', 24, 706, 900, 354, [('dPromotor.promotor', 'Promotor'), ('M.Visitas', 'Visitas'), ('M.SVG Barra Conformidade', 'Checklist'), ('M.Duração Média Visita (min)', 'Min/visita'), ('M.Material PDV OK %', 'Material PDV')], 'Visitas por promotor', sort='M.Visitas')
table(dt, 'dt_oc', 940, 706, 956, 354, [('fOcorrenciasPDV.data', 'Data'), ('fOcorrenciasPDV.descricao', 'Ocorrência (sintética)'), ('fOcorrenciasPDV.categoria_prevista', 'Classe prevista'), ('fOcorrenciasPDV.confianca', 'Confiança')], 'Ocorrências sintéticas classificadas pelo modelo especializado', sort='fOcorrenciasPDV.data', size=11)

# ---------------- RLS ----------------
UP = 'LOOKUPVALUE(dUsuarioAcesso[{c}], dUsuarioAcesso[upn], USERPRINCIPALNAME())'
ROLES = {
 'Acesso por Usuário (dinâmico)': {
   'dUsuarioAcesso': '[upn] = USERPRINCIPALNAME()',
   'dProduto': f'VAR i = {UP.format(c="industria_acesso")} RETURN NOT ISBLANK({UP.format(c="perfil")}) && (i = "" || [industria] = i)',
   'dCampanha': f'VAR i = {UP.format(c="industria_acesso")} RETURN NOT ISBLANK({UP.format(c="perfil")}) && (i = "" || [industria_campanha] = i)',
   'dPDV': f'VAR r = {UP.format(c="regiao_acesso")} RETURN NOT ISBLANK({UP.format(c="perfil")}) && (r = "" || [regiao] = r)',
   'fVenda': f'{UP.format(c="pode_vendas")} = 1', 'fEstoque': f'{UP.format(c="pode_estoque")} = 1',
   'fVisita': f'{UP.format(c="pode_visitas")} = 1', 'fAuditoria': f'{UP.format(c="pode_visitas")} = 1'},
 'Demo · Cliente Aurora Foods': {'dProduto': '[industria] = "Aurora Foods"', 'dCampanha': '[industria_campanha] = "Aurora Foods"', 'fVisita': 'FALSE()', 'fAuditoria': 'FALSE()', 'dUsuarioAcesso': 'FALSE()'},
 'Demo · Promotor Sul': {'dPDV': '[regiao] = "Sul"', 'fVenda': 'FALSE()', 'fEstoque': 'FALSE()', 'dUsuarioAcesso': 'FALSE()'},
}
for rn, perms in ROLES.items():
    body = f"role {q(rn)}\n\tmodelPermission: read\n\n" + ''.join(f"\ttablePermission {t} = {e}\n\n" for t, e in perms.items()) + f"\tannotation PBI_Id = {lt(rn).replace('-', '')}\n"
    wt(D / 'roles' / f"{re.sub(r'[^A-Za-z0-9]+', '_', rn)}.tmdl", body)
wt(D / 'model.tmdl', (D / 'model.tmdl').read_text(encoding='utf-8') + ''.join(f'ref role {q(r)}\n' for r in ROLES))

# ---------------- escrever relatório ----------------
R = RP / 'definition'
RES = RP / 'StaticResources' / 'RegisteredResources'; RES.mkdir(parents=True, exist_ok=True)
shutil.copy(ROOT / 'Ondas Abstratas em Azul e Laranja aba de home.png', RES / 'bg_home.png')
shutil.copy(ROOT / 'Ondas Abstratas em Azul e Laranja abas.png', RES / 'bg_pages.png')
shutil.copy(ROOT / 'Logo Vértice Trade Marketing.png', RES / 'logo.png')
theme = json.load(open(ROOT / '02_POWER_BI' / 'theme' / 'VerticeTheme.json', encoding='utf-8'))
wj(RES / 'VerticeTheme.json', theme)
shutil.copytree(ROOT / '05_CUSTOM_VISUAL' / 'registered' / 'tradeMindChatRAG7F3A2C', RP / 'CustomVisuals' / 'tradeMindChatRAG7F3A2C')
wj(R / 'version.json', {'$schema': f'{SCH}/versionMetadata/1.0.0/schema.json', 'version': '2.0.0'})
wj(R / 'report.json', {'$schema': f'{SCH}/report/1.2.0/schema.json',
    'layoutOptimization': 'None',
    'themeCollection': {'customTheme': {'name': 'VerticeTheme.json', 'reportVersionAtImport': '5.55', 'type': 'RegisteredResources'}},
    'objects': {'outspacePane': [{'properties': {'expanded': L_(False), 'visible': L_(False)}}]},
    'resourcePackages': [{'name': 'RegisteredResources', 'type': 'RegisteredResources', 'items': [
        {'name': 'VerticeTheme.json', 'path': 'VerticeTheme.json', 'type': 'CustomTheme'},
        {'name': 'bg_home.png', 'path': 'bg_home.png', 'type': 'Image'}, {'name': 'bg_pages.png', 'path': 'bg_pages.png', 'type': 'Image'},
        {'name': 'logo.png', 'path': 'logo.png', 'type': 'Image'}]},
        {'name': 'tradeMindChatRAG7F3A2C', 'type': 'CustomVisual', 'items': [{'name': 'tradeMindChatRAG7F3A2C.pbiviz.json', 'path': 'tradeMindChatRAG7F3A2C.pbiviz.json', 'type': 'CustomVisualMetadata'}]}],
    'settings': {'useStylableVisualContainerHeader': True, 'exportDataMode': 'AllowSummarized', 'defaultDrillFilterOtherVisuals': True, 'allowChangeFilterTypes': True}})
wj(R / 'pages' / 'pages.json', {'$schema': f'{SCH}/pagesMetadata/1.0.0/schema.json', 'pageOrder': [p.name for p in PAGES], 'activePageName': 'home'})
for p in PAGES:
    pj = {'$schema': f'{SCH}/page/2.0.0/schema.json', 'name': p.name, 'displayName': p.disp, 'displayOption': 'ActualSize' if p.tooltip else 'FitToPage', 'height': p.h, 'width': p.w}
    if p.hidden: pj['visibility'] = 'HiddenInViewMode'
    if p.tooltip: pj['type'] = 'Tooltip'
    if getattr(p, 'drill', None):
        f, _, _ = fld(p.drill)
        pj['pageBinding'] = {'name': 'pbDetalhePDV', 'type': 'Drillthrough', 'parameters': [{'name': 'prmDrillPDV', 'boundFilter': 'fDrillPDV', 'asAggregation': False, 'qnaSingleSelectRequired': False, 'fieldExpr': f}]}
        pj['filterConfig'] = {'filters': [{'name': 'fDrillPDV', 'field': f, 'type': 'Categorical', 'howCreated': 'Drillthrough'}]}
    objs = {'outspace': [{'properties': {'color': C_('#F7F9FC')}}]}
    if p.bg:
        objs['background'] = [{'properties': {'image': {'image': {'name': L_(p.bg), 'url': {'expr': {'ResourcePackageItem': {'PackageName': 'RegisteredResources', 'PackageType': 1, 'ItemName': p.bg}}}, 'scaling': L_('Fill')}},
                                                'transparency': L_(0)}}]
    else:
        objs['background'] = [{'properties': {'color': C_(SURF), 'transparency': L_(0)}}]
    pj['objects'] = objs
    wj(R / 'pages' / p.name / 'page.json', pj)
    for vid, vc in p.v.items(): wj(R / 'pages' / p.name / 'visuals' / vid / 'visual.json', vc)
wj(R / 'bookmarks' / 'bookmarks.json', {'$schema': f'{SCH}/bookmarksMetadata/1.0.0/schema.json', 'items': [{'name': b['name']} for b in BOOK]})
for b in BOOK: wj(R / 'bookmarks' / f"{b['name']}.bookmark.json", b)
wj(RP / 'definition.pbir', {'$schema': 'https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json', 'version': '4.0',
                            'datasetReference': {'byPath': {'path': f'../{NAME}.SemanticModel'}}})
wj(RP / '.platform', {'$schema': 'https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json',
                      'metadata': {'type': 'Report', 'displayName': NAME}, 'config': {'version': '2.0', 'logicalId': lt('rp')}})
wj(PB / f'{NAME}.pbip', {'$schema': 'https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json', 'version': '1.0',
                          'artifacts': [{'report': {'path': f'{NAME}.Report'}}], 'settings': {'enableAutoRecovery': True}})
# re-escrever tabela de medidas (medidas adicionadas após a 1a montagem)
L = ['table _Medidas', f'\tlineageTag: {lt("_Medidas")}', '']
for folder, name, expr, fmt, img in M:
    L.append(f"\tmeasure {q(name)} = ```")
    for line in expr.split('\n'): L.append('\t\t\t' + line)
    L.append('\t\t\t```')
    if fmt: L.append(f'\t\tformatString: {fmt}')
    if img: L.append('\t\tdataCategory: ImageUrl')
    L += [f'\t\tdisplayFolder: {folder}', f'\t\tlineageTag: {lt("m" + name)}', '']
L += ['\tcolumn Coluna', '\t\tdataType: string', '\t\tisHidden', f'\t\tlineageTag: {lt("mcol")}', '\t\tsummarizeBy: none', '\t\tsourceColumn: Coluna', '',
      '\tpartition _Medidas = m', '\t\tmode: import', '\t\tsource = #table(type table [Coluna = text], {})', '']
wt(D / 'tables' / '_Medidas.tmdl', '\n'.join(L))
# documentação das medidas
wt(PB / 'MEDIDAS_DAX.md', '# Medidas DAX\n\n' + '\n'.join(f'## {n}\n*Pasta:* {f}\n```dax\n{e}\n```\n' for f, n, e, _, _ in M if not f.startswith('90')))
print(f'pages={len(PAGES)} visuals={sum(len(p.v) for p in PAGES)} measures={len(M)} bookmarks={len(BOOK)}')
