from src.cli import CLI
from src.extract import Extract
from src.ibge import TABELAS_PNAD_PROJETO, QueryBuilder
from src.load import Load

def run_pipeline():
    print("🚀 Iniciando Pipeline de Extração IBGE -> MongoDB Atlas")
    
    # 1. Interage com a CLI para selecionar variáveis/UF e gerar a URL da API
    cli = CLI()
    url = cli.run()

    # 2. Executa a requisição HTTP e extrai os dados JSON
    extractor = Extract()
    dados_extraidos = extractor.get_pnad(url)

    # 3. Salva os dados extraídos diretamente no MongoDB
    loader = Load()
    loader.save_to_mongodb(
        db_name="ibge_database",           # Nome do banco no MongoDB Atlas
        collection_name="pnad_extractions", # Nome da coleção onde o JSON será guardado
        data=dados_extraidos
    )

if __name__ == "__main__":
    run_pipeline()