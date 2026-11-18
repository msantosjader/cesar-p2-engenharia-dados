# Evolução incremental — aulas 08, 09 e 10

Data de validação: 18/11/2026. Branch: `feature/foundation`.

## Escopo e compatibilidade

O projeto continua organizado em `main.py`, classes em `src/`, configuração por
ambiente e catálogo próprio da PNAD. Nenhum endpoint, nome de recurso ou segredo
do professor foi incorporado. O planejamento CRISP-DM continua válido.

O fluxo anterior permanece em `python main.py`. A opção 1 mantém a consulta 4093
e a escrita em `ibge_database.pnad_extractions`. A opção 2 agora percorre as sete
tabelas já catalogadas, em vez de enviar a string `pnad-projeto` como URL. Essa
correção reutiliza `CLI`, `QueryBuilder`, `Extract` e `Load.save_to_mongodb`.
O cliente de carga é fechado ao finalizar ou falhar.

**O fluxo anterior continua com inserções simples e pode duplicar dados.** A
idempotência descrita abaixo pertence à nova entrada opt-in; não se alterou o
contrato de escrita legado nem se migraram documentos históricos.

## Mapeamento por aula

| Aula | Funcionalidade | Arquivos principais | Reuso |
|---|---|---|---|
| Pré-requisito | Conectar modo das sete tabelas | `main.py`, `src/load.py` | CLI, catálogo, extração e método de escrita existentes |
| 08 | Bronze por execução, transformação pandas e Silver PostgreSQL | `src/bronze.py`, `src/transform.py`, `src/postgres.py`, `src/pipeline.py`, `run_project.py` | `Extract`, `QueryBuilder`, `TABELAS_PNAD_PROJETO`, `Mongo`, `MONGODB_URI` |
| 09 | Tarefas e flow Prefect | `orchestrate_prefect.py` | Serviços de `src/pipeline.py`; nenhuma segunda implementação de ETL |
| 10 | Transformação PySpark com mesmo contrato | `src/transform_spark.py` | Validação de formato/identidade compartilhada, mesma leitura Bronze e carga Silver |

Também foram atualizados `.env_example`, `pyproject.toml`, `uv.lock`,
`requirements.txt`, README e changelog. Os testes estão em `tests/`; o DDL
proposto está em `docs/sql/pnad_silver.sql`. `scripts/validate_ibge.py` permite
repetir a validação pública de leitura sem conectar a bancos.

## Arquitetura da nova entrada

```text
preflight (configuração + schema Silver; nenhuma escrita)
  → API IBGE (sete tabelas anuais)
  → validação de todas as respostas
  → Bronze MongoDB (coleção separada, snapshots por run_id/tabela)
  → leitura da mesma execução completa
  → transformação pandas OU Spark
  → upsert PostgreSQL + releitura na mesma transação
```

O modo Spark faz conversões de números, datas, ano, trimestre e status com a API
DataFrame. A travessia do JSON e a identidade das observações são compartilhadas
para evitar divergências entre os mecanismos. Não foi adicionada uma fonte do
Banco Central, um SQLite de produção ou infraestrutura de cluster.

## Contrato Bronze

Cada documento novo contém `_id = run_id:tabela`, `run_id`, `tabela`,
`source_url`, `captured_at`, `format_version`, `payload_hash` e `payload` bruto.

- A coleção é configurada explicitamente e separada das duas combinações
  legadas encontradas no código.
- A escrita utiliza `$setOnInsert` e a unicidade nativa de `_id`, sem criar índices.
- Repetir a escrita do mesmo snapshot não duplica documentos.
- Reutilizar o mesmo `run_id` com conteúdo/consulta diferente falha, preservando
  o snapshot anterior. Uma nova coleta deve usar novo identificador.
- A leitura exige exatamente as sete tabelas da execução solicitada e confere hashes.
- Falhas parciais podem deixar snapshots Bronze incompletos; estes não alimentam
  a Silver. Não se promete transação distribuída entre MongoDB e PostgreSQL.
