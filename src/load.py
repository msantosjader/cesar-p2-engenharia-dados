import json
from datetime import datetime, timezone


class Load():
    def __init__(self):
        pass

    def load_json(self, nome_arquivo, data):
        try :
            arquivo = f"saidas/{nome_arquivo}.json"
            with open(arquivo, 'w', encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

                print(f"ℹ️ JSON gearado: {arquivo}")

        except Exception as e:
            print(f"❌ Erro ao salvar o JSON: {e}")
            raise

    def load_mongo(self, collection, data, tabela_id):
        result = collection.update_one(
            {"tabela": tabela_id},
            {"$set": {
                "tabela": tabela_id,
                "dados": data,
                "inserted_at": datetime.now(timezone.utc),
            }},
            upsert=True,
        )
        return 1 if result.upserted_id or result.modified_count else 0
