import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi


class Mongo:
    def __init__(self, uri=None):
        load_dotenv()
        if uri is None:
            uri = os.getenv("MONGODB_URI")
        if not uri:
            raise ValueError("MONGODB_URI não encontrado no .env")
        self.client = MongoClient(uri, server_api=ServerApi("1"))

    def ping(self):
        self.client.admin.command("ping")

    def get_database(self, name="pnad"):
        return self.client[name]

    def get_collection(self, db, name="pnad_projeto"):
        coll = db[name]
        coll.create_index([("tabela", 1)], name="idx_tabela")
        return coll

    def close(self):
        self.client.close()
