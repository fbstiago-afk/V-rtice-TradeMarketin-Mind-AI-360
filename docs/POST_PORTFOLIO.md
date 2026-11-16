# Texto para o site do portfólio

---

## Título

**Vértice TradeMind AI 360 — cockpit de Trade Marketing com camada de IA auditável**

*Subtítulo:* Power BI gerado por código, RAG com API real, guardrails testados e registro de experimentos de machine learning.

---

## Descrição curta

Cockpit de Trade Marketing com duas camadas separadas: a análise comercial (sell-out, ruptura, execução de PDV e campanhas) e um laboratório onde RAG, guardrails de segurança, classificação especializada e MLOps são executados, avaliados e registrados — com o Power BI lendo essa telemetria real.

O relatório inteiro (7 páginas, 170 visuais, 113 medidas DAX) é gerado por script Python em TMDL/PBIR, e por isso é reprodutível a partir do repositório. Dados fictícios, gerados com seed fixa.

---

## Contexto e objetivos

Dashboards de Trade Marketing costumam parar no mesmo lugar: muitos gráficos espalhados, indicadores sem denominador declarado e, mais recentemente, um bloco chamado "IA" que é texto estático fingindo ser insight gerado.

O objetivo aqui foi construir o oposto, em três frentes:

1. **Experiência de produto, não relatório.** Navegação superior, painel de filtros oculto, barra de contexto mostrando os filtros realmente aplicados, drill-through por PDV e poucos gráficos por página — cada área da tela respondendo a uma pergunta ou permitindo uma ação.
2. **Integridade analítica explícita.** Sell-out é amostrado e o card diz isso. Ruptura é observada nas combinações auditadas, e ausência de observação não vira estoque zero. Campanhas não têm grupo de controle, então execução e custo são exibidos, e ROI incremental é declarado como não calculável.
3. **IA que pode ser auditada.** Em vez de explicar o que são RAG, fine-tuning, guardrails e MLOps, construir um ambiente em que essas tecnologias rodam de verdade, produzem logs e são avaliadas — e o relatório consome esses logs.

O cenário é fictício: três indústrias, cinco redes, 240 PDVs, 350 SKUs e dois anos de operação simulada (525.600 vendas diárias, 299.520 observações de estoque, 50.058 auditorias de produto).

---

## Metodologia / abordagem

**Engenharia de dados.** Banco SQLite fictício gerado por script com seed fixa, auditado antes de qualquer medida: órfãos, duplicidades, valores negativos, consistência entre saldo e sinalização de ruptura, cobertura temporal. Modelagem em estrela com dimensões compartilhadas e calendário próprio, com o período simulado futuro identificado como tal.

**Modelo semântico como código.** Todo o modelo (22 tabelas, 21 relacionamentos, 113 medidas em pastas, 3 papéis de RLS) e todo o relatório (7 páginas, 170 visuais, 17 bookmarks, drill-through, páginas de tooltip) são escritos por um gerador Python que emite TMDL e PBIR. Cada correção vira uma alteração no gerador e uma regeração completa — não um ajuste manual que se perde na próxima versão.

**Componentes visuais em SVG via DAX.** Cards executivos com micrográficos, sparklines, barras em célula, selos semânticos e a barra de contexto de filtros são SVG construídos dentro da medida, com tratamento de BLANK, escape de texto dinâmico e estado vazio resolvido. Sem dependência de visual de marketplace.

**Camada de IA (Python).** Recuperação híbrida TF-IDF com re-ranking por cobertura de termos ponderada por IDF; ferramentas analíticas tipadas (`get_metric`, `compare_periods`, `rank_dimensions`, `get_metadata`) com validação de parâmetros e escopo por perfil; guardrails de entrada e de contexto recuperado; classificador supervisionado de ocorrências com separação por template para impedir vazamento entre treino e teste; e um registro de experimentos em que cada execução acrescenta métricas ao histórico.

**Serviço e segurança.** API local em Python com autenticação por token HMAC-SHA256 com expiração, limite de requisições, validação de payload e auditoria. RLS dinâmico no modelo semântico por `USERPRINCIPALNAME()`, derivado da própria tabela de regras de acesso — e as mesmas regras reaplicadas no backend, porque RLS de Power BI não protege um serviço externo.

**Integração com o relatório.** Um visual personalizado em TypeScript (`.pbiviz`) dentro do Power BI chama a API por HTTP, exibe a resposta com as fontes citadas, a latência medida e o estado real da conexão.

---

## Desafios e aprendizados

**Gerar PBIR à mão exige validar no Desktop, não no JSON.** Vários detalhes do formato só aparecem quando o Power BI abre o arquivo: propriedades que exigem seletor explícito, páginas de tooltip que precisam de um campo próprio, largura de imagem que precisa ser fixada para a célula não criar barra de rolagem. O método que funcionou foi configurar o recurso uma vez pela interface, ler o JSON que o Desktop gravou e levar esse formato de volta ao gerador.

