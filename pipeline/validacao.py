import logging

from pyspark.sql import functions as F
from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
)

from . import config

log = logging.getLogger("validacao")

SCHEMA = StructType(
    [
        StructField("id", LongType()),
        StructField("title", StringType()),
        StructField("vote_average", DoubleType()),
        StructField("vote_count", LongType()),
        StructField("status", StringType()),
        StructField("release_date", StringType()),
        StructField("revenue", LongType()),
        StructField("runtime", IntegerType()),
        StructField("adult", BooleanType()),
        StructField("backdrop_path", StringType()),
        StructField("budget", LongType()),
        StructField("homepage", StringType()),
        StructField("imdb_id", StringType()),
        StructField("original_language", StringType()),
        StructField("original_title", StringType()),
        StructField("overview", StringType()),
        StructField("popularity", DoubleType()),
        StructField("poster_path", StringType()),
        StructField("tagline", StringType()),
        StructField("genres", StringType()),
        StructField("production_companies", StringType()),
        StructField("production_countries", StringType()),
        StructField("spoken_languages", StringType()),
        StructField("keywords", StringType()),
        StructField("_corrupt_record", StringType()),
    ]
)

def regras():
    return {
        "registro_malformado": F.col("_corrupt_record").isNotNull(),
        "id_ausente": F.col("id").isNull(),
        "titulo_ausente": F.col("title").isNull() | (F.trim(F.col("title")) == ""),
        "nota_fora_do_intervalo": (F.col("vote_average") < 0) | (F.col("vote_average") > 10),
        "valor_financeiro_negativo": (F.col("budget") < 0) | (F.col("revenue") < 0),
        "duracao_negativa": F.col("runtime") < 0,
    }


def ler_csv(spark):
    caminho = str(config.RAW_DIR / config.CSV_NAME)
    df = (
        spark.read.schema(SCHEMA)
        .option("header", "true")
        .option("multiLine", "true")
        .option("quote", '"')
        .option("escape", '"')
        .option("encoding", "UTF-8")
        .option("mode", "PERMISSIVE")
        .option("columnNameOfCorruptRecord", "_corrupt_record")
        .csv(caminho)
    )
    if config.SAMPLE_ROWS > 0:
        df = df.limit(config.SAMPLE_ROWS)
    return df


def validar(spark):
    bruto = ler_csv(spark).repartition(16)
    condicoes = regras()
    motivos = F.filter(
        F.array(*[F.when(F.coalesce(cond, F.lit(False)), F.lit(nome)) for nome, cond in condicoes.items()]),
        lambda m: m.isNotNull(),
    )
    marcado = bruto.withColumn("motivos", motivos).cache()
    agregados = marcado.agg(
        F.count(F.lit(1)).alias("total_lido"),
        F.sum(F.when(F.size("motivos") > 0, 1).otherwise(0)).alias("total_rejeitado"),
        *[F.sum(F.when(F.array_contains("motivos", nome), 1).otherwise(0)).alias(nome) for nome in condicoes],
    ).first().asDict()
    rejeitados = marcado.filter(F.size("motivos") > 0)
    rejeitados.select("id", "title", "motivos", "_corrupt_record").write.mode("overwrite").json(str(config.QUARENTENA_DIR))
    validos = marcado.filter(F.size("motivos") == 0).drop("motivos", "_corrupt_record")
    agregados["total_valido"] = agregados["total_lido"] - agregados["total_rejeitado"]
    log.info("Validação: %s", agregados)
    return validos, agregados
