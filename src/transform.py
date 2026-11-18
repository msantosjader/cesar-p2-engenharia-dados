"""Contrato Silver longo: uma observação por variável/local/período/categorias."""

import json
import math
import re
from datetime import date
from hashlib import sha256

import pandas as pd

MISSING_STATUS = {
    "": "ausente",
    "..": "nao_aplicavel",
    "...": "nao_disponivel",
    "X": "suprimido",
}
MISSING = set(MISSING_STATUS)
COLUMNS = [
    "observation_id",
    "tabela",
    "variavel_id",
    "variavel",
    "unidade",
    "nivel",
    "localidade_id",
    "localidade",
    "classificacoes",
    "periodo",
    "data_periodo",
    "ano",
    "trimestre",
    "valor",
    "valor_original",
    "status_valor",
    "run_id",
]


def period_parts(period):
    if re.fullmatch(r"\d{4}", period):
        year = int(period)
        return date(year, 1, 1), year, None
    if re.fullmatch(r"\d{4}0[1-4]", period):
        year, quarter = int(period[:4]), int(period[-2:])
        return date(year, (quarter - 1) * 3 + 1, 1), year, quarter
    raise ValueError(f"Período anual/trimestral inválido: {period}")


def number_value(raw):
    # Convenções IBGE: '-' é zero absoluto; não é ausência ou supressão.
    if raw == "-":
        return 0.0, "zero_absoluto"
    if raw in MISSING:
        return None, MISSING_STATUS[raw]
    if not re.fullmatch(r"[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)", raw):
        raise ValueError("Valor numérico inválido no retorno IBGE")
    value = float(raw.replace(",", "."))
    if not math.isfinite(value):
        raise ValueError("Valor numérico não finito")
    return value, "observado"


def iter_observations(documents):
    """Percorre todas as séries. Não presume sexo, UF ou trimestre na fonte anual."""
    for document in documents:
        table, run_id = str(document["tabela"]), str(document["run_id"])
        payload = document["payload"]
        if not isinstance(payload, list) or not payload:
            raise ValueError(f"Tabela {table}: payload vazio ou inválido")
        count = 0
        try:
            for variable in payload:
                for result in variable["resultados"]:
                    categories = result["classificacoes"]
                    # Códigos, e não rótulos, definem a identidade da observação.
                    identity_categories = sorted(
                        [
                            (str(c["id"]), sorted(str(k) for k in c["categoria"]))
                            for c in categories
                        ]
                    )
                    if any(len(c["categoria"]) != 1 for c in categories):
                        raise ValueError(
                            "Resultado deve identificar uma categoria por classificação"
                        )
                    categories_json = json.dumps(
                        sorted(categories, key=lambda c: str(c["id"])),
                        sort_keys=True,
                        ensure_ascii=False,
                    )
                    for series in result["series"]:
                        location = series["localidade"]
                        level = str(location["nivel"]["id"])
                        for period, raw_value in series["serie"].items():
                            period = str(period)
                            raw = "" if raw_value is None else str(raw_value).strip()
                            # Validação antes da criação de qualquer DataFrame.
                            period_parts(period)
                            number_value(raw)
                            identity = [
                                table,
                                str(variable["id"]),
                                level,
                                str(location["id"]),
                                period,
                                identity_categories,
                            ]
                            count += 1
                            yield {
                                "observation_id": sha256(
                                    json.dumps(identity, ensure_ascii=False).encode()
                                ).hexdigest(),
                                "tabela": table,
                                "variavel_id": str(variable["id"]),
                                "variavel": variable["variavel"],
                                "unidade": variable["unidade"],
                                "nivel": level,
                                "localidade_id": str(location["id"]),
                                "localidade": location["nome"],
                                "classificacoes": categories_json,
                                "periodo": period,
                                "valor_original": raw,
                                "run_id": run_id,
                            }
        except (KeyError, TypeError, AttributeError) as exc:
            raise ValueError(f"Tabela {table}: estrutura IBGE inválida") from exc
        if not count:
            raise ValueError(f"Tabela {table}: nenhuma observação retornada")


def unique_observations(documents):
    observations = {}
    for row in iter_observations(documents):
        key = row["observation_id"]
        if key in observations and observations[key] != row:
            raise ValueError("Observações conflitantes para a mesma chave")
        observations[key] = row
    if not observations:
        raise ValueError("Carga sem observações")
    return list(observations.values())


class Transform:
    def transform(self, documents):
        rows = unique_observations(documents)
        for row in rows:
            row["data_periodo"], row["ano"], row["trimestre"] = period_parts(
                row["periodo"]
            )
            row["valor"], row["status_valor"] = number_value(row["valor_original"])
        df = pd.DataFrame(rows, columns=COLUMNS)
        df["trimestre"] = df["trimestre"].astype("Int64")
        df["ano"] = df["ano"].astype("int64")
        df["valor"] = df["valor"].astype("float64")
        return df
