import os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Carrega a URI do arquivo .env
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

uri = os.getenv("MONGODB_URI")
client = MongoClient(uri, server_api=ServerApi('1'))

# Acessa o banco e a coleção onde salvamos
db = client["ibge_database"]
collection = db["pnad_extractions"]

# Busca e exibe todos os documentos inseridos
documentos = list(collection.find())

print(f"📌 Total de documentos encontrados: {len(documentos)}\n")

for i, doc in enumerate(documentos, 1):
    print(f"--- Documento {i} ---")
    print(f"ID no Mongo: {doc.get('_id')}")
    print(f"Agregado/Tabela: {doc.get('id')}")
    print(f"Variável: {doc.get('variavel')}")
    print("-" * 30)