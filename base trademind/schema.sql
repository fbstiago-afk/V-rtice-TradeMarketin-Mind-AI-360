
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
