import sys

from src.ibge import QueryBuilder, VARIAVEIS, SEXO, UFS


class CLI:
    def __init__(self):
        self.qb = QueryBuilder()

    def _encerrar(self):
        print("Programa encerrado.")
        sys.exit(0)

    def _perguntar(self, prompt, catalogo, usar_all=False):
        opcoes = "\n  ".join(f"{k} - {nome}" for k, nome in catalogo.items())
        validos = {str(k) for k in catalogo}
        erros = 0

        while True:
            resposta = input(f"{prompt}\n  {opcoes}\n> ").strip()

            if resposta == "":
                if usar_all:
                    return "all"
                return ",".join(str(k) for k in catalogo)

            if resposta == "0":
                self._encerrar()

            valores = [v.strip() for v in resposta.split(",")]
            invalidos = [v for v in valores if v not in validos]

            if invalidos:
                erros += 1
                if erros >= 3:
                    print("Muitas tentativas inválidas.")
                    self._encerrar()
                print(f"Valor inválido: {', '.join(invalidos)}. Válidos: {', '.join(sorted(validos))}")
                continue

            return ",".join(valores)

    def run(self):
        print("Escolha o modo de execução:")
        print("  1 - Atividade1 (4093 → JSON)")
        print("  2 - pnad-projeto (→ MongoDB)")
        print("  0 - Sair")

        while True:
            opcao = input("> ").strip()
            if opcao == "0":
                self._encerrar()
            if opcao in ("1", "2"):
                break
            print("Opção inválida.")

        if opcao == "1":
            return self._run_atividade1()
        return "pnad-projeto"

    def _run_atividade1(self):
        print("\nQueryBuilder IBGE PNAD para a Atividade 1\n")

        variaveis = self._perguntar(
            "Escolha as variáveis (ENTER = todas, 0 = sair):", VARIAVEIS
        )
        sexo = self._perguntar(
            "Escolha o sexo (ENTER = todos, 0 = sair):", SEXO, usar_all=True
        )
        ufs = self._perguntar(
            "Escolha a UF (ENTER = todas, 0 = sair):", UFS, usar_all=True
        )

        return self.qb.montar_url(variaveis, sexo, ufs)
