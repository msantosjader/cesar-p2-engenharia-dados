from unittest.mock import Mock

import mongomock
import pytest

pytest.importorskip("prefect")
from prefect.testing.utilities import prefect_test_harness

import orchestrate_prefect as orchestration
from src.bronze import BronzeStore
from src.pipeline import PipelineConfig


@pytest.fixture(scope="module", autouse=True)
def prefect_server():
    with prefect_test_harness():
        yield


def test_real_flow_tasks_use_same_run_and_preserve_transform(documents, monkeypatch):
    config = PipelineConfig("test", "bronze", "public", "silver")
    store = BronzeStore(mongomock.MongoClient().db.bronze)
    monkeypatch.setattr(orchestration, "preflight", lambda *args: None)
    monkeypatch.setattr(
        orchestration, "extract_project", lambda *args, **kwargs: documents
    )
    attempts = []

    def write_with_transient_failure(config, docs):
        attempts.append(True)
        for document in docs:
            store.write(document)
        if len(attempts) == 1:
            raise RuntimeError("Falha transitória simulada após escrita Bronze")

    monkeypatch.setattr(orchestration, "write_bronze", write_with_transient_failure)
    monkeypatch.setattr(
        orchestration, "read_bronze", lambda config, run_id: store.read(run_id, [6736])
    )
    saved = []
    monkeypatch.setattr(
        orchestration,
        "load_silver",
        lambda config, frame: saved.append(frame) or len(frame),
    )
    result = orchestration.pipeline_pnad(
        config, run_id="test-run", allow_external_writes=True
    )
    assert result == {"run_id": "test-run", "rows": 4, "backend": "pandas"}
    assert saved[0].observation_id.nunique() == 4
    assert store.collection.count_documents({}) == 1
    assert len(attempts) == 2


def test_partial_bronze_fails_flow_without_silver(documents, monkeypatch):
    config = PipelineConfig("test", "bronze", "public", "silver")
    monkeypatch.setattr(orchestration, "preflight", lambda *args: None)
    monkeypatch.setattr(
        orchestration, "extract_project", lambda *args, **kwargs: documents
    )
    monkeypatch.setattr(orchestration, "write_bronze", lambda *args: None)

    def incomplete(*args):
        raise ValueError("Carga incompleta")

    monkeypatch.setattr(orchestration, "read_bronze", incomplete)
    load = Mock()
    monkeypatch.setattr(orchestration, "load_silver", load)
    with pytest.raises(ValueError, match="incompleta"):
        orchestration.pipeline_pnad(config, allow_external_writes=True)
    load.assert_not_called()


def test_no_external_authorization_stops_before_services(monkeypatch):
    preflight = Mock()
    monkeypatch.setattr(orchestration, "preflight", preflight)
    with pytest.raises(ValueError, match="Autorize"):
        orchestration.pipeline_pnad(
            PipelineConfig("test", "bronze", "public", "silver")
        )
    preflight.assert_not_called()
