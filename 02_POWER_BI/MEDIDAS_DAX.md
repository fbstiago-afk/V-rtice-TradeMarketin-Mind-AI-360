# Medidas DAX

## Sell-out
*Pasta:* 01 Vendas
```dax
SUM(fVenda[receita])
```

## Unidades
*Pasta:* 01 Vendas
```dax
SUM(fVenda[unidades])
```

## Preço Médio
*Pasta:* 01 Vendas
```dax
DIVIDE([Sell-out], [Unidades])
```

## Sell-out AA
*Pasta:* 01 Vendas
```dax
CALCULATE([Sell-out], SAMEPERIODLASTYEAR(dCalendario[Data]))
```

## Sell-out Var %
*Pasta:* 01 Vendas
```dax
VAR c = CALCULATE([Sell-out], KEEPFILTERS(FILTER(ALL(dCalendario[Data]), dCalendario[Data] >= EDATE(CALCULATE(MIN(fVenda[data]), REMOVEFILTERS()), 12)))) VAR a = CALCULATE([Sell-out AA], KEEPFILTERS(FILTER(ALL(dCalendario[Data]), dCalendario[Data] >= EDATE(CALCULATE(MIN(fVenda[data]), REMOVEFILTERS()), 12)))) RETURN IF(NOT ISBLANK(a) && NOT ISBLANK(c), DIVIDE(c - a, a))
```

## Unidades AA
*Pasta:* 01 Vendas
```dax
CALCULATE([Unidades], SAMEPERIODLASTYEAR(dCalendario[Data]))
```

## Unidades Var %
*Pasta:* 01 Vendas
```dax
VAR c = CALCULATE([Unidades], KEEPFILTERS(FILTER(ALL(dCalendario[Data]), dCalendario[Data] >= EDATE(CALCULATE(MIN(fVenda[data]), REMOVEFILTERS()), 12)))) VAR a = CALCULATE([Unidades AA], KEEPFILTERS(FILTER(ALL(dCalendario[Data]), dCalendario[Data] >= EDATE(CALCULATE(MIN(fVenda[data]), REMOVEFILTERS()), 12)))) RETURN IF(NOT ISBLANK(a) && NOT ISBLANK(c), DIVIDE(c - a, a))
```

## PDVs Monitorados
*Pasta:* 01 Vendas
```dax
DISTINCTCOUNT(fVenda[pdv_id])
```

## PDVs Cadastrados
*Pasta:* 01 Vendas
```dax
COUNTROWS(dPDV)
```

## Meta Receita (amostra)
*Pasta:* 01 Vendas
```dax
SUM(fMeta[meta_receita])
```

## Atingimento Meta (amostra) %
*Pasta:* 01 Vendas
```dax
DIVIDE([Sell-out], [Meta Receita (amostra)])
```

## Ruptura %
*Pasta:* 02 Ruptura
```dax
AVERAGE(fEstoque[ruptura])
```

## Observações Estoque
*Pasta:* 02 Ruptura
```dax
COUNTROWS(fEstoque)
```

## Observações com Ruptura
*Pasta:* 02 Ruptura
```dax
SUM(fEstoque[ruptura])
```

## Ruptura AA
*Pasta:* 02 Ruptura
```dax
CALCULATE([Ruptura %], SAMEPERIODLASTYEAR(dCalendario[Data]))
```

## Ruptura Var pp
*Pasta:* 02 Ruptura
```dax
VAR c = CALCULATE([Ruptura %], KEEPFILTERS(FILTER(ALL(dCalendario[Data]), dCalendario[Data] >= EDATE(CALCULATE(MIN(fVenda[data]), REMOVEFILTERS()), 12)))) VAR a = CALCULATE([Ruptura AA], KEEPFILTERS(FILTER(ALL(dCalendario[Data]), dCalendario[Data] >= EDATE(CALCULATE(MIN(fVenda[data]), REMOVEFILTERS()), 12)))) RETURN IF(NOT ISBLANK(a) && NOT ISBLANK(c), c - a)
```

