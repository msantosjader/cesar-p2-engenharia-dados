import requests


class Extract():
    def __init__(self):
        pass

    def get_pnadc(self):
        url = "https://servicodados.ibge.gov.br/api/v3/agregados/4093/periodos/201201-202601/variaveis/4099?localidades=N3[26]&classificacao=2[all]"
        req = requests.get(url)
        data = req.json()

        return data