# TradeMind AI 360 — Base sintética

Banco SQLite 100% fictício e reproduzível. Período: 2025-01-01 a 2026-12-31 (inclui datas futuras simuladas).

## Tabelas e contagens
- industria: 3
- rede: 5
- pdv: 240
- produto: 350
- promotor: 80
- campanha: 12
- venda_diaria: 525,600
- estoque_semanal: 299,520
- visita: 25,029
- auditoria: 50,058
- execucao_campanha: 720
- meta_mensal: 5,760
- documento: 4
- usuario: 5
- regra_acesso: 20
- exemplo_finetuning: 5
- avaliacao_ia: 4

## Arquivos
- trademind_ai360.sqlite: banco SQLite pronto para consulta.
- schema.sql: DDL relacional.
- build.py: gerador com semente fixa.
- rag_documentos.jsonl: corpus inicial para indexação vetorial (ainda sem embeddings).
- finetuning_exemplos.jsonl: exemplos didáticos, insuficientes para um fine-tuning robusto.

## Limitações importantes
- Sell-out é amostrado em 3 SKUs por PDV/dia; não representa vendas completas do sortimento.
- Estoque é fotografado semanalmente para 12 SKUs por PDV; não pode ser reconciliado diretamente com vendas diárias.
- Campanhas não possuem grupo controle nem atribuição causal. Não calcular ROI incremental sem modelagem adicional.
- Permissões são registros demonstrativos: a aplicação precisa impor filtros por indústria/região antes de consultar dados ou recuperar documentos.
- Dados e pessoas são inventados; padrões não devem ser tratados como evidência de mercado.
