import os
from dotenv import load_dotenv
from pathlib import Path
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Carrega as variáveis declaradas no arquivo .env
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Load:
    def __init__(self):
        # 1. Obtém a URI configurada no arquivo .env
        self.uri = os.getenv("MONGODB_URI")
        if not self.uri:
            raise ValueError("❌ MONGODB_URI não foi encontrada no arquivo .env!")

        # 2. Inicializa o cliente do MongoDB de forma segura
        self.client = MongoClient(self.uri, server_api=ServerApi('1'))

    def save_to_mongodb(self, db_name: str, collection_name: str, data):
        """
        Recebe o JSON extraído e envia para o MongoDB Atlas.
        """
        try:
            # Seleciona o banco de dados e a coleção (criados automaticamente se não existirem)
            db = self.client[db_name]
            collection = db[collection_name]

            # Caso o retorno da API seja uma lista de documentos JSON
            if isinstance(data, list):
                result = collection.insert_many(data)
                print(f"✅ Sucesso: {len(result.inserted_ids)} documento(s) inserido(s) na coleção '{collection_name}'!")
            
            # Caso o retorno seja um único dicionário JSON
            elif isinstance(data, dict):
                result = collection.insert_one(data)
                print(f"✅ Sucesso: Documento inserido com ID {result.inserted_id} na coleção '{collection_name}'!")

        except Exception as e:
            print(f"❌ Erro ao salvar dados no MongoDB: {e}")
            raise
