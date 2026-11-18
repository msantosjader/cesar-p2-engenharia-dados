"""Serviços compartilhados pela execução manual e pelo Prefect."""

import logging
import os
import re
from dataclasses import dataclass
from uuid import uuid4

from dotenv import load_dotenv
from pymongo.errors import PyMongoError
from sqlalchemy.exc import SQLAlchemyError

from src.bronze import BronzeStore, snapshot
from src.extract import Extract
from src.ibge import TABELAS_PNAD_PROJETO, QueryBuilder
from src.mongo import Mongo
from src.postgres import PostgresStore, postgres_engine, silver_table
from src.transform import Transform, unique_observations

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineConfig:
    mongo_database: str
    bronze_collection: str
    silver_schema: str
    silver_table: str

    def __post_init__(self):
        for name in (self.mongo_database, self.bronze_collection):
            if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_-]{0,62}", name):
                raise ValueError(
                    "Banco e coleção Bronze devem ter nomes simples explícitos"
                )
        silver_table(self.silver_table, self.silver_schema)
        if (self.mongo_database, self.bronze_collection) in {
            ("ibge_database", "pnad_extractions"),
            ("ibge", "pnadc"),
        }:
            raise ValueError(
                "Use coleção Bronze separada para preservar os documentos legados"
            )

    @classmethod
    def from_env(cls):
        load_dotenv()
        keys = [
            "MONGODB_DATABASE",
            "MONGODB_BRONZE_COLLECTION",
            "SILVER_SCHEMA",
            "SILVER_TABLE",
        ]
        missing = [k for k in keys if not os.getenv(k)]
        if missing:
            raise ValueError("Configuração ausente: " + ", ".join(missing))
        return cls(*(os.environ[k] for k in keys))


def run_identifier(value=None):
    value = value or uuid4().hex
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", value):
        raise ValueError("run_id inválido")
    return value


def extract_project(run_id, extractor=None, max_retries=1):
    extractor = extractor or Extract()
    qb = QueryBuilder()
    documents = []
    for table in TABELAS_PNAD_PROJETO:
        url = qb.montar_url_projeto(table)
        payload = extractor.get_pnad(url, max_retries=max_retries)
        document = snapshot(run_id, table, url, payload)
        validate_project_response(document, TABELAS_PNAD_PROJETO[table])
        documents.append(document)
    # Não persiste cargas vazias, inválidas ou parciais.
    unique_observations(documents)
    logger.info("Extração validada run_id=%s tabelas=%d", run_id, len(documents))
    return documents


def validate_project_response(document, specification):
    """Detecta respostas HTTP 200 que omitem variáveis, períodos ou o local pedido."""
    rows = unique_observations([document])
    if {r["variavel_id"] for r in rows} != set(specification["variaveis"].split("|")):
        raise ValueError("Resposta IBGE não contém todas as variáveis solicitadas")
    expected_periods = set(specification["periodos"].split("|"))
    series = {}
    for row in rows:
        if row["nivel"] != "N6" or row["localidade_id"] != "2611606":
            raise ValueError("Resposta IBGE fora da localidade municipal configurada")
        key = (row["variavel_id"], row["classificacoes"])
        series.setdefault(key, set()).add(row["periodo"])
    if any(periods != expected_periods for periods in series.values()):
        raise ValueError("Resposta IBGE não contém todos os períodos solicitados")


def with_bronze(config, action):
    mongo = None
    try:
        mongo = Mongo()
        # Acesso direto evita create_index do utilitário legado get_collection.
        store = BronzeStore(
            mongo.get_database(config.mongo_database)[config.bronze_collection]
        )
        return action(store)
    except ValueError:
        raise
    except PyMongoError, OSError:
        raise RuntimeError(
            "Falha na operação Bronze; confira conexão e permissões"
        ) from None
    finally:
        if mongo is not None:
            mongo.close()


def write_bronze(config, documents):
    def write(store):
        for document in documents:
            store.write(document)

    with_bronze(config, write)


def read_bronze(config, run_id):
    return with_bronze(config, lambda store: store.read(run_id, TABELAS_PNAD_PROJETO))


def load_silver(config, frame):
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL ausente")
    engine = None
    try:
        engine = postgres_engine(url)
        return PostgresStore(engine, config.silver_table, config.silver_schema).load(
            frame
        )
    except ValueError:
        raise
    except SQLAlchemyError, OSError:
        # Não propaga URLs, parâmetros SQL ou payloads para logs do orquestrador.
        raise RuntimeError(
            "Falha na carga Silver; confira conexão, contrato e permissões"
        ) from None
    finally:
        if engine is not None:
            engine.dispose()


def transform_documents(documents, backend="pandas", max_rows=100000):
    if backend == "pandas":
        return Transform().transform(documents)
    if backend == "spark":
        from src.transform_spark import transform_to_pandas

        return transform_to_pandas(documents, max_rows=max_rows)
    raise ValueError("Backend deve ser pandas ou spark")


def preflight(config, backend, max_rows):
    """Valida configuração e destino antes da primeira escrita externa."""
    if backend not in {"pandas", "spark"} or max_rows <= 0:
        raise ValueError("Backend ou max_rows inválido")
    load_dotenv()
    if not os.getenv("MONGODB_URI"):
        raise ValueError("MONGODB_URI ausente")
    if not os.getenv("DATABASE_URL"):
        raise ValueError("DATABASE_URL ausente")
    if backend == "spark":
        from src.transform_spark import create_session

        session = create_session()
        session.stop()
    engine = None
    try:
        engine = postgres_engine(os.environ["DATABASE_URL"])
        with engine.connect() as connection:
            PostgresStore(
                engine, config.silver_table, config.silver_schema
            ).validate_schema(connection)
    except SQLAlchemyError, OSError:
        raise RuntimeError("Não foi possível validar o destino Silver") from None
    finally:
        if engine is not None:
            engine.dispose()


def run_project(config, backend="pandas", run_id=None, max_rows=100000):
    run_id = run_identifier(run_id)
    if backend not in {"pandas", "spark"}:
        raise ValueError("Backend deve ser pandas ou spark")
    preflight(config, backend, max_rows)
    documents = extract_project(run_id)
    write_bronze(config, documents)
    frame = transform_documents(read_bronze(config, run_id), backend, max_rows)
    count = load_silver(config, frame)
    logger.info("Pipeline concluída run_id=%s linhas=%d", run_id, count)
    return {"run_id": run_id, "rows": count, "backend": backend}
