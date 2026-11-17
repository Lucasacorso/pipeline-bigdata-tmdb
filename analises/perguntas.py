import argparse

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pymongo import MongoClient
from sklearn.linear_model import LinearRegression

from analises import recomendacao
from pipeline import config

ANO_INICIO = 2000
ANO_FIM = 2023
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)


def banco():
    return MongoClient(config.MONGO_URI)[config.MONGO_DB]


def minimo(db, base_completa, amostra):
    return base_completa if db.filmes.estimated_document_count() >= 100_000 else amostra


def salvar(df, nome):
    config.SAIDAS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.SAIDAS_DIR / f"{nome}.csv", index=False, encoding="utf-8-sig")


def titulo(texto):
    print("\n" + "=" * 90 + f"\n{texto}\n" + "=" * 90)


def generos_em_crescimento(db):
    titulo(f"01. Quais gêneros crescem a cada ano? ({ANO_INICIO}-{ANO_FIM})")
    linhas = list(
        db.resumo_genero_ano.find(
            {"ano": {"$gte": ANO_INICIO, "$lte": ANO_FIM}}, {"_id": 0, "genero": 1, "ano": 1, "qtd_filmes": 1}
        )
    )
    tabela = pd.DataFrame(linhas).pivot_table(index="ano", columns="genero", values="qtd_filmes", aggfunc="sum").fillna(0)
    anos = tabela.index.to_numpy(dtype=float)
    resultado = pd.DataFrame(
        {
            "genero": tabela.columns,
            "filmes_por_ano_crescimento": [round(np.polyfit(anos, tabela[g].to_numpy(), 1)[0], 1) for g in tabela.columns],
            f"filmes_{ANO_INICIO}": tabela.loc[tabela.index.min()].to_numpy().astype(int),
            f"filmes_{ANO_FIM}": tabela.loc[tabela.index.max()].to_numpy().astype(int),
        }
    ).sort_values("filmes_por_ano_crescimento", ascending=False)
    print(resultado.head(10).to_string(index=False))
    salvar(resultado, "01_generos_crescimento")
    top = resultado.head(5)["genero"].tolist()
    ax = tabela[top].plot(figsize=(10, 5), marker="o", markersize=3)
    ax.set_title("Filmes lançados por ano — 5 gêneros que mais crescem")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Filmes")
    plt.tight_layout()
    plt.savefig(config.SAIDAS_DIR / "01_generos_crescimento.png", dpi=120)
    plt.close()