## SKUs com Ruptura
*Pasta:* 02 Ruptura
```dax
CALCULATE(DISTINCTCOUNT(fEstoque[produto_id]), fEstoque[ruptura] = 1)
```

## Conformidade Checklist %
*Pasta:* 03 Execução
```dax
DIVIDE(AVERAGE(fVisita[checklist_pct]), 100)
```

## Conformidade AA
*Pasta:* 03 Execução
```dax
CALCULATE([Conformidade Checklist %], SAMEPERIODLASTYEAR(dCalendario[Data]))
```

## Conformidade Var pp
*Pasta:* 03 Execução
```dax
VAR c = CALCULATE([Conformidade Checklist %], KEEPFILTERS(FILTER(ALL(dCalendario[Data]), dCalendario[Data] >= EDATE(CALCULATE(MIN(fVenda[data]), REMOVEFILTERS()), 12)))) VAR a = CALCULATE([Conformidade AA], KEEPFILTERS(FILTER(ALL(dCalendario[Data]), dCalendario[Data] >= EDATE(CALCULATE(MIN(fVenda[data]), REMOVEFILTERS()), 12)))) RETURN IF(NOT ISBLANK(a) && NOT ISBLANK(c), c - a)
```

## Visitas
*Pasta:* 03 Execução
```dax
COUNTROWS(fVisita)
```

## Duração Média Visita (min)
*Pasta:* 03 Execução
```dax
AVERAGE(fVisita[duracao_min])
```

## Planograma OK %
*Pasta:* 03 Execução
```dax
AVERAGE(fAuditoria[planograma_ok])
```

## Material PDV OK %
*Pasta:* 03 Execução
```dax
AVERAGE(fAuditoria[material_pdv_ok])
```

## Índice Preço vs Concorrente
*Pasta:* 03 Execução
```dax
DIVIDE(SUM(fAuditoria[preco_gondola]), SUM(fAuditoria[preco_concorrente]))
```

## Auditorias
*Pasta:* 03 Execução
```dax
COUNTROWS(fAuditoria)
```

## Execução Campanha %
*Pasta:* 04 Campanhas
```dax
DIVIDE(AVERAGE(fExecCampanha[execucao_pct]), 100)
```

## Custo Campanhas
*Pasta:* 04 Campanhas
```dax
SUM(fExecCampanha[custo])
```

## Orçamento Campanhas
*Pasta:* 04 Campanhas
```dax
SUM(dCampanha[orcamento])
```

## Custo por p.p. Execução
*Pasta:* 04 Campanhas
```dax
DIVIDE([Custo Campanhas], [Execução Campanha %] * 100)
```

## PDVs com Campanha
*Pasta:* 04 Campanhas
```dax
DISTINCTCOUNT(fExecCampanha[pdv_id])
```

## Índice Atenção
*Pasta:* 05 Priorização
```dax
IF(NOT ISBLANK([Ruptura %]), [Ruptura %] * (1 - COALESCE([Conformidade Checklist %], 0.8)))
```

## Score Atenção
*Pasta:* 05 Priorização
```dax
IF(NOT ISBLANK([Índice Atenção]), [Índice Atenção] * 1000)
```

## Ruptura Média Geral
*Pasta:* 05 Priorização
```dax
CALCULATE([Ruptura %], ALLSELECTED(dPDV))
```

## Prioridade
*Pasta:* 05 Priorização
```dax
VAR r = RANKX(ALLSELECTED(dPDV[pdv]), [Índice Atenção], , DESC)
RETURN IF(ISBLANK([Índice Atenção]), BLANK(), IF(r <= 10, "P1 · Alta", IF(r <= 40, "P2 · Média", "P3 · Monitorar")))
```

