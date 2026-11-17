# Consultas para rodar no MongoDB Compass

Cada pergunta da N2 virou um *aggregation pipeline*. É o mesmo pipeline que o Python executa em `python -m analises.consultas_mongo` (fonte: `analises/pipelines.py`).

## Como colar um pipeline no Compass

1. Conecte em `mongodb://localhost:27017` e abra o banco **`tmdb`**.
2. Clique na **coleção** indicada na pergunta.
3. Abra a aba **Aggregations**.
4. Clique no botão **`</>`** (*Text*), ao lado de *Stages*, para editar em texto.
5. Apague o conteúdo, cole o pipeline e clique em **Run**.

> Os limites mínimos estão ajustados para a base de exemplo de **1.000 filmes**. Com a base inteira, troque `"$gte": 5` por `15` na pergunta 03 e `"$gte": 3` por `500` na 04a.

Para conferir sem o Compass: `python -m analises.consultas_mongo --mostrar-pipeline`.

## Consultas rápidas (aba *Documents*, campo *Filter*)

| O que mostrar | Coleção | Filter | Sort |
|---|---|---|---|
| Documento completo de um filme | `filmes` | `{ "titulo": "Interstellar" }` | |
| Ficção científica de 2014 | `filmes` | `{ "generos": "Science Fiction", "lancamento.ano": 2014 }` | `{ "avaliacao.votos": -1 }` |
| Filmes de uma produtora | `filmes` | `{ "produtoras": "Pixar" }` | `{ "avaliacao.nota_media": -1 }` |
| Resumo pré-agregado de um gênero | `resumo_genero_ano` | `{ "genero": "Horror" }` | `{ "ano": -1 }` |
| Recomendações de um filme | `recomendacoes` | `{ "titulo": "Inception" }` | |
| Ranking de licenciamento salvo | `ranking_licenciamento` | `{}` | `{ "posicao": 1 }` |

## 01. Quais gêneros crescem a cada ano? (2000-2023)

**Coleção:** `resumo_genero_ano`

```json
[
  {
    "$match": {
      "ano": {
        "$gte": 2000,
        "$lte": 2023
      }
    }
  },
  {
    "$group": {
      "_id": "$genero",
      "soma_xy": {
        "$sum": {
          "$multiply": [
            {
              "$subtract": [
                "$ano",
                2011.5
              ]
            },
            "$qtd_filmes"
          ]
        }
      },
      "filmes_2000": {
        "$sum": {
          "$cond": [
            {
              "$eq": [
                "$ano",
                2000
              ]
            },
            "$qtd_filmes",
            0
          ]
        }
      },
      "filmes_2023": {
        "$sum": {
          "$cond": [
            {
              "$eq": [
                "$ano",
                2023
              ]
            },
            "$qtd_filmes",
            0
          ]
        }
      }
    }
  },
  {
    "$project": {
      "_id": 0,
      "genero": "$_id",
      "crescimento_filmes_por_ano": {
        "$round": [
          {
            "$divide": [
              "$soma_xy",
              1150
            ]
          },
          1
        ]
      },
      "filmes_2000": 1,
      "filmes_2023": 1
    }
  },
  {
    "$sort": {
      "crescimento_filmes_por_ano": -1
    }
  },
  {
    "$limit": 10
  }
]
```

**Resultado esperado (1.000 filmes):** Action, Adventure e Science Fiction no topo; `crescimento_filmes_por_ano` é a inclinação da reta de filmes lançados por ano.

## 02. A receita acompanha o orçamento?

**Coleção:** `filmes`

```json
[
  {
    "$match": {
      "financeiro.orcamento": {
        "$gte": 100000
      },
      "financeiro.receita": {
        "$gte": 100000
      }
    }
  },
  {
    "$set": {
      "x": {
        "$divide": [
          "$financeiro.orcamento",
          1000000
        ]
      },
      "y": {
        "$divide": [
          "$financeiro.receita",
          1000000
        ]
      }
    }
  },
  {
    "$group": {
      "_id": null,
      "n": {
        "$sum": 1
      },
      "sx": {
        "$sum": "$x"
      },
      "sy": {
        "$sum": "$y"
      },
      "sxx": {
        "$sum": {
          "$multiply": [
            "$x",
            "$x"
          ]
        }
      },
      "syy": {
        "$sum": {
          "$multiply": [
            "$y",
            "$y"
          ]
        }
      },
      "sxy": {
        "$sum": {
          "$multiply": [
            "$x",
            "$y"
          ]
        }
      },
      "com_lucro": {
        "$sum": {
          "$cond": [
            {
              "$gt": [
                "$y",
                "$x"
              ]
            },
            1,
            0
          ]
        }
      },
      "orcamento_medio_mi": {
        "$avg": "$x"
      },
      "receita_media_mi": {
        "$avg": "$y"
      }
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
              {
                "$subtract": [
                  {
                    "$multiply": [
                      "$n",
                      "$sxy"
                    ]
                  },
                  {
                    "$multiply": [
                      "$sx",
                      "$sy"
                    ]
                  }
                ]
              },
              {
                "$sqrt": {
                  "$multiply": [
                    {
                      "$subtract": [
                        {
                          "$multiply": [
                            "$n",
                            "$sxx"
                          ]
                        },
                        {
                          "$multiply": [
                            "$sx",
                            "$sx"
                          ]
                        }
                      ]
                    },
                    {
                      "$subtract": [
                        {
                          "$multiply": [
                            "$n",
                            "$syy"
                          ]
                        },
                        {
                          "$multiply": [
                            "$sy",
                            "$sy"
                          ]
                        }
                      ]
                    }
                  ]
                }
              }
            ]
          },
          3
        ]
      },
      "pct_filmes_com_lucro": {
        "$round": [
          {
            "$multiply": [
              {
                "$divide": [
                  "$com_lucro",
                  "$n"
                ]
              },
              100
            ]
          },
          1
        ]
      },
      "orcamento_medio_mi": {
        "$round": [
          "$orcamento_medio_mi",
          1
        ]
      },
      "receita_media_mi": {
        "$round": [
          "$receita_media_mi",
          1
        ]
      }
    }
  }
]
```

