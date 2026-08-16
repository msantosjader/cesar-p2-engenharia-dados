# main

from datetime import datetime

from src.cli import CLI
from src.extract import Extract
from src.load import Load


if __name__ == "__main__":   
    url = CLI().run()
    
    extractor = Extract()
    data = extractor.get_pnad(url)
    
    nome_arquivo = f"pnad_{datetime.now():%Y%m%d_%H%M%S}"
    
    load = Load()
    load.load_json(nome_arquivo, data)

    print("✅ Execução finalizada.")




