from src.cli import CLI
from src.extract import Extract
from src.ibge import TABELAS_PNAD_PROJETO, QueryBuilder
from src.load import Load


def run_pipeline():
    print("🚀 Iniciando Pipeline de Extração IBGE -> MongoDB Atlas")

    # 1. Interage com a CLI para selecionar variáveis/UF e gerar a URL da API
    cli = CLI()
    url = cli.run()

    if url == "pnad-projeto":
        extractor = Extract()
        loader = Load()
        try:
            for tabela in TABELAS_PNAD_PROJETO:
                dados = extractor.get_pnad(QueryBuilder().montar_url_projeto(tabela))
                if not isinstance(dados, list) or not dados:
                    raise ValueError(f"Tabela {tabela}: resposta vazia ou inválida")
                loader.save_to_mongodb("ibge_database", "pnad_extractions", dados)
        finally:
            loader.close()
        return

    # 2. Executa a requisição HTTP e extrai os dados JSON
    extractor = Extract()
    dados_extraidos = extractor.get_pnad(url)

    # 3. Salva os dados extraídos diretamente no MongoDB
    loader = Load()
    try:
        loader.save_to_mongodb(
            db_name="ibge_database",
            collection_name="pnad_extractions",
            data=dados_extraidos,
        )
    finally:
        loader.close()


if __name__ == "__main__":
    run_pipeline()
