# ibge.py

URL_BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"

PERIODO = "201201-202601"

VARIAVEIS = {
    4096: "Taxa de participação na força de trabalho, na semana de referência, das pessoas de 14 anos ou mais de idade",
    4099: "Taxa de desocupação, na semana de referência, das pessoas de 14 anos ou mais de idade",
    12466: "Taxa de informalidade das pessoas de 14 anos ou mais de idade ocupadas na semana de referência"
}
SEXO = {
    4: "Homens",
    5: "Mulheres",
    6794: "Total"
}
UFS = {
    11 : "Rondônia", 12 : "Acre", 13 : "Amazonas", 14 : "Roraima",
    15 : "Pará", 16 : "Amapá", 17 : "Tocantins", 21 : "Maranhão",
    22 : "Piauí", 23 : "Ceará", 24 : "Rio Grande do Norte", 25 : "Paraíba",
    26 : "Pernambuco", 27 : "Alagoas", 28 : "Sergipe", 29 : "Bahia",
    31 : "Minas Gerais", 32 : "Espírito Santo", 33 : "Rio de Janeiro", 35 : "São Paulo",
    41 : "Paraná", 42 : "Santa Catarina", 43 : "Rio Grande do Sul", 50 : "Mato Grosso do Sul",
    51 : "Mato Grosso", 52 : "Goiás", 53 : "Distrito Federal"
}

class QueryBuilder:
    def __init__(self):
        self.url_base = URL_BASE
        self.periodo = PERIODO
        self.tabela = 4093
        self.variaveis = VARIAVEIS
        self.sexo = SEXO
        self.ufs = UFS

    def montar_url(self, variaveis, sexo, ufs):
        url_completa = (f"{self.url_base}/{self.tabela}/periodos/{self.periodo}"
                        f"/variaveis/{variaveis}?localidades=N3[{ufs}]"
                        f"&classificacao=2[{sexo}]")
        return url_completa