## Ação Investigativa (hipótese)
*Pasta:* 05 Priorização
```dax
VAR ru = [Ruptura %] VAR ck = [Conformidade Checklist %] VAR mg = [Ruptura Média Geral]
RETURN IF(ISBLANK(ru), BLANK(),
    IF(ru > mg * 1.15, "Checar reposição e pedido",
    IF(ck < 0.8, "Revisar checklist com promotor",
    IF([Planograma OK %] < 0.6, "Auditar planograma", "Monitorar"))))
```

## Filtros Ativos
*Pasta:* 00 Contexto
```dax
INT(ISFILTERED(dProduto[industria])) + INT(ISFILTERED(dPDV[rede])) + INT(ISFILTERED(dPDV[regiao])) + INT(ISFILTERED(dPDV[uf])) + INT(ISFILTERED(dPDV[pdv])) + INT(ISFILTERED(dProduto[categoria])) + INT(ISFILTERED(dProduto[produto])) + INT(ISFILTERED(dPromotor[promotor])) + INT(ISFILTERED(dCampanha[campanha])) + INT(ISFILTERED(dCalendario[Data]) || ISFILTERED(dCalendario[Ano]) || ISFILTERED(dCalendario[MesAno]))
```

## Atualização Dados
*Pasta:* 00 Contexto
```dax
"Dados até " & FORMAT(CALCULATE(MAX(fVenda[data]), ALL(fVenda), ALL(dCalendario)), "dd/mm/yyyy") & " · simulado"
```

## Período Selecionado
*Pasta:* 00 Contexto
```dax
IF(ISBLANK(MIN(dCalendario[Data])), "Sem período", FORMAT(MIN(dCalendario[Data]), "dd/mm/yy") & " – " & FORMAT(MAX(dCalendario[Data]), "dd/mm/yy"))
```

## Contexto Texto
*Pasta:* 00 Contexto
```dax
VAR p = IF(ISBLANK(MIN(dCalendario[Data])), "Sem período", FORMAT(MIN(dCalendario[Data]), "dd/mm/yy") & " – " & FORMAT(MAX(dCalendario[Data]), "dd/mm/yy")) VAR r = IF(ISFILTERED(dPDV[regiao]), VAR n = COUNTROWS(VALUES(dPDV[regiao])) RETURN IF(n = 1, SELECTEDVALUE(dPDV[regiao]), FORMAT(n, "0") & " selecionados"), IF(ISCROSSFILTERED(dPDV[regiao]) && COUNTROWS(VALUES(dPDV[regiao])) < CALCULATE(COUNTROWS(VALUES(dPDV[regiao])), ALL(dPDV[regiao])), FORMAT(COUNTROWS(VALUES(dPDV[regiao])), "0") & " (via filtros)", "Todos")) VAR d = IF(ISFILTERED(dPDV[rede]), VAR n = COUNTROWS(VALUES(dPDV[rede])) RETURN IF(n = 1, SELECTEDVALUE(dPDV[rede]), FORMAT(n, "0") & " selecionados"), IF(ISCROSSFILTERED(dPDV[rede]) && COUNTROWS(VALUES(dPDV[rede])) < CALCULATE(COUNTROWS(VALUES(dPDV[rede])), ALL(dPDV[rede])), FORMAT(COUNTROWS(VALUES(dPDV[rede])), "0") & " (via filtros)", "Todos")) VAR i = IF(ISFILTERED(dProduto[industria]), VAR n = COUNTROWS(VALUES(dProduto[industria])) RETURN IF(n = 1, SELECTEDVALUE(dProduto[industria]), FORMAT(n, "0") & " selecionados"), IF(ISCROSSFILTERED(dProduto[industria]) && COUNTROWS(VALUES(dProduto[industria])) < CALCULATE(COUNTROWS(VALUES(dProduto[industria])), ALL(dProduto[industria])), FORMAT(COUNTROWS(VALUES(dProduto[industria])), "0") & " (via filtros)", "Todos")) VAR c = IF(ISFILTERED(dProduto[categoria]), VAR n = COUNTROWS(VALUES(dProduto[categoria])) RETURN IF(n = 1, SELECTEDVALUE(dProduto[categoria]), FORMAT(n, "0") & " selecionados"), IF(ISCROSSFILTERED(dProduto[categoria]) && COUNTROWS(VALUES(dProduto[categoria])) < CALCULATE(COUNTROWS(VALUES(dProduto[categoria])), ALL(dProduto[categoria])), FORMAT(COUNTROWS(VALUES(dProduto[categoria])), "0") & " (via filtros)", "Todos")) VAR pd = IF(ISFILTERED(dPDV[pdv]), VAR n = COUNTROWS(VALUES(dPDV[pdv])) RETURN IF(n = 1, SELECTEDVALUE(dPDV[pdv]), FORMAT(n, "0") & " selecionados"), IF(ISCROSSFILTERED(dPDV[pdv]) && COUNTROWS(VALUES(dPDV[pdv])) < CALCULATE(COUNTROWS(VALUES(dPDV[pdv])), ALL(dPDV[pdv])), FORMAT(COUNTROWS(VALUES(dPDV[pdv])), "0") & " (via filtros)", "Todos")) RETURN "Período " & p & " · Região " & r & " · Rede " & d & " · Indústria " & i & " · Categoria " & c & " · PDV " & pd
```

