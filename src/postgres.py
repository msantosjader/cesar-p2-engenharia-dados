"""Carga Silver sem DDL automático, substituição de tabelas ou SQL interpolado."""

import re

import pandas as pd
from sqlalchemy import (
    Column,
    Date,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    inspect,
    select,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateTable

from src.transform import COLUMNS


def silver_table(name, schema):
    for identifier in (name, schema):
        if not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", identifier):
            raise ValueError(
                "Schema e tabela devem ser identificadores simples em minúsculas"
            )
    types = {
        "observation_id": String(64),
        "data_periodo": Date,
        "ano": Integer,
        "trimestre": Integer,
        "valor": Float,
    }
    return Table(
        name,
        MetaData(),
        *[
            Column(
                c,
                types.get(c, Text),
                primary_key=c == "observation_id",
                nullable=c in {"valor", "trimestre"},
            )
            for c in COLUMNS
        ],
        schema=schema,
    )


def ddl(name, schema):
    return (
        str(
            CreateTable(silver_table(name, schema)).compile(
                dialect=postgresql.dialect()
            )
        )
        + ";"
    )


def postgres_engine(url):
    parsed = make_url(url)
    if parsed.get_backend_name() not in {"postgresql", "postgres"}:
        raise ValueError("DATABASE_URL deve apontar para PostgreSQL")
    if parsed.host not in {"localhost", "127.0.0.1", "::1"} and parsed.query.get(
        "sslmode"
    ) not in {"require", "verify-ca", "verify-full"}:
        raise ValueError(
            "PostgreSQL remoto exige sslmode=require ou verificação mais forte"
        )
    parsed = parsed.set(drivername="postgresql+psycopg2")
    return create_engine(
        parsed,
        pool_pre_ping=True,
        hide_parameters=True,
        connect_args={"connect_timeout": 10},
    )


class PostgresStore:
    def __init__(self, engine, table, schema):
        self.engine = engine
        self.table = silver_table(table, schema)

    def validate_schema(self, connection):
        inspector = inspect(connection)
        if not inspector.has_table(self.table.name, schema=self.table.schema):
            raise ValueError(
                "Tabela Silver ausente; revise e aplique o DDL autorizado antes da carga"
            )
        columns = {
            c["name"]: c
            for c in inspector.get_columns(self.table.name, schema=self.table.schema)
        }
        if set(columns) != set(COLUMNS):
            raise ValueError("Schema Silver incompatível com o contrato esperado")
        for column in self.table.columns:
            actual = columns[column.name]
            if (
                actual["type"]._type_affinity is not column.type._type_affinity
                or actual["nullable"] != column.nullable
            ):
                raise ValueError(f"Tipo ou nulabilidade incompatível em {column.name}")
        pk = inspector.get_pk_constraint(self.table.name, schema=self.table.schema)
        if pk.get("constrained_columns") != ["observation_id"]:
            raise ValueError("Silver deve ter chave primária observation_id")

    def load(self, frame):
        if list(frame.columns) != COLUMNS or frame.empty:
            raise ValueError("DataFrame vazio ou contrato Silver inválido")
        if frame["observation_id"].duplicated().any():
            raise ValueError("DataFrame contém chaves duplicadas")
        records = frame.astype(object).where(pd.notna(frame), None).to_dict("records")
        with self.engine.begin() as connection:
            self.validate_schema(connection)
            for offset in range(0, len(records), 500):
                batch = records[offset : offset + 500]
                statement = insert(self.table).values(batch)
                statement = statement.on_conflict_do_update(
                    index_elements=["observation_id"],
                    set_={
                        c: statement.excluded[c]
                        for c in COLUMNS
                        if c != "observation_id"
                    },
                )
                connection.execute(statement)
                # Confere a persistência dentro da mesma transação, sem consultar outras cargas.
                saved = (
                    connection.execute(
                        select(self.table).where(
                            self.table.c.observation_id.in_(
                                [r["observation_id"] for r in batch]
                            )
                        )
                    )
                    .mappings()
                    .all()
                )
                by_id = {r["observation_id"]: dict(r) for r in saved}
                if any(by_id.get(r["observation_id"]) != r for r in batch):
                    raise ValueError(
                        "Verificação de leitura Silver falhou; transação revertida"
                    )
        return len(records)
