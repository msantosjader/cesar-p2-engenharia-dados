import os
import shutil

import pandas as pd
import pytest

from src.transform import Transform

pytestmark = pytest.mark.spark


@pytest.fixture(scope="module")
def spark():
    pytest.importorskip("pyspark")
    if not shutil.which("java") and not os.getenv("JAVA_HOME"):
        pytest.skip("Java indisponível")
    from src.transform_spark import create_session

    session = create_session()
    yield session
    session.stop()


def test_spark_pandas_equivalence_and_sql(spark, documents):
    from src.transform_spark import transform

    frame = transform(spark, documents)
    result = frame.toPandas().sort_values("observation_id").reset_index(drop=True)
    result["trimestre"] = result["trimestre"].astype("Int64")
    result["ano"] = result["ano"].astype("int64")
    expected = (
        Transform()
        .transform(documents)
        .sort_values("observation_id")
        .reset_index(drop=True)
    )
    pd.testing.assert_frame_equal(result, expected)
    frame.createOrReplaceTempView("pnad_test")
    assert (
        spark.sql("SELECT COUNT(*) AS n FROM pnad_test").first().n == frame.count() == 4
    )


def test_spark_refuses_unbounded_collection(spark, documents):
    from src.transform_spark import transform

    with pytest.raises(ValueError, match="limite local"):
        transform(spark, documents, max_rows=1)


def test_spark_quarters(spark, documents):
    from src.transform_spark import transform

    documents[0]["payload"][0]["resultados"][0]["series"][0]["serie"] = {"202404": "5"}
    row = transform(spark, documents).filter("periodo = '202404'").first()
    assert row.trimestre == 4
    assert str(row.data_periodo) == "2024-10-01"


def test_spark_marker_semantics_match_pandas(spark, documents):
    from src.transform_spark import transform

    documents[0]["payload"][0]["resultados"][0]["series"][0]["serie"] = {
        "2020": "-",
        "2021": "X",
        "2022": "..",
        "2023": "...",
        "2024": None,
    }
    actual = (
        transform(spark, documents)
        .toPandas()
        .sort_values("observation_id")
        .reset_index(drop=True)
    )
    actual["trimestre"] = actual["trimestre"].astype("Int64")
    actual["ano"] = actual["ano"].astype("int64")
    expected = (
        Transform()
        .transform(documents)
        .sort_values("observation_id")
        .reset_index(drop=True)
    )
    pd.testing.assert_frame_equal(actual, expected)