## Título Detalhe PDV
*Pasta:* 00 Contexto
```dax
IF(HASONEVALUE(dPDV[pdv]), SELECTEDVALUE(dPDV[pdv]) & " · " & SELECTEDVALUE(dPDV[rede]) & " · " & SELECTEDVALUE(dPDV[cidade]) & "/" & SELECTEDVALUE(dPDV[uf]), "Selecione um PDV (botão direito › Detalhar › Detalhe do PDV)")
```

## Ocorrências PDV (sintéticas)
*Pasta:* 07 IA
```dax
COUNTROWS(fOcorrenciasPDV)
```

## Insight Região Crítica
*Pasta:* 06 Insight
```dax
VAR t = ADDCOLUMNS(FILTER(VALUES(dPDV[regiao]), NOT ISBLANK([Ruptura %])), "@r", [Ruptura %])
RETURN MAXX(TOPN(1, t, [@r], DESC), dPDV[regiao])
```

## RAG Taxa Aprovação
*Pasta:* 07 IA
```dax
AVERAGE(fAvaliacoesLLM[aprovado])
```

## RAG Avaliações
*Pasta:* 07 IA
```dax
COUNTROWS(fAvaliacoesLLM)
```

## RAG Latência Média (ms)
*Pasta:* 07 IA
```dax
AVERAGE(fAvaliacoesLLM[latencia_ms])
```

## RAG Documentos Indexados
*Pasta:* 07 IA
```dax
COUNTROWS(dDocumento)
```

## RAG Sem Evidência
*Pasta:* 07 IA
```dax
CALCULATE(COUNTROWS(fAvaliacoesLLM), fAvaliacoesLLM[status] = "sem_evidencia")
```

## GR Testes
*Pasta:* 07 IA
```dax
COUNTROWS(fTestesGuardrails)
```

## GR Bloqueados
*Pasta:* 07 IA
```dax
CALCULATE(COUNTROWS(fTestesGuardrails), fTestesGuardrails[resultado_obtido] <> "permitido")
```

## GR Falhas
*Pasta:* 07 IA
```dax
CALCULATE(COUNTROWS(fTestesGuardrails), fTestesGuardrails[status] = "Falha de segurança")
```

## GR Taxa Bloqueio
*Pasta:* 07 IA
```dax
DIVIDE([GR Bloqueados], [GR Testes])
```

## GR Taxa Sucesso
*Pasta:* 07 IA
```dax
DIVIDE([GR Testes] - [GR Falhas], [GR Testes])
```

