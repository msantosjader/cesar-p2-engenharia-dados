import time

import requests


class Extract():
    def __init__(self):
        pass

    def get_pnad(self, url, max_retries=1):
        for attempt in range(max_retries + 1):
            try:
                req = requests.get(url, timeout=30)
            except Exception as e:
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                print(f"❌ Erro realizando a consulta! URL: {url}\nErro: {e}")
                raise

            if req.status_code == 429 or req.status_code >= 500:
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                print(f"❌ Erro na consulta! URL: {url}")
                raise Exception(f"Código HTTP {req.status_code}")

            if req.status_code != 200:
                print(f"❌ Erro na consulta! URL: {url}")
                raise Exception(f"Código HTTP {req.status_code}")

            data = req.json()
            print(f"ℹ️ Consulta realizada com sucesso. URL: {url}")
            return data