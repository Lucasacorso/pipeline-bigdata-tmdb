import pandas as pd
from bson import json_util
from pymongo import MongoClient

from pipeline import config

pd.set_option("display.width", 200)


def cabecalho(texto):
    print("\n" + "=" * 90 + f"\n{texto}\n" + "=" * 90)


def main():
    db = MongoClient(config.MONGO_URI)[config.MONGO_DB]

    cabecalho("Contagem de documentos por coleção")
    for colecao in ("filmes", "resumo_genero_ano", "recomendacoes", "ranking_licenciamento"):
        print(f"  {colecao:<24}{db[colecao].count_documents({}):>10,}")

    cabecalho("Um documento completo (modelo embutido da N2)")
    documento = db.filmes.find_one({"titulo": "Interstellar"}, {"sinopse": 0, "palavras_chave": {"$slice": 5}})
    print(json_util.dumps(documento, indent=2, ensure_ascii=False, json_options=json_util.RELAXED_JSON_OPTIONS))

    cabecalho("Top 5 de Ficção Científica de 2014 por votos (consulta direta, sem $lookup)")
    cursor = (
        db.filmes.find(
            {"generos": "Science Fiction", "lancamento.ano": 2014},
            {"_id": 0, "titulo": 1, "avaliacao.nota_media": 1, "avaliacao.votos": 1},
        )
        .sort("avaliacao.votos", -1)
        .limit(5)
    )
    print(pd.json_normalize(list(cursor)).to_string(index=False))

    cabecalho("Coleção pré-agregada resumo_genero_ano: Drama x Terror, 2014-2023")
    linhas = db.resumo_genero_ano.find(
        {"genero": {"$in": ["Drama", "Horror"]}, "ano": {"$gte": 2014, "$lte": 2023}},
        {"_id": 0, "genero": 1, "ano": 1, "qtd_filmes": 1},
    )
    tabela = pd.DataFrame(list(linhas))
    if not tabela.empty:
        print(tabela.pivot_table(index="ano", columns="genero", values="qtd_filmes", fill_value=0).astype(int).to_string())

    cabecalho("Consulta por gênero usando índice (explain)")
    estatisticas = db.filmes.find({"generos": "Animation"}).explain()["executionStats"]
    print(f"  documentos retornados   {estatisticas['nReturned']}")
    print(f"  chaves de índice lidas  {estatisticas['totalKeysExamined']}")
    print(f"  documentos examinados   {estatisticas['totalDocsExamined']}")
    print(f"  tempo                   {estatisticas['executionTimeMillis']} ms")

    cabecalho("Top 5 do ranking de licenciamento")
    ranking = db.ranking_licenciamento.find({}, {"_id": 0, "posicao": 1, "titulo": 1, "ano": 1, "score": 1}).sort("posicao", 1).limit(5)
    print(pd.DataFrame(list(ranking)).to_string(index=False))


if __name__ == "__main__":
    main()