- O limite BSON de 16 MiB é verificado antes da escrita. Volumes maiores exigem
  particionamento, que não faz parte desta implementação acadêmica.

Documentos legados não são reclassificados nem lidos automaticamente pela nova ETL.

## Contrato Silver

Uma linha representa uma combinação de tabela, variável, nível territorial,
localidade, período e códigos de classificações/categorias. `observation_id`
é o SHA-256 dessa identidade; rótulos e `run_id` não alteram a chave.

| Colunas | Significado |
|---|---|
| `observation_id` | Chave primária estável |
| `tabela`, `variavel_id`, `variavel`, `unidade` | Identificação e unidade da medida |
| `nivel`, `localidade_id`, `localidade` | Granularidade e localidade |
| `classificacoes` | JSON canônico em texto com códigos e rótulos; preserva todas as dimensões |
| `periodo`, `data_periodo`, `ano`, `trimestre` | Código original e início do período; trimestre nulo para séries anuais |
| `valor`, `valor_original`, `status_valor` | Valor numérico, representação original normalizada e interpretação |
| `run_id` | Última carga que publicou a observação |

Conversões conforme as [convenções oficiais do IBGE](https://ftp.ibge.gov.br/Indicadores_Sociais/Sintese_de_Indicadores_Sociais/Indicadores_Sociais_2018_tabulacoes_especiais/documentacao/Convencoes_Utilizadas_nas_Tabelas.pdf):

| Entrada | Valor Silver | Status |
|---|---|---|
| Número, inclusive `0` | Número | `observado` |
| `-` | 0 | `zero_absoluto` |
| `...` | NULL | `nao_disponivel` |
| `..` | NULL | `nao_aplicavel` |
| `X` | NULL | `suprimido` |
| Vazio/None | NULL | `ausente` |

Decimais com ponto ou vírgula são aceitos; valores inválidos e não finitos falham.
Períodos anuais têm quatro dígitos; trimestrais usam `AAAA01` a `AAAA04`.
Datas anuais são âncoras de 1º de janeiro, não observações diárias.
Observações idênticas repetidas são consolidadas; conflitos para a mesma chave falham.

A carga usa `ON CONFLICT DO UPDATE`, lotes de 500 dentro de uma única transação
e confere todas as colunas por releitura. Erro em qualquer lote ou divergência
na leitura reverte a transação. Não há `replace`, `DROP`, criação automática de
tabela ou exclusão de observações ausentes em uma coleta posterior.

Antes de carregar, são verificados nomes/tipos/nulabilidade das colunas e a chave
primária. A Silver representa o estado atualizado, não um histórico de revisões;
os snapshots Bronze preservam as versões coletadas. Execuções concorrentes com
observações sobrepostas seguem a última escrita: operar sequencialmente neste estágio.

## Instalação e dependências

Python 3.14 foi preservado e utilizado nos testes.

```bash
uv sync --frozen                      # runtime base + ferramentas de testes
uv sync --frozen --extra orchestration
uv sync --frozen --all-extras          # inclui também Spark
```

O runtime base acrescenta pandas, SQLAlchemy e psycopg2-binary. Prefect e PySpark
são extras para manter o fluxo anterior independente dessas ferramentas.
Pandas foi limitado à série 2.3: o teste inicial com pandas 3 passou, mas o
próprio PySpark alertou sobre suporte parcial. A configuração Spark desativa
Arrow, evitando uma dependência adicional para este volume pequeno.

Versões verificadas: pandas 2.3.3, SQLAlchemy 2.1.9, psycopg2-binary 2.9.13,
Prefect 3.9.3, PySpark 4.3.0, Java 21 e PostgreSQL local 16.2.
O arquivo `uv.lock` fixa a resolução completa. `requirements.txt` é o export
do runtime base, sem os extras e sem ferramentas de testes:

```bash
uv export --frozen --no-dev --no-emit-project --no-hashes -o requirements.txt
```

Para Spark local é necessário Java compatível e `JAVA_HOME` configurado.
O Java baixado durante a validação ficou somente em `.venv/tools`; isso não é
uma dependência versionada nem uma instalação de sistema.

## Configuração e execução autorizada

Preencher `.env` local, que continua ignorado pelo Git, ou exportar:

```dotenv
MONGODB_URI=<URI própria já utilizada pela equipe>
MONGODB_DATABASE=<banco aprovado>
MONGODB_BRONZE_COLLECTION=<coleção nova e aprovada>
DATABASE_URL=<URL PostgreSQL própria com sslmode=require ou verificação mais forte>
SILVER_SCHEMA=<schema existente aprovado>
SILVER_TABLE=<tabela aprovada com o contrato Silver>
```

As URLs não entram nos parâmetros do flow e as falhas dos adaptadores novos
de banco não propagam SQL/payloads/strings de conexão para o orquestrador.
Para PostgreSQL remoto, TLS é obrigatório; recomenda-se `verify-full` quando
o ambiente suportar a verificação completa do certificado.

O DDL pode ser gerado sem conexão, inclusive sem credenciais:

```bash
uv run --frozen python run_project.py --print-ddl --schema public --table pnad_silver
```

`public.pnad_silver` é somente um exemplo local de DDL, não uma escolha de
recurso remoto. A criação da tabela e o acesso de escrita à coleção Bronze
dependem de aprovação específica da equipe. O processo de carga precisa de
SELECT/INSERT/UPDATE na tabela; não precisa de DROP/CREATE/ALTER.

Depois de aprovar/preparar os destinos:

```bash
uv run --frozen python run_project.py --allow-external-writes
uv run --frozen --extra orchestration python orchestrate_prefect.py --allow-external-writes
uv run --frozen --all-extras python orchestrate_prefect.py --backend spark --allow-external-writes
```

O parâmetro `--run-id` permite identificar/repetir uma carga, desde que o conteúdo
do snapshot não tenha mudado. Sem ele, um UUID é gerado. `--max-rows` limita a
ponte Spark → pandas (padrão 100.000 observações). A API e o JSON Bronze já são
lidos no driver: esta implementação não é uma ingestão distribuída de big data.

Uma execução manual Prefect pode iniciar seu servidor efêmero local. Para
acompanhar no painel, iniciar um servidor local separado e configurar, no ambiente,
`PREFECT_API_URL=http://127.0.0.1:4200/api`. Nenhum servidor persistente, deployment,
agendamento, conta Prefect Cloud ou notificação externa foi ativado para o projeto.
A validação remota utilizou servidor Prefect temporário local.
O agendamento é conteúdo extra e pode ser configurado posteriormente com
`.serve()` e `Cron(..., timezone="America/Recife")`, após decidir frequência.

## Testes e validação

```bash
uv run --frozen --all-extras pytest -q
```

Os testes Spark precisam de Java. Os testes de PostgreSQL são opt-in, usam
`TEST_POSTGRES_URL` e recusam hosts remotos ou bancos cujo nome não comece com
`test_`. Criam schemas aleatórios somente nesse banco de teste e os removem ao
terminar. Os testes Prefect iniciam servidor local temporário, com operações
externas substituídas por fixtures. Os testes MongoDB usam mongomock, sem Atlas.
Sem dependências extras, os testes correspondentes são ignorados explicitamente.

Validações executadas:

Resultado da suíte completa com extras, Java e banco descartável configurados:
**48 testes aprovados, sem testes ignorados**.

- Regressão dos dois modos anteriores e fechamento do cliente.
- Todas as variáveis, localidades e categorias; tipos anuais/trimestrais;
  ausências, supressão, zero absoluto, valores inválidos e duplicidades.
- Idempotência Bronze, colisão de identificador, hashes, isolamento entre cargas
  e bloqueio de cargas incompletas.
- PostgreSQL local real: upsert, atualização sem duplicação, releitura,
  rollback provocado por trigger de teste e recusa de schema incompatível.
- Pipeline Bronze simulado → pandas/Spark reais → PostgreSQL local real,
  executado duas vezes, mantendo 28 observações Silver em cada cenário.
- Flow/tarefas Prefect reais: sucesso, retry após falha transitória de escrita sem
  duplicação, bloqueio de carga parcial e ausência de autorização.
- Erros dos novos adaptadores sem credenciais no traceback formatado.
- Spark DataFrame e Spark SQL, equivalência com pandas e limite da coleta local.
- Ruff nos arquivos novos/alterados de implementação e `git diff --check`.

As sete consultas existentes foram executadas contra a API pública em 18/11/2026,
sem escrita em bancos. Todos os metadados continham as variáveis configuradas e
o nível N6; as respostas continham Recife e os períodos solicitados:

| Tabela | Observações normalizadas |
|---|---:|
| 9468 | 64 |
| 7192 | 600 |
| 6732 | 768 |
| 6736 | 960 |
| 6820 | 256 |
| 6678 | 224 |
| 6578 | 16 |
| **Total** | **2.888** |

Os mesmos retornos públicos foram processados por pandas e Spark e comparados
coluna a coluna: as 2.888 observações foram equivalentes, com 1.698 zeros absolutos
(`-`) e 1.190 valores numéricos observados. Essa primeira validação foi local;
a execução posterior autorizada em Atlas/Neon está registrada no
[relatório de integração](validacao-integracao-atlas-neon.md).
Essa validação não equivale a validar representatividade estatística
ou adequação de cada indicador para os modelos futuros do projeto.

Para repetir essa checagem pública, sem acessar bancos:

```bash
uv run --frozen python -m scripts.validate_ibge
```

## Limitações e pendências

- A conexão real com Atlas/Neon e as escritas autorizadas foram validadas; ver
  [relatório de integração](validacao-integracao-atlas-neon.md). O DDL foi aplicado
  pelo usuário. A validação não criou/alterou schemas ou índices nem acessou
  coleções/tabelas legadas.
- Mongomock continua sendo usado na suíte isolada; a integração real foi
  conferida separadamente, sem testes de indisponibilidade ou carga concorrente.
- Não foi executado cluster Spark; testes usam modo local e coleta limitada.
- A execução em notebook Google Colab ainda está pendente; a integração remota
  foi executada a partir do ambiente local do projeto.
- O catálogo original foi preservado, inclusive variáveis auxiliares. Selecionar
  somente indicadores percentuais para a futura base analítica CRISP-DM é outra
  decisão; não se somam percentuais/categorias heterogêneas nesta entrega.
- O modo legado anuncia JSON no menu, mas já gravava MongoDB antes desta evolução.
  Essa divergência foi registrada e não teve o destino alterado silenciosamente.
- O script legado `read_mongo.py` continua executando consultas ao importar;
  não é utilizado pelo novo pipeline. O método legado `get_collection()` continua
  criando índice; o novo caminho usa acesso direto e não executa esse método.
- H3, PostGIS e ingestão OVT/EDL permanecem no planejamento, fora destas aulas.

## Reversão

A nova ETL é opt-in: `main.py` não importa Prefect ou Spark. Pode-se retornar a
operação ao fluxo anterior sem remover dados. A transformação pandas permanece
disponível como alternativa ao Spark, preservando o mesmo contrato Silver.

As mudanças estão separadas por arquivos e mapeadas por aula acima. Não houve
push, PR ou merge. Retirar o código novo não exige apagar coleções/tabelas;
qualquer reversão de dados ou de recursos externos requer planejamento e
autorização próprios. Não se fornece comando destrutivo automático de rollback.

## Referências técnicas

- [Instalação PySpark](https://spark.apache.org/docs/latest/api/python/getting_started/install.html)
- [Retries no Prefect](https://docs.prefect.io/v3/how-to-guides/workflows/retries)
- [Upsert PostgreSQL no SQLAlchemy](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert)
- [API de agregados IBGE](https://servicodados.ibge.gov.br/api/docs/agregados)

Os PDFs das aulas definiram os objetivos; o repositório local do professor,
no commit `b57a1a0`, foi usado apenas como referência até Neon. As decisões de
granularidade, estrutura, integração e preservação acima são deste projeto.
