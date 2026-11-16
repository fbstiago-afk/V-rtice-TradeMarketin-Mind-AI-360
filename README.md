# Vértice TradeMind AI 360

**Cockpit de Trade Marketing que separa o que é análise do que é inteligência artificial — e mostra as duas camadas funcionando, com evidência.**

Power BI (PBIP/TMDL/PBIR gerado por código) + RAG com API real + Guardrails testados + registro MLOps.
Dados fictícios, gerados por script. Resultados de IA são telemetria de execuções reais do pipeline local.

![Home](docs/screenshots/01-home.jpg)

🎥 **Demonstração (58s, sem áudio):** [`docs/TradeMind_AI360_demo.mp4`](docs/TradeMind_AI360_demo.mp4)

---

## As duas camadas

| Camada | O que o usuário faz |
|---|---|
| **1 · Trade Marketing Intelligence** | Analisa sell-out, ruptura, execução de PDV, campanhas e promotores — com filtros sincronizados, drill-through e tabelas inteligentes. |
| **2 · AI Intelligence Lab** | Pergunta ao RAG e vê as fontes, compara modelo base × especializado, audita guardrails de segurança e acompanha experimentos de ML. |

A diferença importante: o AI Lab não *explica* o que é RAG, Fine-tuning, Guardrails e MLOps — ele **executa, avalia e registra** cada um deles, e o Power BI lê essa telemetria.

---

## Diferenciais técnicos

**1. Relatório como código.** As 7 páginas, 170 visuais, 113 medidas DAX, 17 bookmarks, 3 papéis de RLS e o drill-through são gerados por um script Python (`02_POWER_BI/build_pbip.py`) que escreve TMDL e PBIR direto. O relatório inteiro é reprodutível a partir do repositório — nenhum passo manual de montagem.

**2. Componentes HTML/SVG renderizados por DAX.** Cards executivos com micrográficos, sparklines, barras em célula, selos de status e a barra de contexto de filtros são SVG construídos dentro da medida, sem visual externo e sem dependência de marketplace.

![Trade Performance](docs/screenshots/07-performance-ruptura.jpg)

**3. Chat RAG de verdade dentro do Power BI.** Um visual personalizado em TypeScript (`.pbiviz`, código em `05_CUSTOM_VISUAL/`) chama a API local por HTTP, recebe a resposta com as fontes e exibe a latência medida. Não é um chat simulado com texto fixo: quando a API está desligada, o visual mostra "API offline".

![RAG](docs/screenshots/11-ailab-rag-resposta.jpg)

**4. Guardrails testados, não ilustrados.** Dez cenários de segurança (acesso cross-tenant, escopo regional, dados pessoais, prompt injection na pergunta e no documento recuperado, consulta arbitrária, payload inválido, usuário desconhecido) são executados contra o backend a cada run. O painel lê o resultado real: **10/10 com o comportamento esperado** na última execução.

![Guardrails](docs/screenshots/14-ailab-guardrails.jpg)

**5. Segurança em duas camadas.** RLS dinâmico no modelo semântico por `USERPRINCIPALNAME()`, derivado da tabela de regras de acesso do próprio banco — e as mesmas regras reaplicadas no backend da API, porque RLS de Power BI não protege um serviço externo.

**6. Ferramentas analíticas tipadas em vez de RAG para número.** Perguntas numéricas vão para `get_metric`, `compare_periods`, `rank_dimensions` e `get_metadata`, com validação de parâmetros e escopo por perfil. O RAG responde definição e procedimento; indicador vem do modelo, não do texto.

**7. Integridade analítica declarada na interface.** Sell-out é amostrado e está escrito no card. Ruptura é *observada* nas combinações auditadas — ausência de observação não vira estoque zero. Campanhas não têm grupo de controle, então o painel mostra execução e custo, e diz que ROI incremental não é calculável.

**8. O modelo preditivo foi rejeitado — e isso está no dashboard.** Dois experimentos de risco de ruptura (Regressão Logística e Gradient Boosting com defasagens de vendas) deram **AUC ≈ 0,50**, equivalente a acaso, e a correlação com a semana anterior é ≈ 0. O gerador fictício sorteia ruptura aleatoriamente. O catálogo de modelos marca os dois como **Rejeitado** e nenhuma previsão é publicada.

![MLOps](docs/screenshots/15-ailab-mlops.jpg)

---

## Resultados verificados

Medidos na última execução do pipeline (`03_AI/run_pipeline.py`) e validados no Power BI Desktop.

