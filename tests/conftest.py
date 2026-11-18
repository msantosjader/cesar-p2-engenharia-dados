from copy import deepcopy

import pytest

from src.bronze import snapshot


@pytest.fixture
def documents():
    result = {
        "classificacoes": [
            {"id": "67", "nome": "Destino do lixo", "categoria": {"1": "Coletado"}}
        ],
        "series": [
            {
                "localidade": {
                    "id": "2611606",
                    "nome": "Recife",
                    "nivel": {"id": "N6", "nome": "Município"},
                },
                "serie": {"2023": "12.5", "2024": "..."},
            }
        ],
    }
    second = deepcopy(result)
    second["classificacoes"][0]["categoria"] = {"2": "Outro"}
    second["series"][0]["serie"] = {"2023": "0", "2024": "3,5"}
    payload = [
        {
            "id": "162",
            "variavel": "Domicílios",
            "unidade": "%",
            "resultados": [result, second],
        }
    ]
    return [snapshot("test-run", 6736, "https://example.invalid/6736", payload)]
