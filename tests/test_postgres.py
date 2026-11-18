from unittest.mock import Mock, patch

import pytest
from sqlalchemy.dialects import postgresql

from src.postgres import PostgresStore, ddl, postgres_engine, silver_table
from src.transform import Transform


def test_ddl_is_explicit_and_identifiers_validated():
    text = ddl("silver", "public")
    assert "PRIMARY KEY (observation_id)" in text
    assert "DROP" not in text
    with pytest.raises(ValueError):
        silver_table("silver; DROP TABLE users", "public")


def test_remote_connection_requires_tls():
    with pytest.raises(ValueError, match="sslmode"):
        postgres_engine("postgresql://user:secret@remote.invalid/db")


def test_upsert_and_readback_use_transaction(documents):
    frame = Transform().transform(documents)
    records = frame.astype(object).where(frame.notna(), None).to_dict("records")
    engine = Mock()
    connection = engine.begin.return_value.__enter__ = Mock(return_value=Mock())
    engine.begin.return_value.__exit__ = Mock(return_value=False)
    conn = connection.return_value
    conn.execute.return_value.mappings.return_value.all.return_value = records
    store = PostgresStore(engine, "silver", "public")
    with patch.object(store, "validate_schema"):
        assert store.load(frame) == 4
    statement = conn.execute.call_args_list[0].args[0]
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT (observation_id) DO UPDATE" in sql


def test_readback_failure_rolls_back(documents):
    engine = Mock()
    engine.begin.return_value.__enter__ = Mock(return_value=Mock())
    engine.begin.return_value.__exit__ = Mock(return_value=False)
    conn = engine.begin.return_value.__enter__.return_value
    conn.execute.return_value.mappings.return_value.all.return_value = []
    store = PostgresStore(engine, "silver", "public")
    with (
        patch.object(store, "validate_schema"),
        pytest.raises(ValueError, match="revertida"),
    ):
        store.load(Transform().transform(documents))
    assert engine.begin.return_value.__exit__.call_args.args[0] is ValueError
