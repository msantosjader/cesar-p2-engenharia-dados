-- Proposta para revisão. Não aplicada automaticamente.
-- Requer autorização e schema previamente existente.

CREATE TABLE public.pnad_silver (
	observation_id VARCHAR(64) NOT NULL, 
	tabela TEXT NOT NULL, 
	variavel_id TEXT NOT NULL, 
	variavel TEXT NOT NULL, 
	unidade TEXT NOT NULL, 
	nivel TEXT NOT NULL, 
	localidade_id TEXT NOT NULL, 
	localidade TEXT NOT NULL, 
	classificacoes TEXT NOT NULL, 
	periodo TEXT NOT NULL, 
	data_periodo DATE NOT NULL, 
	ano INTEGER NOT NULL, 
	trimestre INTEGER, 
	valor FLOAT, 
	valor_original TEXT NOT NULL, 
	status_valor TEXT NOT NULL, 
	run_id TEXT NOT NULL, 
	PRIMARY KEY (observation_id)
)

;