**Resultado esperado (1.000 filmes):** `correlacao_pearson` ≈ 0,67 (correlação positiva forte) e ~97% dos filmes com lucro.

## 03. Que produtoras têm melhor avaliação? (mín. 5 filmes com 200+ votos)

**Coleção:** `filmes`

```json
[
  {
    "$match": {
      "avaliacao.votos": {
        "$gte": 200
      }
    }
  },
  {
    "$unwind": "$produtoras"
  },
  {
    "$group": {
      "_id": "$produtoras",
      "filmes": {
        "$sum": 1
      },
      "nota_media": {
        "$avg": "$avaliacao.nota_media"
      },
      "votos_total": {
        "$sum": "$avaliacao.votos"
      }
    }
  },
  {
    "$match": {
      "filmes": {
        "$gte": 5
      }
    }
  },
  {
    "$sort": {
      "nota_media": -1
    }
  },
  {
    "$limit": 15
  },
  {
    "$project": {
      "_id": 0,
      "produtora": "$_id",
      "filmes": 1,
      "nota_media": {
        "$round": [
          "$nota_media",
          2
        ]
      },
      "votos_total": 1
    }
  }
]
```

**Resultado esperado (1.000 filmes):** Studio Ghibli (8,36), A Band Apart, Miramax, Fox Searchlight… ordenadas por `nota_media`.

## 04a. Quais idiomas ampliam o alcance? (idiomas com 3+ filmes)

**Coleção:** `filmes`

```json
[
  {
    "$match": {
      "idioma_original": {
        "$ne": null
      }
    }
  },
  {
    "$group": {
      "_id": "$idioma_original",
      "filmes": {
        "$sum": 1
      },
      "votos_medios": {
        "$avg": "$avaliacao.votos"
      },
      "popularidade_media": {
        "$avg": "$popularidade"
      },
      "receita_total": {
        "$sum": {
          "$ifNull": [
            "$financeiro.receita",
            0
          ]
        }
      }
    }
  },
  {
    "$match": {
      "filmes": {
        "$gte": 3
      }
    }
  },
  {
    "$sort": {
      "votos_medios": -1
    }
  },
  {
    "$limit": 15
  },
  {
    "$project": {
      "_id": 0,
      "idioma": "$_id",
      "filmes": 1,
      "votos_medios": {
        "$round": [
          "$votos_medios",
          1
        ]
      },
      "popularidade_media": {
        "$round": [
          "$popularidade_media",
          2
        ]
      },
      "receita_total_bi": {
        "$round": [
          {
            "$divide": [
              "$receita_total",
              1000000000
            ]
          },
          2
        ]
      }
    }
  }
]
```

**Resultado esperado (1.000 filmes):** fr, ko e ja com mais votos médios que en; en domina em volume (980 filmes) e receita.

## 04b. Filmes falados em mais idiomas alcançam mais público?

**Coleção:** `filmes`

```json
[
  {
    "$set": {
      "n_idiomas": {
        "$size": {
          "$ifNull": [
            "$idiomas_falados",
            []
          ]
        }
      }
    }
  },
  {
    "$match": {
      "n_idiomas": {
        "$gte": 1
      }
    }
  },
  {
    "$group": {
      "_id": {
        "$min": [
          "$n_idiomas",
          4
        ]
      },
      "filmes": {
        "$sum": 1
      },
      "votos_medios": {
        "$avg": "$avaliacao.votos"
      },
      "receita_media": {
        "$avg": "$financeiro.receita"
      }
    }
  },
  {
    "$sort": {
      "_id": 1
    }
  },
  {
    "$project": {
      "_id": 0,
      "idiomas_falados": {
        "$cond": [
          {
            "$eq": [
              "$_id",
              4
            ]
          },
          "4+",
          {
            "$toString": "$_id"
          }
        ]
      },
      "filmes": 1,
      "votos_medios": {
        "$round": [
          "$votos_medios",
          1
        ]
      },
      "receita_media_mi": {
        "$round": [
          {
            "$divide": [
              "$receita_media",
              1000000
            ]
          },
          1
        ]
      }
    }
  }
]
```

