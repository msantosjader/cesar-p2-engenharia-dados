# César School — Banco de Dados (2º Período) — Engenharia de Dados

Extração de dados da **PNAD Contínua (IBGE)** com Python e Programação Orientada a Objetos (POO).

Este documento descreve o estado atual da solução (tag `atividade_1`): extração da PNAD Contínua (Tabela 4093), parametrizável por variável, sexo e UF.

## Evolução

| Tag | Conteúdo |
|-----|----------|
| `aula_2` | Extrator básico da Tabela 4093 com as classes `Extract` e `Load` (URL fixa) |
| `atividade_1` | Solução parametrizável: `QueryBuilder` monta a URL, CLI interativo, consulta com validação de status HTTP |

A solução é reutilizada para qualquer combinação de variáveis, sexo e UF da Tabela 4093 — sem código novo por consulta, apenas novos parâmetros.

## Como rodar

```bash
python main.py
```

O programa pergunta interativamente:

- **Variáveis**: 4096 (participação), 4099 (desocupação), 12466 (informalidade)
- **Sexo**: 4 (Homens), 5 (Mulheres), 6794 (Total)
- **UF**: códigos do IBGE (ex.: 26 = Pernambuco)

Regras do menu:

- **ENTER** = todos os itens disponíveis
- **0** = sair
- 3 respostas inválidas = programa encerra

A URL montada é consultada na API e o resultado é salvo em `saidas/pnad_AAAAMMDD_HHMMSS.json`.

## Estrutura

```
main.py            orquestra o fluxo: CLI → Extract → Load
src/
├── ibge.py        catálogo (variáveis, sexo, UF) + QueryBuilder (monta a URL)
├── extract.py     Extract.get_pnad(url) — consulta a API e valida status HTTP
├── load.py        Load.load_json() — salva o JSON em saidas/
└── cli.py         CLI — menu interativo
```

## Exemplo

```
$ python main.py
QueryBuilder IBGE PNAD para a Atividade 1

Escolha as variáveis (ENTER = todas, 0 = sair):
  Opções: 4096, 4099, 12466
>
```
