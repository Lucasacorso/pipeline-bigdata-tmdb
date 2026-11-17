JANELA_TOTAL = {"documents": ["unbounded", "unbounded"]}


def limites(total_filmes):
    grande = total_filmes >= 100_000
    return {"min_produtora": 15 if grande else 5, "min_idioma": 500 if grande else 3}


def generos_crescimento():
    return [
        {"$match": {"ano": {"$gte": 2000, "$lte": 2023}}},
        {
            "$group": {
                "_id": "$genero",
                "soma_xy": {"$sum": {"$multiply": [{"$subtract": ["$ano", 2011.5]}, "$qtd_filmes"]}},
                "filmes_2000": {"$sum": {"$cond": [{"$eq": ["$ano", 2000]}, "$qtd_filmes", 0]}},
                "filmes_2023": {"$sum": {"$cond": [{"$eq": ["$ano", 2023]}, "$qtd_filmes", 0]}},
            }
        },
        {
            "$project": {
                "_id": 0,
                "genero": "$_id",
                "crescimento_filmes_por_ano": {"$round": [{"$divide": ["$soma_xy", 1150]}, 1]},
                "filmes_2000": 1,
                "filmes_2023": 1,
            }
        },
        {"$sort": {"crescimento_filmes_por_ano": -1}},
        {"$limit": 10},
    ]


def receita_orcamento():
    diferenca = lambda a, b: {"$subtract": [{"$multiply": ["$n", a]}, {"$multiply": b}]}
    return [
        {"$match": {"financeiro.orcamento": {"$gte": 100000}, "financeiro.receita": {"$gte": 100000}}},
        {"$set": {"x": {"$divide": ["$financeiro.orcamento", 1000000]}, "y": {"$divide": ["$financeiro.receita", 1000000]}}},
        {
            "$group": {
                "_id": None,
                "n": {"$sum": 1},
                "sx": {"$sum": "$x"},
                "sy": {"$sum": "$y"},
                "sxx": {"$sum": {"$multiply": ["$x", "$x"]}},
                "syy": {"$sum": {"$multiply": ["$y", "$y"]}},
                "sxy": {"$sum": {"$multiply": ["$x", "$y"]}},
                "com_lucro": {"$sum": {"$cond": [{"$gt": ["$y", "$x"]}, 1, 0]}},
                "orcamento_medio_mi": {"$avg": "$x"},
                "receita_media_mi": {"$avg": "$y"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "filmes_analisados": "$n",
                "correlacao_pearson": {
                    "$round": [
                        {
                            "$divide": [
                                diferenca("$sxy", ["$sx", "$sy"]),
                                {"$sqrt": {"$multiply": [diferenca("$sxx", ["$sx", "$sx"]), diferenca("$syy", ["$sy", "$sy"])]}},
                            ]
                        },
                        3,
                    ]
                },
                "pct_filmes_com_lucro": {"$round": [{"$multiply": [{"$divide": ["$com_lucro", "$n"]}, 100]}, 1]},
                "orcamento_medio_mi": {"$round": ["$orcamento_medio_mi", 1]},
                "receita_media_mi": {"$round": ["$receita_media_mi", 1]},
            }
        },
    ]


def produtoras_avaliacao(min_filmes):
    return [
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


def idiomas_alcance(min_filmes):
    return [
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
                "receita_total_bi": {"$round": [{"$divide": ["$receita_total", 1000000000]}, 2]},
            }
        },
    ]


def idiomas_multilingue():
    return [
        {"$set": {"n_idiomas": {"$size": {"$ifNull": ["$idiomas_falados", []]}}}},
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
                "idiomas_falados": {"$cond": [{"$eq": ["$_id", 4]}, "4+", {"$toString": "$_id"}]},
                "filmes": 1,
                "votos_medios": {"$round": ["$votos_medios", 1]},
                "receita_media_mi": {"$round": [{"$divide": ["$receita_media", 1000000]}, 1]},
            }
        },
    ]


