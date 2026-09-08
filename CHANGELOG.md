# Changelog

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
