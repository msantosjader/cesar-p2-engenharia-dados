"""Aula 9/10: Prefect coordena os serviços existentes, sem duplicar a ETL."""

from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.tasks import exponential_backoff

from src.pipeline import (
    PipelineConfig,
    extract_project,
    load_silver,
    preflight,
    read_bronze,
    run_identifier,
    transform_documents,
    write_bronze,
)


def retry_transient(task, task_run, state):
    try:
        state.result()
    except ValueError:
        return False
    except Exception:  # noqa: BLE001 - callback do Prefect recebe exceções de qualquer task
        return True
    return False


@task(
    retries=2,
    retry_delay_seconds=exponential_backoff(backoff_factor=2),
    retry_condition_fn=retry_transient,
    persist_result=False,
    cache_policy=NO_CACHE,
)
def extract_task(run_id):
    # O Prefect controla tentativas; não multiplica retries internos do extrator.
    result = extract_project(run_id, max_retries=0)
    get_run_logger().info("Extração run_id=%s tabelas=%d", run_id, len(result))
    return result


@task(
    retries=2,
    retry_delay_seconds=2,
    retry_condition_fn=retry_transient,
    persist_result=False,
    cache_policy=NO_CACHE,
)
def bronze_task(config, documents):
    write_bronze(config, documents)
    get_run_logger().info("Bronze gravado tabelas=%d", len(documents))


@task(
    retries=2,
    retry_delay_seconds=2,
    retry_condition_fn=retry_transient,
    persist_result=False,
    cache_policy=NO_CACHE,
)
def read_task(config, run_id):
    return read_bronze(config, run_id)


@task(persist_result=False, cache_policy=NO_CACHE)
def transform_task(documents, backend, max_rows):
    frame = transform_documents(documents, backend, max_rows)
    get_run_logger().info("Transformação backend=%s linhas=%d", backend, len(frame))
    return frame


@task(
    retries=2,
    retry_delay_seconds=2,
    retry_condition_fn=retry_transient,
    persist_result=False,
    cache_policy=NO_CACHE,
)
def silver_task(config, frame):
    count = load_silver(config, frame)
    get_run_logger().info("Silver verificada linhas=%d", count)
    return count


@flow(name="pnad-projeto", persist_result=False)
def pipeline_pnad(
    config: PipelineConfig,
    backend="pandas",
    run_id=None,
    max_rows=100000,
    allow_external_writes=False,
):
    if not allow_external_writes:
        raise ValueError(
            "Autorize explicitamente as escritas nos destinos configurados"
        )
    if backend not in {"pandas", "spark"}:
        raise ValueError("Backend deve ser pandas ou spark")
    run_id = run_identifier(run_id)
    preflight(config, backend, max_rows)
    documents = extract_task(run_id)
    bronze_task(config, documents)
    bronze = read_task(config, run_id)
    frame = transform_task(bronze, backend, max_rows)
    count = silver_task(config, frame)
    get_run_logger().info("Pipeline concluída run_id=%s linhas=%d", run_id, count)
    return {"run_id": run_id, "rows": count, "backend": backend}


if __name__ == "__main__":
    from run_project import parser

    argument_parser = parser()
    args = argument_parser.parse_args()
    if args.print_ddl:
        argument_parser.error("Use run_project.py para imprimir o DDL")
    if not args.allow_external_writes:
        argument_parser.error("É necessário --allow-external-writes")
    print(
        pipeline_pnad(
            PipelineConfig.from_env(),
            args.backend,
            args.run_id,
            args.max_rows,
            allow_external_writes=True,
        )
    )
