from copy import deepcopy

import pandas as pd
import pytest

from src.transform import Transform, number_value, period_parts


def test_all_categories_and_missing_values(documents):
    frame = Transform().transform(documents)
    assert len(frame) == 4
    assert frame.observation_id.nunique() == 4
    assert frame.trimestre.isna().all()
    missing = frame[frame.valor_original == "..."]
    assert missing.valor.isna().all()
    assert missing.status_valor.tolist() == ["nao_disponivel"]
    assert frame[frame.valor_original == "0"].valor.tolist() == [0.0]
    assert frame[frame.valor_original == "3,5"].valor.tolist() == [3.5]


def test_all_variables_and_locations(documents):
    var = deepcopy(documents[0]["payload"][0])
    var["id"] = "999"
    var["resultados"][0]["series"][0]["localidade"]["id"] = "26"
    documents[0]["payload"].append(var)
    frame = Transform().transform(documents)
    assert len(frame) == 8
    assert set(frame.variavel_id) == {"162", "999"}
    assert set(frame.localidade_id) == {"2611606", "26"}


def test_quarters_do_not_change_annual_semantics(documents):
    documents[0]["payload"][0]["resultados"][0]["series"][0]["serie"] = {"202401": "1"}
    frame = Transform().transform(documents)
    assert frame[frame.periodo == "202401"].trimestre.tolist() == [1]
    assert frame[frame.periodo == "2023"].trimestre.isna().all()


@pytest.mark.parametrize("period", ["202413", "202405", "2024Q1", "0000", ""])
def test_invalid_period_rejected(period):
    with pytest.raises(ValueError):
        period_parts(period)


@pytest.mark.parametrize("value", ["NaN", "inf", "abc", "1.2.3"])
def test_invalid_number_rejected(value):
    with pytest.raises(ValueError):
        number_value(value)


def test_conflicting_duplicate_rejected(documents):
    duplicate = deepcopy(documents[0]["payload"][0]["resultados"][0])
    duplicate["series"][0]["serie"]["2023"] = "99"
    documents[0]["payload"][0]["resultados"].append(duplicate)
    with pytest.raises(ValueError, match="conflitantes"):
        Transform().transform(documents)


def test_exact_duplicate_collapsed(documents):
    original = Transform().transform(documents)
    documents[0]["payload"].append(deepcopy(documents[0]["payload"][0]))
    pd.testing.assert_frame_equal(original, Transform().transform(documents))


def test_empty_series_rejected(documents):
    documents[0]["payload"][0]["resultados"] = []
    with pytest.raises(ValueError, match="nenhuma observação"):
        Transform().transform(documents)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("-", (0.0, "zero_absoluto")),
        ("...", (None, "nao_disponivel")),
        ("..", (None, "nao_aplicavel")),
        ("X", (None, "suprimido")),
        ("", (None, "ausente")),
    ],
)
def test_ibge_marker_semantics(raw, expected):
    assert number_value(raw) == expected
