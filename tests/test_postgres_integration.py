"""Testes opt-in: exclusivamente banco local descartável chamado test_* ."""

import os
from copy import deepcopy
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text

from src.postgres import PostgresStore, postgres_engine
from src.transform import Transform

pytestmark = pytest.mark.postgres


@pytest.fixture
def store():
    url = os.getenv("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL não configurada")
    engine = postgres_engine(url)
    if engine.url.host not in {
        "localhost",
        "127.0.0.1",
        "::1",
    } or not engine.url.database.startswith("test_"):
        engine.dispose()
        pytest.fail("Use somente PostgreSQL local descartável em banco test_*")
    schema = "test_" + uuid4().hex
    store = PostgresStore(engine, "silver", schema)
    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        store.table.create(conn)
    try:
        yield store
    finally:
        with engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        engine.dispose()


def test_real_upsert_readback_and_update(store, documents):
    frame = Transform().transform(documents)
    assert store.load(frame) == 4
    assert store.load(frame) == 4
    frame.loc[0, "valor"] = 77.0
    frame.loc[0, "valor_original"] = "77"
    store.load(frame)
    with store.engine.connect() as conn:
        assert conn.scalar(select(func.count()).select_from(store.table)) == 4
        assert (
            conn.scalar(
                select(store.table.c.valor).where(
                    store.table.c.observation_id == frame.loc[0, "observation_id"]
                )
            )
            == 77.0
        )


def test_real_readback_failure_rolls_back(store, documents, monkeypatch):
    frame = Transform().transform(documents)
    store.load(frame)
    # Trigger local de teste altera o valor após a escrita, provocando erro na conferência.
    schema = store.table.schema
    with store.engine.begin() as conn:
        conn.execute(
            text(f'''CREATE FUNCTION "{schema}".change_value() RETURNS trigger AS $$
            BEGIN NEW.valor := 999; RETURN NEW; END; $$ LANGUAGE plpgsql''')
        )
        conn.execute(
            text(f'''CREATE TRIGGER change_value BEFORE UPDATE ON "{schema}".silver
            FOR EACH ROW EXECUTE FUNCTION "{schema}".change_value()''')
        )
    frame.loc[0, "valor"] = 88.0
    with pytest.raises(ValueError, match="revertida"):
        store.load(frame)
    with store.engine.connect() as conn:
        assert (
            conn.scalar(
                select(store.table.c.valor).where(
                    store.table.c.observation_id == frame.loc[0, "observation_id"]
                )
            )
            == 12.5
        )


def test_real_incompatible_schema_rejected_before_insert(store, documents):
    with store.engine.begin() as conn:
        conn.execute(
            text(
                f'ALTER TABLE "{store.table.schema}".silver ALTER COLUMN ano TYPE TEXT'
            )
        )
    with pytest.raises(ValueError, match="incompatível"):
        store.load(Transform().transform(documents))
    with store.engine.connect() as conn:
        assert conn.scalar(select(func.count()).select_from(store.table)) == 0


@pytest.mark.parametrize("backend", ["pandas", "spark"])
def test_pipeline_bronze_transform_postgres_twice(
    store, documents, monkeypatch, backend
):
    if backend == "spark":
        import shutil

        pytest.importorskip("pyspark")
        if not shutil.which("java") and not os.getenv("JAVA_HOME"):
            pytest.skip("Java indisponível")
    import mongomock

    from src.bronze import snapshot
    from src.ibge import TABELAS_PNAD_PROJETO
    from src.pipeline import PipelineConfig, run_project

    mongo = Mock()
    database = mongomock.MongoClient().test_db
    mongo.get_database.return_value = database
    monkeypatch.setattr("src.pipeline.Mongo", lambda: mongo)
    monkeypatch.setenv("MONGODB_URI", "mongodb://127.0.0.1:1")
    monkeypatch.setenv(
        "DATABASE_URL", store.engine.url.render_as_string(hide_password=False)
    )

    def extracted(run_id):
        return [
            snapshot(
                run_id,
                table,
                "https://example.invalid",
                deepcopy(documents[0]["payload"]),
            )
            for table in TABELAS_PNAD_PROJETO
        ]

    monkeypatch.setattr("src.pipeline.extract_project", extracted)
    config = PipelineConfig("test_db", "bronze", store.table.schema, store.table.name)
    first = run_project(config, backend, "first")
    second = run_project(config, backend, "second")
    assert first["rows"] == second["rows"] == 28
    assert database.bronze.count_documents({}) == 14
    with store.engine.connect() as conn:
        assert conn.scalar(select(func.count()).select_from(store.table)) == 28
        assert set(conn.scalars(select(store.table.c.run_id))) == {"second"}
