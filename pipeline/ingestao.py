import logging

from pymongo import ASCENDING, DESCENDING, MongoClient
from pyspark.sql import functions as F

from . import config

log = logging.getLogger("ingestao")


def documentos_filmes(df):
    return df.select(
        F.col("id").alias("_id"),
        "titulo",
        "titulo_original",
        "sinopse",
        "tagline",
        "status",
        "adulto",
        "imdb_id",
        "idioma_original",
        "popularidade",
        F.struct(
            F.col("data_lancamento").alias("data"),
            F.col("ano"),
            F.col("duracao_min"),
        ).alias("lancamento"),
        F.struct("orcamento", "receita", "lucro", "roi").alias("financeiro"),
        F.struct("nota_media", "votos").alias("avaliacao"),
        F.struct("poster", "backdrop", "homepage").alias("midia"),
        "generos",
        "produtoras",
        "paises_producao",
        "idiomas_falados",
        "palavras_chave",
        "processado_em",
    )


def resumo_genero_ano(df):
    return (
        df.filter(F.col("ano").isNotNull())
        .select("ano", F.explode("generos").alias("genero"), "nota_media", "votos", "receita", "orcamento", "popularidade")
        .groupBy("genero", "ano")
        .agg(
            F.count(F.lit(1)).alias("qtd_filmes"),
            F.round(F.avg(F.when(F.col("votos") >= 10, F.col("nota_media"))), 3).alias("nota_media"),
            F.sum("votos").alias("votos_total"),
            F.sum("receita").alias("receita_total"),
            F.sum("orcamento").alias("orcamento_total"),
            F.round(F.avg("popularidade"), 3).alias("popularidade_media"),
        )
        .withColumn("_id", F.concat_ws("|", F.col("genero"), F.col("ano").cast("string")))
    )


def gravar_mongo(df, colecao):
    (
        df.write.format("mongodb")
        .mode("append")
        .option("connection.uri", config.MONGO_URI)
        .option("database", config.MONGO_DB)
        .option("collection", colecao)
        .option("operationType", "replace")
        .option("idFieldList", "_id")
        .option("upsertDocument", "true")
        .option("ignoreNullValues", "true")
        .option("maxBatchSize", "1000")
        .save()
    )
    log.info("Coleção %s.%s atualizada", config.MONGO_DB, colecao)


def criar_indices():
    db = MongoClient(config.MONGO_URI)[config.MONGO_DB]
    db.filmes.create_index([("lancamento.ano", ASCENDING)])
    db.filmes.create_index([("generos", ASCENDING)])
    db.filmes.create_index([("produtoras", ASCENDING)])
    db.filmes.create_index([("idioma_original", ASCENDING)])
    db.filmes.create_index([("avaliacao.votos", DESCENDING)])
    db.filmes.create_index([("titulo", ASCENDING)])
    db.resumo_genero_ano.create_index([("genero", ASCENDING), ("ano", ASCENDING)])
    return {
        "filmes": db.filmes.estimated_document_count(),
        "resumo_genero_ano": db.resumo_genero_ano.estimated_document_count(),
    }


def ingerir(df):
    gravar_mongo(documentos_filmes(df), "filmes")
    gravar_mongo(resumo_genero_ano(df), "resumo_genero_ano")
    contagens = criar_indices()
    log.info("Documentos no MongoDB: %s", contagens)
    return contagens
