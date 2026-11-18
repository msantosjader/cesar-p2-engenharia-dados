"""Snapshots de uma execução, em coleção explícita e separada do legado."""

import json
from datetime import UTC, datetime
from hashlib import sha256

from bson import BSON


def fingerprint(payload):
    return sha256(
        json.dumps(
            payload, sort_keys=True, ensure_ascii=False, allow_nan=False
        ).encode()
    ).hexdigest()


def snapshot(run_id, tabela, url, payload):
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"Tabela {tabela}: resposta vazia ou inválida")
    doc = {
        "_id": f"{run_id}:{tabela}",
        "run_id": run_id,
        "tabela": str(tabela),
        "source_url": url,
        "payload": payload,
        "payload_hash": fingerprint(payload),
        "captured_at": datetime.now(UTC),
        "format_version": 1,
    }
    if len(BSON.encode(doc)) >= 16 * 1024 * 1024:
        raise ValueError("Snapshot excede o limite BSON; particione antes de carregar")
    return doc


class BronzeStore:
    def __init__(self, collection):
        self.collection = collection

    def write(self, document):
        # _id já é único: nenhum índice ou documento legado precisa ser alterado.
        self.collection.update_one(
            {"_id": document["_id"]}, {"$setOnInsert": document}, upsert=True
        )
        saved = self.collection.find_one({"_id": document["_id"]})
        if (saved["payload_hash"], saved["source_url"]) != (
            document["payload_hash"],
            document["source_url"],
        ):
            raise ValueError("run_id já utilizado com outra consulta ou conteúdo")

    def read(self, run_id, expected_tables):
        docs = list(self.collection.find({"run_id": run_id}))
        expected = {str(t) for t in expected_tables}
        if len(docs) != len(expected) or {d["tabela"] for d in docs} != expected:
            raise ValueError("Carga Bronze incompleta ou com tabelas inesperadas")
        for doc in docs:
            if (
                doc.get("format_version") != 1
                or fingerprint(doc["payload"]) != doc["payload_hash"]
            ):
                raise ValueError("Snapshot Bronze inválido ou corrompido")
        return sorted(docs, key=lambda d: d["tabela"])
