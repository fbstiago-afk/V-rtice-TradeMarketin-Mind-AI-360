# Vértice TradeMind AI 360

**Abrir:** `02_POWER_BI/TradeMind_AI360.pbip` (Power BI Desktop) → Atualizar.
Os dados vêm dos CSVs de `01_DATA/processed` (parâmetro `PastaDados` = `E:\Projetos BI\20 - TradeMind AI 360\01_DATA\processed\`). Se mover a pasta, altere o parâmetro.

## Pipeline (Python 3.10+, `pip install pandas scikit-learn`)
1. `python 01_DATA/build_star.py` — SQLite → modelo estrela + `01_DATA/quality/data_quality.json`
2. `python 03_AI/run_pipeline.py` — avaliação RAG, testes de guardrails, classificador de ocorrências, modelo de ruptura, registro MLOps (append em `fExperimentosML.csv`)
3. `python 02_POWER_BI/build_pbip.py` — regenera TMDL/PBIR (feche o Desktop antes; sobrescreve o projeto)
4. API local: **duplo clique em `iniciar_api.bat`** (modo demo, usado pelo chat do Power BI) ou `python 04_API/api.py` (exige token: `python 04_API/auth.py gestor.demo` → header `Authorization: Bearer <token>`)
5. `python 06_TESTS/test_api.py` — 9 testes de API/autenticação
6. Visual de chat: `05_CUSTOM_VISUAL/` (fonte TypeScript + `.pbiviz`). Rebuild: `npm i -g powerbi-visuals-tools && pbiviz package`; copiar `resources/*.pbiviz.json` do pacote para `05_CUSTOM_VISUAL/registered/...` e rodar o passo 3.

## Segurança
- RLS no modelo: papel **Acesso por Usuário (dinâmico)** (USERPRINCIPALNAME → `dUsuarioAcesso`, derivado de `usuario` + `regra_acesso`) e papéis demo. Teste: Modelagem › Exibir como › Outro usuário `promotor.sul@vertice.demo`.
- API: token HMAC-SHA256 com expiração (segredo em `TRADEMIND_SECRET` ou `04_API/.secret`, fora do relatório), limite de 30 req/min por usuário, validação de payload, auditoria em `03_AI/mlops/api_audit.csv`.
- O RLS do Power BI não protege a API: as regras são reaplicadas no backend.



## Natureza dos dados
Banco fictício (2025–2026). Datas > 14/11/2026 = simulado futuro. `fOcorrenciasPDV` e o dataset de classificação são sintéticos (`sintetico=1`).
Medidas documentadas em `02_POWER_BI/MEDIDAS_DAX.md`.

## Pendências
- **Fine-tuning de LLM** — bloqueado: Hugging Face inacessível pela rede e sem GPU. Dataset `03_AI/finetuning/*_chat.jsonl` pronto.
- **Geração generativa no RAG** — sem LLM/credencial; respostas são extrativas (trechos + fontes).
- **Modelo de risco de ruptura** — dois experimentos (LogReg e GBM com vendas) com AUC ≈ 0,50 e correlação lag-1 ≈ 0: a ruptura simulada é aleatória; não há previsão a publicar.
- **Autenticação corporativa (OIDC/Entra ID)** — exige tenant; `auth.verify()` é o ponto de troca.
- **Tooltips de página** — páginas `tt_kpi`/`tt_ia` e referências configuradas (validadas no painel do Desktop), mas nos testes o Desktop exibiu o tooltip padrão; requer verificação manual.
- **Chat no Power BI Service** — o visual usa `http://127.0.0.1` (modo demo local); publicação exige API em HTTPS e domínio liberado nos privilégios do visual.
