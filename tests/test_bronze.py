from copy import deepcopy

import mongomock
import pytest

from src.bronze import BronzeStore, snapshot


def test_retry_is_idempotent_and_legacy_untouched(documents):
    collection = mongomock.MongoClient().db.bronze
    collection.insert_one({"_id": "legacy", "id": "162"})
    store = BronzeStore(collection)
    store.write(documents[0])
    store.write(documents[0])
    assert collection.count_documents({}) == 2
    assert store.read("test-run", [6736])[0]["payload"] == documents[0]["payload"]
    assert collection.find_one({"_id": "legacy"}) == {"_id": "legacy", "id": "162"}


def test_run_cannot_be_overwritten(documents):
    store = BronzeStore(mongomock.MongoClient().db.bronze)
    store.write(documents[0])
    changed = snapshot(
        "test-run", 6736, "https://other.invalid", documents[0]["payload"]
    )
    with pytest.raises(ValueError, match="já utilizado"):
        store.write(changed)


def test_partial_run_and_corruption_rejected(documents):
    store = BronzeStore(mongomock.MongoClient().db.bronze)
    store.write(documents[0])
    with pytest.raises(ValueError, match="incompleta"):
        store.read("test-run", [6736, 9468])
    store.collection.update_one(
        {"_id": documents[0]["_id"]}, {"$set": {"payload_hash": "bad"}}
    )
    with pytest.raises(ValueError, match="corrompido"):
        store.read("test-run", [6736])


def test_runs_do_not_mix(documents):
    store = BronzeStore(mongomock.MongoClient().db.bronze)
    store.write(documents[0])
    other = deepcopy(documents[0])
    other.update(_id="other:6736", run_id="other")
    store.write(other)
    assert len(store.read("test-run", [6736])) == 1