def padroes_por_genero():
    return [
        {"$match": {"avaliacao.votos": {"$gte": 300}}},
        {"$unwind": "$generos"},
        {"$unwind": "$palavras_chave"},
        {"$group": {"_id": {"genero": "$generos", "palavra": "$palavras_chave"}, "filmes": {"$sum": 1}}},
        {
            "$group": {
                "_id": "$_id.genero",
                "total": {"$sum": "$filmes"},
                "top_palavras": {
                    "$topN": {
                        "n": 5,
                        "sortBy": {"filmes": -1},
                        "output": {"$concat": ["$_id.palavra", " (", {"$toString": "$filmes"}, ")"]},
                    }
                },
            }
        },
        {"$sort": {"total": -1}},
        {"$limit": 8},
        {"$project": {"_id": 0, "genero": "$_id", "top_palavras": 1}},
    ]


def recomendacoes_de(titulo):
    return [
        {"$match": {"titulo": titulo}},
        {"$unwind": "$similares"},
        {"$project": {"_id": 0, "porque_assistiu": "$titulo", "recomendado": "$similares.titulo", "similaridade": "$similares.similaridade"}},
    ]


def ranking_licenciamento():
    return [
        {"$match": {"avaliacao.votos": {"$gte": 50}, "status": "Released", "adulto": {"$ne": True}}},
        {
            "$setWindowFields": {
                "sortBy": {"popularidade": 1},
                "output": {
                    "posicao_pop": {"$rank": {}},
                    "total": {"$count": {}, "window": JANELA_TOTAL},
                    "C": {"$avg": "$avaliacao.nota_media", "window": JANELA_TOTAL},
                    "m_lista": {
                        "$percentile": {"input": "$avaliacao.votos", "p": [0.9], "method": "approximate"},
                        "window": JANELA_TOTAL,
                    },
                },
            }
        },
        {"$set": {"m": {"$first": "$m_lista"}, "v": "$avaliacao.votos", "R": "$avaliacao.nota_media"}},
        {
            "$set": {
                "nota_ponderada": {
                    "$add": [
                        {"$multiply": [{"$divide": ["$v", {"$add": ["$v", "$m"]}]}, "$R"]},
                        {"$multiply": [{"$divide": ["$m", {"$add": ["$v", "$m"]}]}, "$C"]},
                    ]
                },
                "pop_percentil": {"$divide": ["$posicao_pop", "$total"]},
            }
        },
        {
            "$set": {
                "score": {
                    "$round": [
                        {"$add": [{"$multiply": [0.7, {"$divide": ["$nota_ponderada", 10]}]}, {"$multiply": [0.3, "$pop_percentil"]}]},
                        4,
                    ]
                }
            }
        },
        {"$match": {"$expr": {"$gte": ["$v", "$m"]}, "lancamento.ano": {"$gte": 2015}}},
        {"$sort": {"score": -1}},
        {"$limit": 20},
        {
            "$project": {
                "_id": 0,
                "titulo": 1,
                "ano": "$lancamento.ano",
                "nota": "$R",
                "votos": "$v",
                "nota_ponderada": {"$round": ["$nota_ponderada", 2]},
                "score": 1,
            }
        },
    ]


def consultas(total_filmes, filme="Inception"):
    lim = limites(total_filmes)
    return [
        ("1", "01. Quais gêneros crescem a cada ano? (2000-2023)", "resumo_genero_ano", generos_crescimento()),
        ("2", "02. A receita acompanha o orçamento?", "filmes", receita_orcamento()),
        (
            "3",
            f"03. Que produtoras têm melhor avaliação? (mín. {lim['min_produtora']} filmes com 200+ votos)",
            "filmes",
            produtoras_avaliacao(lim["min_produtora"]),
        ),
        ("4", f"04a. Quais idiomas ampliam o alcance? (idiomas com {lim['min_idioma']}+ filmes)", "filmes", idiomas_alcance(lim["min_idioma"])),
        ("4", "04b. Filmes falados em mais idiomas alcançam mais público?", "filmes", idiomas_multilingue()),
        ("5", "05a. Que padrões apoiam recomendações? (palavras-chave mais comuns por gênero)", "filmes", padroes_por_genero()),
        ("5", f"05b. Recomendações gravadas para '{filme}'", "recomendacoes", recomendacoes_de(filme)),
        ("6", "06. Quais títulos priorizar no licenciamento? (nota ponderada + popularidade, desde 2015)", "filmes", ranking_licenciamento()),
    ]