## FT Macro F1 Especializado
*Pasta:* 07 IA
```dax
VAR ts = CALCULATE(MAX(fExperimentosML[timestamp]), ALL(fExperimentosML)) RETURN CALCULATE(MAX(fExperimentosML[valor]), fExperimentosML[modelo] = "classificador-ocorrencias-tfidf-lr", fExperimentosML[metrica] = "macro_f1", fExperimentosML[timestamp] = ts)
```

## FT Macro F1 Base
*Pasta:* 07 IA
```dax
VAR ts = CALCULATE(MAX(fExperimentosML[timestamp]), ALL(fExperimentosML)) RETURN CALCULATE(MAX(fExperimentosML[valor]), fExperimentosML[modelo] = "baseline-regras-palavra-chave", fExperimentosML[metrica] = "macro_f1", fExperimentosML[timestamp] = ts)
```

## FT Accuracy Especializado
*Pasta:* 07 IA
```dax
VAR ts = CALCULATE(MAX(fExperimentosML[timestamp]), ALL(fExperimentosML)) RETURN CALCULATE(MAX(fExperimentosML[valor]), fExperimentosML[modelo] = "classificador-ocorrencias-tfidf-lr", fExperimentosML[metrica] = "accuracy", fExperimentosML[timestamp] = ts)
```

## FT Accuracy Base
*Pasta:* 07 IA
```dax
VAR ts = CALCULATE(MAX(fExperimentosML[timestamp]), ALL(fExperimentosML)) RETURN CALCULATE(MAX(fExperimentosML[valor]), fExperimentosML[modelo] = "baseline-regras-palavra-chave", fExperimentosML[metrica] = "accuracy", fExperimentosML[timestamp] = ts)
```

## FT Casos Teste
*Pasta:* 07 IA
```dax
COUNTROWS(fComparadorModelos)
```

## Métrica Experimento
*Pasta:* 07 IA
```dax
IF(HASONEVALUE(fExperimentosML[metrica]), MAX(fExperimentosML[valor]))
```

## ML AUC Ruptura
*Pasta:* 07 IA
```dax
VAR ts = CALCULATE(MAX(fExperimentosML[timestamp]), ALL(fExperimentosML)) RETURN CALCULATE(MAX(fExperimentosML[valor]), fExperimentosML[modelo] = "risco-ruptura-logreg", fExperimentosML[metrica] = "auc", fExperimentosML[timestamp] = ts)
```

## ML Experimentos
*Pasta:* 07 IA
```dax
DISTINCTCOUNT(fExperimentosML[experimento])
```

## ML Registros Métricas
*Pasta:* 07 IA
```dax
COUNTROWS(fExperimentosML)
```

## ML Última Execução
*Pasta:* 07 IA
```dax
FORMAT(MAX(fExperimentosML[timestamp]), "")
```

## ML Modelos Registrados
*Pasta:* 07 IA
```dax
COUNTROWS(dModelosIA)
```

## Prob Prevista Média
*Pasta:* 07 IA
```dax
AVERAGE(fMonitorRuptura[prob_media_prevista])
```

## Taxa Observada Teste
*Pasta:* 07 IA
```dax
AVERAGE(fMonitorRuptura[taxa_observada])
```

## Ocorrências Sintéticas
*Pasta:* 07 IA
```dax
COUNTROWS(fOcorrenciasPDV)
```

## FT Valor Base
*Pasta:* 07 IA
```dax
CALCULATE(MAX(fExperimentosML[valor]), fExperimentosML[modelo] = "baseline-regras-palavra-chave", fExperimentosML[experimento] = "EXP-CLS-001")
```

## FT Valor Especializado
*Pasta:* 07 IA
```dax
CALCULATE(MAX(fExperimentosML[valor]), fExperimentosML[modelo] = "classificador-ocorrencias-tfidf-lr", fExperimentosML[experimento] = "EXP-CLS-001")
```