**RAG não é busca.** A primeira versão recuperava trechos por similaridade pura e respondia a "qual a previsão do tempo?" com um parágrafo do glossário. Três mudanças resolveram: stopwords de domínio, re-ranking por cobertura de termos ponderada por IDF e um limiar mínimo de relevância que permite a resposta "não encontrei evidência suficiente". A taxa de aprovação nas avaliações subiu de 37,5% para 62,5% sem afrouxar o critério de teste.

**Separar treino e teste por frase não basta.** Dividir exemplos sintéticos aleatoriamente inflava a acurácia: variações da mesma frase-base caíam nos dois lados. A separação passou a ser por template, e a métrica caiu para um valor honesto.

**Guardrail de prompt injection precisa cobrir o documento recuperado.** Bloquear a pergunta do usuário é o caso fácil. O caso real é a instrução escondida dentro de um documento que o RAG recupera — tratada como dado e sanitizada antes de compor a resposta.

**Nem todo bloqueio é problema de modelagem.** O fine-tuning de LLM ficou pendente por dependência de infraestrutura (sem GPU e com o repositório de modelos inacessível pela rede). A decisão foi preparar o dataset, deixar o pipeline pronto e registrar o estado como "Treinamento pendente" no catálogo — em vez de chamar prompt engineering de fine-tuning.

**O aprendizado mais útil foi sobre o que não publicar.** Ver dois modelos preditivos falharem e resistir à tentação de publicar a previsão mesmo assim é uma decisão de engenharia, não de modelagem.

---

## Insights e descobertas

**A ruptura da base fictícia é aleatória — e descobrir isso tinha valor.** Dois experimentos independentes de risco de ruptura, um com Regressão Logística sobre defasagens de estoque e outro com Gradient Boosting incluindo defasagens de vendas, chegaram a AUC 0,500 e 0,495, com correlação ≈ 0 entre a ruptura de uma semana e a anterior. A conclusão não é "o modelo ficou ruim": é que o gerador de dados sorteia ruptura sem dependência temporal, e nenhum modelo honesto vai prever isso. Ambos estão no catálogo como **Rejeitado**, com a justificativa visível.

**A especialização ganhou da regra, mas pouco — e isso é informação.** O classificador supervisionado alcançou macro-F1 0,760 contra 0,738 da base por palavra-chave. Em um conjunto sintético com vocabulário controlado, uma regra simples vai longe; o ganho real da especialização aparece na precisão macro (0,900 contra 0,705), ou seja, em errar menos quando afirma uma categoria.

**Guardrail no modelo semântico não é guardrail.** O teste de acesso cross-tenant só passou porque a restrição por indústria é aplicada no backend da API. Um usuário consultando a API diretamente ignoraria completamente o RLS do relatório. A segurança precisou ser reimplementada em cada camada.

**Barra de contexto muda o comportamento de quem usa.** Exibir os filtros efetivamente aplicados, com contagem de filtros ativos e tratamento de seleção total e de filtro cruzado, elimina a dúvida mais cara em reunião: "esse número está filtrado por quê?".

---

## Resultado e impacto

Entrega funcional, validada no Power BI Desktop:

- **Relatório completo** com 3 páginas principais e 4 técnicas, 170 visuais, 113 medidas DAX, navegação, painel de filtros sincronizados, reset, drill-through por PDV e identidade visual aplicada.
- **Modelo semântico** com 22 tabelas carregando sem erro, RLS dinâmico validado por simulação de usuário (como promotor regional, vendas e estoque ficam vazios e a conformidade mostra apenas a região autorizada).
- **RAG** sobre 9 documentos, com citação de fontes e recusa declarada por falta de evidência: 5 de 8 avaliações aprovadas, latência média de 4,4 ms.
- **Guardrails**: 10 cenários de segurança executados contra o backend, 10/10 com o comportamento esperado, 9 bloqueios corretos.
- **Classificador de ocorrências**: macro-F1 0,760 contra 0,738 da base, acurácia 80,4%, com separação por template.
- **API**: 9 de 9 testes passando, incluindo token forjado, token expirado, requisição sem autenticação e perfil sem permissão.
- **Visual de chat** em TypeScript funcionando dentro do Power BI Desktop contra a API local.
- **Registro MLOps** com 5 experimentos, 7 modelos catalogados e 137 métricas acumuladas, incluindo os dois modelos rejeitados.

O impacto que me interessa demonstrar não é o número bonito: é que cada afirmação da interface tem rastro. Indicador tem denominador declarado, resposta de IA tem fonte citada, teste de segurança tem timestamp, modelo tem status real — e o que não funcionou aparece marcado como não funcionou.

**Pendências declaradas:** fine-tuning de LLM (sem infraestrutura), geração generativa no RAG (respostas são extrativas, com fonte), autenticação corporativa OIDC/Entra ID e publicação do chat no Power BI Service (exige API em HTTPS).

*Dados fictícios gerados por script com seed fixa. Nenhum número representa operação real.*

**Repositório:** https://github.com/fbstiago-afk/V-rtice-TradeMarketin-Mind-AI-360
