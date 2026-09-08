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

TABELAS_PNAD_PROJETO = {
    9468: {
        "nome": "Rede geral de distribuição de água",
        "eixo": "Saneamento",
        "periodos": "2016|2017|2018|2019|2022|2023|2024|2025",
        "variaveis": "9974|9975|12953|12954|10119|10120|12955|12956",
        "classificacao": None,
    },
    7192: {
        "nome": "Esgotamento sanitário",
        "eixo": "Saneamento",
        "periodos": "2019|2022|2023|2024|2025",
        "variaveis": "9986|9987|9988|9989|10131|10132|10133|10134",
        "classificacao": "1[all]|11558[all]",
    },
    6732: {
        "nome": "Disponibilidade da rede geral de água",
        "eixo": "Saneamento",
        "periodos": "2016|2017|2018|2019|2022|2023|2024|2025",
        "variaveis": "9974|9975|9976|9977|10119|10120|10121|10122",
        "classificacao": "1[all]|826[all]",
    },
    6736: {
        "nome": "Destino do lixo",
        "eixo": "Resíduos Sólidos",
        "periodos": "2016|2017|2018|2019|2022|2023|2024|2025",
        "variaveis": "162|5123|9784|9785|10114|10116|10117|10118",
        "classificacao": "1[all]|67[all]",
    },
    6820: {
        "nome": "Tipo de domicílio",
        "eixo": "Adensamento",
        "periodos": "2016|2017|2018|2019|2022|2023|2024|2025",
        "variaveis": "162|5123|9784|9785|10114|10116|10117|10118",
        "classificacao": "125[all]",
    },
    6678: {
        "nome": "Número de moradores por domicílio",
        "eixo": "Adensamento",
        "periodos": "2016|2017|2018|2019|2022|2023|2024|2025",
        "variaveis": "162|5123|9784|9785",
        "classificacao": "68[all]",
    },
    6578: {
        "nome": "Número médio de moradores por domicílio",
        "eixo": "Adensamento",
        "periodos": "2016|2017|2018|2019|2022|2023|2024|2025",
        "variaveis": "10163|10164",
        "classificacao": None,
    },
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

    def montar_url_projeto(self, tabela_id):
        t = TABELAS_PNAD_PROJETO[tabela_id]
        url = (f"{self.url_base}/{tabela_id}"
               f"/periodos/{t['periodos']}"
               f"/variaveis/{t['variaveis']}"
               f"?localidades=N6[2611606]")
        if t["classificacao"]:
            url += f"&classificacao={t['classificacao']}"
        return url