"""Transformação Spark local com o mesmo contrato Silver do pandas."""

import os

from src.transform import COLUMNS, MISSING, MISSING_STATUS, unique_observations


def create_session():
    from pyspark.sql import SparkSession

    return (
        SparkSession.builder.appName("pnad-projeto")
        .master(os.getenv("SPARK_MASTER", "local[2]"))
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.execution.arrow.pyspark.enabled", "false")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )


def transform(spark, documents, max_rows=100000):
    from pyspark.sql import functions as F
    from pyspark.sql.types import StringType, StructField, StructType

    if max_rows <= 0:
        raise ValueError("max_rows deve ser positivo")
    rows = unique_observations(documents)
    if len(rows) > max_rows:
        raise ValueError("Carga excede limite local; use leitura e carga distribuídas")
    schema = StructType([StructField(key, StringType(), False) for key in rows[0]])
    frame = spark.createDataFrame(rows, schema)
    annual = F.length("periodo") == 4
    marker = F.col("valor_original").isin(sorted(MISSING))
    zero = F.col("valor_original") == "-"
    status_map = F.create_map(
        *[F.lit(item) for pair in MISSING_STATUS.items() for item in pair]
    )
    frame = (
        frame.withColumn("ano", F.substring("periodo", 1, 4).cast("int"))
        .withColumn(
            "trimestre", F.when(~annual, F.substring("periodo", 5, 2).cast("int"))
        )
        .withColumn(
            "data_periodo",
            F.make_date(
                "ano",
                F.when(annual, F.lit(1)).otherwise((F.col("trimestre") - 1) * 3 + 1),
                F.lit(1),
            ),
        )
        .withColumn(
            "valor",
            F.when(zero, F.lit(0.0)).when(
                ~marker, F.regexp_replace("valor_original", ",", ".").cast("double")
            ),
        )
        .withColumn(
            "status_valor",
            F.when(zero, F.lit("zero_absoluto"))
            .when(marker, status_map[F.col("valor_original")])
            .otherwise(F.lit("observado")),
        )
    )
    return frame.select(*COLUMNS)


def transform_to_pandas(documents, max_rows=100000):
    spark = create_session()
    try:
        frame = transform(spark, documents, max_rows)
        # Limite explícito antes de coletar no driver; esta é uma ponte acadêmica local.
        result = frame.toPandas()
        result["trimestre"] = result["trimestre"].astype("Int64")
        result["ano"] = result["ano"].astype("int64")
        result["valor"] = result["valor"].astype("float64")
        return result
    finally:
        spark.stop()