**Resultado esperado (1.000 filmes):** Filmes com 4+ idiomas falados têm a maior receita média (~US$ 390 mi).

## 05a. Que padrões apoiam recomendações? (palavras-chave mais comuns por gênero)

**Coleção:** `filmes`

```json
[
  {
    "$match": {
      "avaliacao.votos": {
        "$gte": 300
      }
    }
  },
  {
    "$unwind": "$generos"
  },
  {
    "$unwind": "$palavras_chave"
  },
  {
    "$group": {
      "_id": {
        "genero": "$generos",
        "palavra": "$palavras_chave"
      },
      "filmes": {
        "$sum": 1
      }
    }
  },
  {
    "$group": {
      "_id": "$_id.genero",
      "total": {
        "$sum": "$filmes"
      },
      "top_palavras": {
        "$topN": {
          "n": 5,
          "sortBy": {
            "filmes": -1
          },
          "output": {
            "$concat": [
              "$_id.palavra",
              " (",
              {
                "$toString": "$filmes"
              },
              ")"
            ]
          }
        }
      }
    }
  },
  {
    "$sort": {
      "total": -1
    }
  },
  {
    "$limit": 8
  },
  {
    "$project": {
      "_id": 0,
      "genero": "$_id",
      "top_palavras": 1
    }
  }
]
```

**Resultado esperado (1.000 filmes):** Action → based on comic, superhero, sequel; Science Fiction → dystopia, alien…

## 05b. Recomendações gravadas para 'Inception'

**Coleção:** `recomendacoes`

```json
[
  {
    "$match": {
      "titulo": "Inception"
    }
  },
  {
    "$unwind": "$similares"
  },
  {
    "$project": {
      "_id": 0,
      "porque_assistiu": "$titulo",
      "recomendado": "$similares.titulo",
      "similaridade": "$similares.similaridade"
    }
  }
]
```

**Resultado esperado (1.000 filmes):** The Matrix, The Matrix Resurrections, The Matrix Revolutions… com a similaridade.

## 06. Quais títulos priorizar no licenciamento? (nota ponderada + popularidade, desde 2015)

**Coleção:** `filmes`

```json
[
  {
    "$match": {
      "avaliacao.votos": {
        "$gte": 50
      },
      "status": "Released",
      "adulto": {
        "$ne": true
      }
    }
  },
  {
    "$setWindowFields": {
      "sortBy": {
        "popularidade": 1
      },
      "output": {
        "posicao_pop": {
          "$rank": {}
        },
        "total": {
          "$count": {},
          "window": {
            "documents": [
              "unbounded",
              "unbounded"
            ]
          }
        },
        "C": {
          "$avg": "$avaliacao.nota_media",
          "window": {
            "documents": [
              "unbounded",
              "unbounded"
            ]
          }
        },
        "m_lista": {
          "$percentile": {
            "input": "$avaliacao.votos",
            "p": [
              0.9
            ],
            "method": "approximate"
          },
          "window": {
            "documents": [
              "unbounded",
              "unbounded"
            ]
          }
        }
      }
    }
  },
  {
    "$set": {
      "m": {
        "$first": "$m_lista"
      },
      "v": "$avaliacao.votos",
      "R": "$avaliacao.nota_media"
    }
  },
  {
    "$set": {
      "nota_ponderada": {
        "$add": [
          {
            "$multiply": [
              {
                "$divide": [
                  "$v",
                  {
                    "$add": [
                      "$v",
                      "$m"
                    ]
                  }
                ]
              },
              "$R"
            ]
          },
          {
            "$multiply": [
              {
                "$divide": [
                  "$m",
                  {
                    "$add": [
                      "$v",
                      "$m"
                    ]
                  }
                ]
              },
              "$C"
            ]
          }
        ]
      },
      "pop_percentil": {
        "$divide": [
          "$posicao_pop",
          "$total"
        ]
      }
    }
  },
  {
    "$set": {
      "score": {
        "$round": [
          {
            "$add": [
              {
                "$multiply": [
                  0.7,
                  {
                    "$divide": [
                      "$nota_ponderada",
                      10
                    ]
                  }
                ]
              },
              {
                "$multiply": [
                  0.3,
                  "$pop_percentil"
                ]
              }
            ]
          },
          4
        ]
      }
    }
  },
  {
    "$match": {
      "$expr": {
        "$gte": [
          "$v",
          "$m"
        ]
      },
      "lancamento.ano": {
        "$gte": 2015
      }
    }
  },
  {
    "$sort": {
      "score": -1
    }
  },
  {
    "$limit": 20
  },
  {
    "$project": {
      "_id": 0,
      "titulo": 1,
      "ano": "$lancamento.ano",
      "nota": "$R",
      "votos": "$v",
      "nota_ponderada": {
        "$round": [
          "$nota_ponderada",
          2
        ]
      },
      "score": 1
    }
  }
]
```

**Resultado esperado (1.000 filmes):** Avengers: Infinity War, Coco, Spider-Man: No Way Home, Avengers: Endgame, Inside Out…
