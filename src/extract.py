import requests


class Extract():
    def __init__(self):
        pass

    def get_pnad(self, url):
        try:
            req = requests.get(url)
        except Exception as e:
            print(f"❌ Erro realizando a consulta! URL: {url}\nErro: {e}")
            raise

        if req.status_code != 200:
            print(f"❌ Erro na consulta! URL: {url}")
            raise Exception(f"Código HTTP {req.status_code}")

        data = req.json()
        print(f"ℹ️ Consulta realizada com sucesso. URL: {url}")
        return data