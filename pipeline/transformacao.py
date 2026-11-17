import logging

from pyspark.sql import Window
from pyspark.sql import functions as F

log = logging.getLogger("transformacao")

TEXTO = [
    "title",
    "status",
    "backdrop_path",
    "homepage",
    "imdb_id",
    "original_language",
    "original_title",
    "overview",
    "poster_path",
    "tagline",
    "genres",
    "production_companies",
    "production_countries",
    "spoken_languages",
    "keywords",
]

LISTAS = {
    "genres": "generos",
    "production_companies": "produtoras",
    "production_countries": "paises_producao",
    "spoken_languages": "idiomas_falados",
    "keywords": "palavras_chave",
}

RENOMEAR = {
    "title": "titulo",
    "original_title": "titulo_original",
    "overview": "sinopse",
    "adult": "adulto",
    "original_language": "idioma_original",
    "popularity": "popularidade",
    "release_date": "data_lancamento",
    "runtime": "duracao_min",
    "budget": "orcamento",
    "revenue": "receita",
    "vote_average": "nota_media",
    "vote_count": "votos",
    "poster_path": "poster",
    "backdrop_path": "backdrop",
}


def _texto_limpo(coluna):
    valor = F.trim(F.col(coluna))
    return F.when(valor == "", None).otherwise(valor)


def _para_array(coluna):
    itens = F.filter(F.transform(F.split(F.col(coluna), ","), lambda x: F.trim(x)), lambda x: x != "")
    return F.when(F.col(coluna).isNull(), F.array().cast("array<string>")).otherwise(F.array_distinct(itens))


def transformar(df):
    df = df.select([_texto_limpo(c).alias(c) if c in TEXTO else F.col(c) for c in df.columns])

    data = F.coalesce(
        F.to_date("release_date", "yyyy-MM-dd"),
        F.to_date("release_date", "dd/MM/yyyy"),
        F.to_date("release_date", "yyyy"),
    )
    df = (
        df.withColumn("release_date", F.when(F.year(data).between(1870, 2035), data))
        .withColumn("ano", F.year("release_date"))
        .withColumn("budget", F.when(F.col("budget") > 0, F.col("budget")))
        .withColumn("revenue", F.when(F.col("revenue") > 0, F.col("revenue")))
        .withColumn("runtime", F.when(F.col("runtime") > 0, F.col("runtime")))
        .withColumn("vote_count", F.coalesce(F.col("vote_count"), F.lit(0)))
        .withColumn("vote_average", F.when(F.col("vote_count") > 0, F.col("vote_average")))
        .withColumn("popularity", F.coalesce(F.col("popularity"), F.lit(0.0)))
        .withColumn("adult", F.coalesce(F.col("adult"), F.lit(False)))
        .withColumn("lucro", F.col("revenue") - F.col("budget"))
        .withColumn("roi", F.round(F.col("revenue") / F.col("budget"), 4))
    )

    janela = Window.partitionBy("id").orderBy(F.col("vote_count").desc(), F.col("popularity").desc())
    df = df.withColumn("_rank", F.row_number().over(janela))
    duplicatas = df.filter(F.col("_rank") > 1).count()
    df = df.filter(F.col("_rank") == 1).drop("_rank")

    for origem, destino in LISTAS.items():
        df = df.withColumn(destino, _para_array(origem)).drop(origem)

    for origem, destino in RENOMEAR.items():
        df = df.withColumnRenamed(origem, destino)

    df = df.withColumn("processado_em", F.current_timestamp())
    log.info("Duplicatas removidas: %d", duplicatas)
    return df, {"duplicatas_removidas": duplicatas}
