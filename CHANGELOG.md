# Changelog

## [feature/foundation] — 2026-11-18

### Corrigido
- Encadeamento do modo `pnad-projeto` em `main.py`, reutilizando as sete consultas existentes.
- Fechamento do cliente `Load` após execução ou falha.
- Instalação base consistente entre `pyproject.toml`, `uv.lock` e `requirements.txt`.

### Adicionado — Aula 08
- Snapshots Bronze por execução em coleção separada, hashes e leitura de carga completa.
- Transformação longa preservando variáveis, localidades, categorias, períodos e valores originais.
- Distinção entre zero absoluto e valores ausentes/suprimidos conforme convenções IBGE.
- PostgreSQL configurável com TLS remoto, validação de schema, upsert transacional e releitura.
- Entrada `run_project.py` e geração de DDL para revisão, sem aplicação automática.

### Adicionado — Aula 09
- Flow e tasks Prefect reutilizando os serviços da ETL, com logs e retries limitados.
- Recusa de carga parcial e confirmação explícita de escritas na nova entrada.

### Adicionado — Aula 10
- Transformação PySpark com o mesmo contrato Silver do pandas e coleta local limitada.
- Testes de equivalência DataFrame/Spark SQL e integração com PostgreSQL local.

### Validação e documentação
- Testes de regressão, integridade, idempotência, transações e orquestração local.
- Validação pública das sete consultas IBGE e posterior validação autorizada de
  escrita no Atlas/Neon; evidências em `docs/validacao-integracao-atlas-neon.md`.
- Detalhes e limitações em `docs/evolucao-aulas-08-10.md`.

## [pnad-projeto] — 2026-09-02

### Adicionado
- `src/mongo.py`: conector MongoDB Atlas (`get_client`, `ping`, `get_database`, `get_collection`)
- `src/ibge.py`: catálogo `TABELAS_PNAD_PROJETO` com 7 tabelas PNAD Anual (N6 Recife) + método `montar_url_projeto()`
- `src/load.py`: método `Load.load_mongo()` com flatten, upsert e tratamento de ausentes
- Modo `pnad-projeto` no CLI e `main.py`: captura 7 tabelas de uma só vez e insere no MongoDB

### Removido
- `src/atlas_mongodb.py` e `src/mongodb_cloud.py` (duplicatas substituídas por `src/mongo.py`)

### Alterado
- `src/cli.py`: novo menu de seleção de modo (Atividade1 / pnad-projeto)
- `src/extract.py`: timeout de 30s e retry em 429/5xx
- `docs/planejamento-crispdm.md`: seção 2.1 reescrita com 7 tabelas e justificativa biológica

## [atividade_1] — 2026-08-16

### Adicionado
- `src/ibge.py`: catálogo de variáveis, sexo e UF + classe `QueryBuilder` (monta a URL)
- `src/cli.py`: menu interativo (`CLI`) com validação, contagem de erros e opção de saída
- `main.py`: orquestração do fluxo (CLI → Extract → Load)
- `Extract.get_pnad(url)`: consulta parametrizável com validação de status HTTP
- Saída com data/hora: `saidas/pnad_AAAAMMDD_HHMMSS.json`

### Alterado
- `Extract` e `Load`: tratamento de erros e mensagens de status

## [aula_2] — 2026-08-12

### Adicionado
- Extrator PNAD Contínua (Tabela 4093) com as classes `Extract` e `Load` (URL fixa)
- Saída em `saidas/pnad.json`
