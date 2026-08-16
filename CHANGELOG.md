# Changelog

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