def receita_vs_orcamento(db):
    titulo("02. A receita acompanha o orçamento?")
    cursor = db.filmes.find(
        {"financeiro.orcamento": {"$gte": 100_000}, "financeiro.receita": {"$gte": 100_000}},
        {"_id": 0, "titulo": 1, "financeiro.orcamento": 1, "financeiro.receita": 1},
    )
    df = pd.json_normalize(list(cursor)).rename(
        columns={"financeiro.orcamento": "orcamento", "financeiro.receita": "receita"}
    )
    x = np.log10(df[["orcamento"]].to_numpy())
    y = np.log10(df["receita"].to_numpy())
    modelo = LinearRegression().fit(x, y)
    resumo = pd.DataFrame(
        [
            {
                "filmes_analisados": len(df),
                "correlacao_pearson": round(df["orcamento"].corr(df["receita"]), 3),
                "correlacao_spearman": round(df["orcamento"].corr(df["receita"], method="spearman"), 3),
                "elasticidade_log_log": round(modelo.coef_[0], 3),
                "r2_log_log": round(modelo.score(x, y), 3),
                "pct_filmes_com_lucro": round((df["receita"] > df["orcamento"]).mean() * 100, 1),
            }
        ]
    )
    print(resumo.to_string(index=False))
    salvar(resumo, "02_receita_vs_orcamento")
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df["orcamento"], df["receita"], s=4, alpha=0.3)
    grade = np.linspace(x.min(), x.max(), 50).reshape(-1, 1)
    ax.plot(10**grade.ravel(), 10 ** modelo.predict(grade), color="red", label=f"regressão (R²={modelo.score(x, y):.2f})")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Orçamento (US$)")
    ax.set_ylabel("Receita (US$)")
    ax.set_title("Receita x Orçamento (escala log)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(config.SAIDAS_DIR / "02_receita_vs_orcamento.png", dpi=120)
    plt.close()


def produtoras_melhor_avaliadas(db):
    min_filmes = minimo(db, 15, 5)
    titulo(f"03. Que produtoras têm melhor avaliação? (mín. {min_filmes} filmes com 200+ votos)")
    pipeline = [
        {"$match": {"avaliacao.votos": {"$gte": 200}}},
        {"$unwind": "$produtoras"},
        {
            "$group": {
                "_id": "$produtoras",
                "filmes": {"$sum": 1},
                "nota_media": {"$avg": "$avaliacao.nota_media"},
                "votos_total": {"$sum": "$avaliacao.votos"},
            }
        },
        {"$match": {"filmes": {"$gte": min_filmes}}},
        {"$sort": {"nota_media": -1}},
        {"$limit": 15},
        {"$project": {"_id": 0, "produtora": "$_id", "filmes": 1, "nota_media": {"$round": ["$nota_media", 2]}, "votos_total": 1}},
    ]
    df = pd.DataFrame(list(db.filmes.aggregate(pipeline)))[["produtora", "filmes", "nota_media", "votos_total"]]
    print(df.to_string(index=False))
    salvar(df, "03_produtoras_avaliacao")


def idiomas_alcance(db):
    min_filmes = minimo(db, 500, 3)
    titulo(f"04. Quais idiomas ampliam o alcance? (idiomas com {min_filmes}+ filmes)")
    por_idioma = [
        {"$match": {"idioma_original": {"$ne": None}}},
        {
            "$group": {
                "_id": "$idioma_original",
                "filmes": {"$sum": 1},
                "votos_medios": {"$avg": "$avaliacao.votos"},
                "popularidade_media": {"$avg": "$popularidade"},
                "receita_total": {"$sum": {"$ifNull": ["$financeiro.receita", 0]}},
            }
        },
        {"$match": {"filmes": {"$gte": min_filmes}}},
        {"$sort": {"votos_medios": -1}},
        {"$limit": 15},
        {
            "$project": {
                "_id": 0,
                "idioma": "$_id",
                "filmes": 1,
                "votos_medios": {"$round": ["$votos_medios", 1]},
                "popularidade_media": {"$round": ["$popularidade_media", 2]},
                "receita_total_bi": {"$round": [{"$divide": ["$receita_total", 1e9]}, 2]},
            }
        },
    ]
    df = pd.DataFrame(list(db.filmes.aggregate(por_idioma)))[["idioma", "filmes", "votos_medios", "popularidade_media", "receita_total_bi"]]
    print(df.to_string(index=False))
    salvar(df, "04_idiomas_alcance")
    multilingue = [
        {"$addFields": {"n_idiomas": {"$size": {"$ifNull": ["$idiomas_falados", []]}}}},
        {"$match": {"n_idiomas": {"$gte": 1}}},
        {
            "$group": {
                "_id": {"$min": ["$n_idiomas", 4]},
                "filmes": {"$sum": 1},
                "votos_medios": {"$avg": "$avaliacao.votos"},
                "receita_media": {"$avg": "$financeiro.receita"},
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$project": {
                "_id": 0,
                "idiomas_falados": "$_id",
                "filmes": 1,
                "votos_medios": {"$round": ["$votos_medios", 1]},
                "receita_media_mi": {"$round": [{"$divide": ["$receita_media", 1e6]}, 1]},
            }
        },
    ]
    df2 = pd.DataFrame(list(db.filmes.aggregate(multilingue)))[["idiomas_falados", "filmes", "votos_medios", "receita_media_mi"]]
    df2["idiomas_falados"] = df2["idiomas_falados"].map(lambda n: "4+" if n == 4 else str(n))
    print("\nAlcance por quantidade de idiomas falados no filme:")
    print(df2.to_string(index=False))
    salvar(df2, "04_idiomas_multilingue")


def titulos_para_licenciar(db, top=20):
    titulo("06. Quais títulos priorizar no licenciamento? (nota ponderada + popularidade, lançados desde 2015)")
    base = pd.json_normalize(
        list(
            db.filmes.find(
                {"avaliacao.votos": {"$gte": 50}, "status": "Released", "adulto": {"$ne": True}},
                {"titulo": 1, "lancamento.ano": 1, "avaliacao": 1, "popularidade": 1, "generos": 1},
            )
        )
    )
    c = base["avaliacao.nota_media"].mean()
    m = base["avaliacao.votos"].quantile(0.90)
    v = base["avaliacao.votos"]
    r = base["avaliacao.nota_media"]
    base["nota_ponderada"] = (v / (v + m)) * r + (m / (v + m)) * c
    base["pop_percentil"] = base["popularidade"].rank(pct=True)
    base["score"] = (0.7 * base["nota_ponderada"] / 10 + 0.3 * base["pop_percentil"]).round(4)
    candidatos = base[(base["avaliacao.votos"] >= m) & (base["lancamento.ano"] >= 2015)]
    ranking = candidatos.sort_values("score", ascending=False).head(top)
    ranking = ranking.assign(
        generos=ranking["generos"].map(lambda g: ", ".join(g[:3]) if isinstance(g, list) else ""),
        nota_ponderada=ranking["nota_ponderada"].round(2),
    )
    saida = ranking[["_id", "titulo", "lancamento.ano", "avaliacao.nota_media", "avaliacao.votos", "nota_ponderada", "score", "generos"]]
    saida.columns = ["id", "titulo", "ano", "nota", "votos", "nota_ponderada", "score", "generos"]
    saida = saida.astype({"ano": int, "votos": int})
    print(f"C (nota média global) = {c:.2f} | m (votos mínimos, p90) = {m:.0f}")
    print(saida.drop(columns="id").to_string(index=False))
    salvar(saida, "06_ranking_licenciamento")
    db.ranking_licenciamento.drop()
    db.ranking_licenciamento.insert_many(
        [{"_id": int(r.pop("id")), "posicao": i, **r} for i, r in enumerate(saida.to_dict("records"), start=1)]
    )


def padroes_recomendacao(db, filme="Inception", min_votos=300):
    titulo("05. Que padrões apoiam recomendações? (TF-IDF de gêneros, palavras-chave e produtoras + kNN)")
    df = recomendacao.carregar(db, min_votos)
    print(f"Treinando com {len(df)} filmes com {min_votos}+ votos...")
    distancias, indices = recomendacao.treinar(df)
    total = recomendacao.gravar(db, df, distancias, indices)
    print(f"{total} listas de similares gravadas em {config.MONGO_DB}.recomendacoes")
    recomendacao.recomendar(db, filme)


PERGUNTAS = {
    1: generos_em_crescimento,
    2: receita_vs_orcamento,
    3: produtoras_melhor_avaliadas,
    4: idiomas_alcance,
    5: padroes_recomendacao,
    6: titulos_para_licenciar,
}


def main():
    parser = argparse.ArgumentParser(description="Responde as 6 perguntas de negócio da N2 consultando o MongoDB")
    parser.add_argument("perguntas", nargs="*", type=int, help="números das perguntas de 1 a 6 (padrão: todas)")
    args = parser.parse_args()
    invalidas = [n for n in args.perguntas if n not in PERGUNTAS]
    if invalidas:
        parser.error(f"perguntas inválidas: {invalidas} (use 1 a 6)")
    db = banco()
    for numero in args.perguntas or sorted(PERGUNTAS):
        PERGUNTAS[numero](db)
    print(f"\nCSVs e gráficos salvos em {config.SAIDAS_DIR}")


if __name__ == "__main__":
    main()
