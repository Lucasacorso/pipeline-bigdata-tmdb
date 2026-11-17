import argparse
import re

import pandas as pd
from pymongo import MongoClient, ReplaceOne
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from pipeline import config

VIZINHOS = 10


def _tokens(lista, prefixo, peso=1):
    if not isinstance(lista, list):
        return []
    return [f"{prefixo}:{item.lower().replace(' ', '_')}" for item in lista] * peso


def carregar(db, min_votos):
    cursor = db.filmes.find(
        {"avaliacao.votos": {"$gte": min_votos}},
        {"titulo": 1, "generos": 1, "palavras_chave": 1, "produtoras": 1, "lancamento.ano": 1, "avaliacao": 1},
    )
    df = pd.json_normalize(list(cursor))
    df["perfil"] = df.apply(
        lambda f: " ".join(
            _tokens(f.get("generos"), "g", 3) + _tokens(f.get("palavras_chave"), "k") + _tokens(f.get("produtoras"), "p")
        ),
        axis=1,
    )
    return df[df["perfil"].str.len() > 0].reset_index(drop=True)


def treinar(df):
    matriz = TfidfVectorizer(token_pattern=r"[^ ]+", sublinear_tf=True).fit_transform(df["perfil"])
    modelo = NearestNeighbors(n_neighbors=VIZINHOS + 1, metric="cosine").fit(matriz)
    distancias, indices = modelo.kneighbors(matriz)
    return distancias, indices


def gravar(db, df, distancias, indices):
    operacoes = []
    for i, filme_id in enumerate(df["_id"]):
        similares = [
            {"_id": int(df.at[j, "_id"]), "titulo": df.at[j, "titulo"], "similaridade": round(1 - float(d), 4)}
            for d, j in zip(distancias[i], indices[i])
            if j != i
        ][:VIZINHOS]
        operacoes.append(ReplaceOne({"_id": int(filme_id)}, {"_id": int(filme_id), "titulo": df.at[i, "titulo"], "similares": similares}, upsert=True))
    db.recomendacoes.drop()
    db.recomendacoes.bulk_write(operacoes, ordered=False)
    return len(operacoes)


def recomendar(db, titulo):
    filme = db.filmes.find_one(
        {"titulo": {"$regex": f"^{re.escape(titulo)}$", "$options": "i"}}, sort=[("avaliacao.votos", -1)], projection={"titulo": 1, "generos": 1}
    )
    if not filme:
        print(f"Filme '{titulo}' não encontrado")
        return
    rec = db.recomendacoes.find_one({"_id": filme["_id"]})
    if not rec:
        print(f"'{filme['titulo']}' não tem votos suficientes para entrar no modelo")
        return
    print(f"\nPorque você assistiu '{filme['titulo']}' ({', '.join(filme.get('generos', []))}):")
    print(pd.DataFrame(rec["similares"])[["titulo", "similaridade"]].to_string(index=False))


def main():
    parser = argparse.ArgumentParser(description="05. Padrões que apoiam recomendações (similaridade de conteúdo)")
    parser.add_argument("titulo", nargs="?", default="Inception")
    parser.add_argument("--min-votos", type=int, default=300)
    parser.add_argument("--sem-treino", action="store_true")
    args = parser.parse_args()
    db = MongoClient(config.MONGO_URI)[config.MONGO_DB]
    if not args.sem_treino:
        df = carregar(db, args.min_votos)
        print(f"Treinando modelo TF-IDF + kNN (cosseno) com {len(df)} filmes...")
        distancias, indices = treinar(df)
        total = gravar(db, df, distancias, indices)
        print(f"{total} documentos gravados em {config.MONGO_DB}.recomendacoes")
    recomendar(db, args.titulo)


if __name__ == "__main__":
    main()
