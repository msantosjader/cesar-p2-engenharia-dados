# Validação real — Atlas, Neon e Prefect/PySpark

Data: 18/11/2026 (America/Recife). Início: 2026-11-18T15:13:44.865539-03:00.
Branch: `feature/foundation`.

## Autorização e limites

O usuário confirmou a criação do projeto Neon, a configuração local do `.env`
e a aplicação do DDL. Autorizou explicitamente a validação com escrita somente em:

- MongoDB Atlas: `ibge_database.pnad_bronze_runs`.
- Neon/PostgreSQL: `public.pnad_silver`.

Nenhuma URI, senha, hostname de conexão ou conteúdo do `.env` está neste relatório.
O `.env` permanece ignorado pelo Git. Não houve criação ou alteração de schema,
DDL, índices, permissões, deployments ou recursos de nuvem pelo agente.
Coleções e tabelas legadas não foram usadas pela validação.

## Verificações antes da escrita

- Destinos do `.env` conferidos contra a autorização, sem imprimir credenciais.
- Conexões reais ao Neon e ao Atlas aprovadas.
- TLS obrigatório configurado para o PostgreSQL remoto.
- Tabela Silver existente: nomes, afinidades de tipos, nulabilidade e chave
  primária compatíveis com o contrato do projeto.
- Contagens iniciais: 0 documentos Bronze,
  0 linhas Silver.

## Execuções e resultados

| Execução | Identificador | Bronze total | Silver total | Chaves Silver distintas |
|---|---|---:|---:|---:|
| Pipeline manual pandas | `validation-eba439857533-pandas` | 7 | 2888 | 2888 |
| Flow Prefect / Spark | `validation-eba439857533-spark` | 14 | 2888 | 2888 |
| Reexecução Prefect / Spark, mesmo run_id | `validation-eba439857533-spark` | 14 | 2888 | 2888 |

Cada carga percorreu API IBGE → snapshots Bronze no Atlas → `read_bronze` da
mesma execução → transformação → upsert na mesma tabela Silver do Neon.
Pandas e Spark utilizaram o mesmo contrato de dados e os métodos existentes.

Depois de cada execução, os sete documentos Bronze foram relidos e seus hashes
validados. Todas as 2888 observações foram comparadas,
coluna a coluna, com a releitura da Silver. Os resultados das versões pandas e
Spark foram comparados desconsiderando apenas `run_id`; foram equivalentes.

A segunda execução manteve 2888 observações na mesma
tabela. Repetir o mesmo run_id de Spark também manteve as contagens de Bronze e
Silver: a reexecução não criou snapshots nem linhas duplicados.
Os dados de validação permanecem nos destinos autorizados; não houve limpeza destrutiva.

| Tabela PNAD | Observações |
|---|---:|
| 6578 | 16 |
| 6678 | 224 |
| 6732 | 768 |
| 6736 | 960 |
| 6820 | 256 |
| 7192 | 600 |
| 9468 | 64 |
| **Total** | **2888** |

## Evidência da orquestração

Flow Prefect confirmado pela API do servidor temporário local:

- Flow ID: `cc5dc5f0-191b-4626-ac9e-ca47ac0c173c`.
- Estado: **Completed**.
- As cinco tarefas foram consultadas na API e estavam em **Completed**:

| Tarefa | Estado |
|---|---|
| `bronze_task-2d2` | Completed |
| `extract_task-fbd` | Completed |
| `read_task-4d8` | Completed |
| `silver_task-afb` | Completed |
| `transform_task-5cb` | Completed |

Na primeira validação, a configuração temporária do processo deixou
`PREFECT_API_URL` com string vazia. O flow e a carga concluíram, mas o emissor
local de eventos falhou. A causa foi identificada no cliente Prefect instalado:
a string vazia selecionava o cliente de servidor configurado sem URL utilizável.

A variável temporária foi removida, sem alterar o `.env` ou código do projeto.
O flow foi reexecutado com o mesmo run_id e servidor efêmero local, com os eventos
e os cinco registros de tarefas confirmados pela API. Não foi necessário modificar
as dependências ou a implementação. Não configurar `PREFECT_API_URL=""`: omitir
essa variável para servidor efêmero, ou informar uma URL local completa.

Os servidores Prefect temporários são encerrados ao sair dos processos de validação.
Nenhum servidor persistente ou agendamento foi configurado.

## Evidência e limitações

A validação executou os métodos reais `run_project` e `pipeline_pnad`, com as
credenciais locais configuradas pelo usuário. Não houve mocks de Atlas, Neon,
IBGE, Prefect ou Spark nesta etapa. Scripts temporários externos ao repositório
coordenaram consultas de schema, contagens e comparações; não alteraram a ETL.

A suíte isolada de 48 testes aprovada anteriormente continua documentada em
`docs/evolucao-aulas-08-10.md`; não foi reexecutada nesta etapa, pois somente a
documentação mudou. Os testes remotos acima são evidência adicional e distinta.

- Execução feita no computador do projeto, com Spark local; não em Google Colab.
- O notebook Colab e sua execução continuam pendentes para a entrega acadêmica.
- A transformação é Spark; a ponte final limitada para pandas reutiliza a carga
  PostgreSQL existente. Não é um teste de escrita distribuída em larga escala.
- Não foram testados failover, indisponibilidade dos serviços ou concorrência remota.
- Não houve push, PR ou commit nesta etapa.
