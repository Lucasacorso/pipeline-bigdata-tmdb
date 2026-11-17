import logging

from pyspark.sql import functions as F

from . import config

log = logging.getLogger("parquet")


def gravar_parquet(df):
    destino = str(config.PARQUET_DIR)
    (
        df.repartition("ano")
        .write.mode("overwrite")
        .partitionBy("ano")
        .option("compression", "snappy")
        .parquet(destino)
    )
    log.info("Parquet gravado em %s", destino)


def ler_parquet(spark):
    return spark.read.parquet(str(config.PARQUET_DIR))


def resumo_particoes(df):
    linhas = df.groupBy("ano").count().orderBy(F.col("ano").desc_nulls_last()).collect()
    return {"particoes": len(linhas), "registros": sum(r["count"] for r in linhas)}