| Componente | Status | Evidência |
|---|---|---|
| Modelo semântico (22 tabelas, 113 medidas) | Implementado e testado | Carga sem erros; medidas consultadas via DAX |
| 3 páginas principais + 4 técnicas | Implementado e testado | Navegação, filtros, bookmarks e reset validados |
| Drill-through Radar → Detalhe do PDV | Implementado e testado | `docs/screenshots/05-detalhe-pdv.jpg` |
| RLS dinâmico + papéis demo | Implementado e testado | "Exibir como" `promotor.sul`: vendas/estoque vazios, só região Sul |
| RAG (9 documentos, 29 trechos recuperados) | Implementado e testado | 5/8 avaliações aprovadas (62,5%), latência média 4,4 ms |
| Guardrails (10 cenários) | Implementado e testado | 10/10 conforme esperado · 9 bloqueios corretos |
| Classificador de ocorrências | Implementado e testado | macro-F1 **0,760** vs **0,738** da base por regras; acurácia 80,4% |
| API + autenticação por token | Implementado e testado | 9/9 testes (token forjado, expirado, sem auth, sem permissão) |
| Visual de chat `.pbiviz` | Protótipo funcional | Conectado à API local; Service exige HTTPS |
| Risco de ruptura (2 experimentos) | **Rejeitado** | AUC 0,500 e 0,495 — sem sinal nos dados |
| Fine-tuning de LLM | Bloqueado por dependência | Dataset JSONL pronto; sem GPU/credencial |

---

## Arquitetura

```text
SQLite fictício (525.600 vendas · 299.520 obs. de estoque · 50.058 auditorias · 240 PDVs · 350 SKUs)
        │
        ├── 01_DATA/build_star.py ──► modelo estrela em CSV + checagens de qualidade
        │
        ├── 03_AI/run_pipeline.py ──► RAG · guardrails · classificador · experimentos ML
        │                             └─► telemetria (CSV) consumida pelo Power BI
        │
        ├── 04_API/api.py ──────────► /ask (RAG) · /tool (métricas tipadas) · auth HMAC + auditoria
        │                                   ▲
        │                                   │ HTTP
        └── 02_POWER_BI/build_pbip.py ──► TMDL + PBIR ──► Power BI Desktop ──► visual .pbiviz
```

---

## Telas

| | |
|---|---|
| ![Filtros](docs/screenshots/02-painel-filtros.jpg) Painel de filtros oculto | ![Filtro aplicado](docs/screenshots/03-home-filtro-sudeste.jpg) Barra de contexto reage ao filtro |
| ![Detalhe](docs/screenshots/05-detalhe-pdv.jpg) Drill-through do PDV | ![Campanhas](docs/screenshots/09-performance-campanhas.jpg) Campanhas sem inferência causal |
| ![Fine-tuning](docs/screenshots/13-ailab-finetuning.jpg) Comparador base × especializado | ![Bloqueio](docs/screenshots/12-ailab-guardrail-bloqueio.jpg) Guardrail bloqueando no chat |

---

## Como executar

Requisitos: Power BI Desktop, Python 3.10+ (`pip install pandas scikit-learn`), Node 18+ apenas para recompilar o visual.

```bash
python "base trademind/build.py"     # gera o SQLite fictício (seed fixa)
python 01_DATA/build_star.py         # SQLite -> modelo estrela em CSV
python 03_AI/run_pipeline.py         # executa RAG, guardrails, ML e grava a telemetria
python 02_POWER_BI/build_pbip.py     # gera TMDL + PBIR (feche o Power BI antes)
python 06_TESTS/test_api.py          # 9 testes de API e autenticação
```

Abra `02_POWER_BI/TradeMind_AI360.pbip` e ajuste o parâmetro `PastaDados` para o caminho de `01_DATA/processed` na sua máquina. Para o chat: `iniciar_api.bat` (Windows) ou `python 04_API/api.py`.

Detalhes de execução, segurança e pendências: [`docs/EXECUCAO.md`](docs/EXECUCAO.md) · medidas DAX: [`02_POWER_BI/MEDIDAS_DAX.md`](02_POWER_BI/MEDIDAS_DAX.md)

---

## Limitações conhecidas

- **Dados são fictícios.** Gerados por `base trademind/build.py` com seed fixa. Nenhum número representa operação real.
- **O RAG é extrativo.** Não há LLM generativo conectado: a resposta é composta de trechos recuperados, sempre com a fonte citada. Isso está escrito no rodapé do próprio chat.
- **Sem previsão de ruptura.** Ver item 8 acima.
- **Fine-tuning de LLM pendente**, autenticação corporativa (OIDC/Entra ID) não configurada, chat ainda não publicável no Service.

O repositório não inclui o SQLite (67 MB) nem as tabelas-fato em CSV: ambos são regenerados pelos scripts acima em poucos minutos.

---

*Projeto de portfólio. Identidade visual Vértice Trade Marketing usada como estudo de caso.*
