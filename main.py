# main

from datetime import datetime

from src.cli import CLI
from src.extract import Extract
from src.ibge import TABELAS_PNAD_PROJETO, QueryBuilder
from src.load import Load
from src.mongo import get_client, get_collection, get_database, ping


if __name__ == "__main__":
    modo = CLI().run()

    if modo == "pnad-projeto":
        client = get_client()
        try:
            ping(client)
            print("✅ Conectado ao MongoDB")
        except Exception as e:
            print(f"❌ Erro ao conectar no MongoDB: {e}")
            raise SystemExit(1)

        db = get_database(client)
        collection = get_collection(db)
        extractor = Extract()
        load = Load()
        qb = QueryBuilder()

        total = 0
        tabelas = list(TABELAS_PNAD_PROJETO.keys())
        for i, tabela_id in enumerate(tabelas, 1):
            info = TABELAS_PNAD_PROJETO[tabela_id]
            print(f"📋 [{i}/{len(tabelas)}] {tabela_id} - {info['nome']}...", end=" ")
            url = qb.montar_url_projeto(tabela_id)
            data = extractor.get_pnad(url)
            n = load.load_mongo(collection, data, tabela_id)
            total += n
            print(f"{n} docs upserted")

        print(f"\n✅ Execução finalizada. Total: {total} docs upserted")
        client.close()
    else:
        extractor = Extract()
        data = extractor.get_pnad(modo)

        nome_arquivo = f"pnad_{datetime.now():%Y%m%d_%H%M%S}"

        load = Load()
        load.load_json(nome_arquivo, data)

        print("✅ Execução finalizada.")


