import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi


def get_client(uri=None):
    load_dotenv()
    if uri is None:
        uri = os.getenv("MONGODB_URI")
    if not uri:
        raise ValueError("MONGODB_URI não encontrado no .env")
    return MongoClient(uri, server_api=ServerApi("1"))


def ping(client):
    client.admin.command("ping")


def get_database(client, name="pnad"):
    return client[name]


def get_collection(db, name="pnad_projeto"):
    coll = db[name]
    coll.create_index(
        [("tabela", 1)],
        name="idx_tabela",
    )
    return coll
