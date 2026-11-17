# Comandos Python para mostrar os dados no terminal

Rode sempre na pasta `n3`, depois de carregar o ambiente:

```powershell
. .\ambiente.ps1
```

> Use `python -m pacote.modulo`, com pontos e sem `.py`. O comando `python -m .\pipeline\main.py` dá erro.

## 1. Rodar o pipeline (CSV → Parquet → MongoDB)

```powershell
python -m pipeline.main
```
Carrega os primeiros **1.000 filmes**. **Espere:** `Validação: {'total_lido': 1000, ...}` e `Documentos no MongoDB: {'filmes': 1000, 'resumo_genero_ano': 628}`.

## 2. Dado cru x dado estruturado

```powershell
python -m demo.cru_vs_estruturado --id 27205
```
**Espere:**
1. As primeiras linhas do CSV
2. O registro do filme como texto puro
3. O mesmo filme como documento no MongoDB
4. Filmes similares

Outros ids: `157336` (Interstellar) e `155` (The Dark Knight).

## 3. Tour pelo MongoDB

```powershell
python -m demo.consultas_demo
```
**Espere:**
- Contagem de documentos por coleção
- O documento de Interstellar
- Top 5 de ficção científica de 2014
- Drama x Terror por ano
- O `explain` mostrando o índice sendo usado
- Top 5 do ranking

## 4. Responder as perguntas com queries no MongoDB

Executa os *aggregation pipelines* direto no banco, os mesmos do `docs/QUERIES_COMPASS.md`:

```powershell
python -m analises.consultas_mongo
python -m analises.consultas_mongo 3
python -m analises.consultas_mongo 6 --mostrar-pipeline
python -m analises.consultas_mongo 5 --filme "The Dark Knight"
```
O primeiro roda todas. O segundo roda só a pergunta 3. O `--mostrar-pipeline` imprime também o pipeline em JSON, e o `--filme` troca o filme da recomendação.

| Pergunta | O que aparece (1.000 filmes) |
|---|---|
| **01.** Quais gêneros crescem a cada ano? | Action, Adventure e Science Fiction lideram o crescimento |
| **02.** Receita acompanha orçamento? | Correlação de Pearson **0,669** e 97,1% dos filmes com lucro |
| **03.** Que produtoras têm melhor avaliação? | Studio Ghibli (8,36), A Band Apart (7,82), Miramax (7,69)… |
| **04.** Quais idiomas ampliam o alcance? | fr, ko e ja com mais votos médios; filmes com 4+ idiomas têm a maior receita média |
| **05.** Que padrões apoiam recomendações? | Palavras-chave por gênero e recomendações para Inception (The Matrix…) |
| **06.** Quais títulos priorizar? | Avengers: Infinity War, Coco, Spider-Man: No Way Home… |

## 5. Responder as perguntas com análise em Pandas e scikit-learn

Mesmas perguntas, com estatística e Machine Learning. Também gera CSVs e gráficos em `saidas\`:

```powershell
python -m analises.perguntas
python -m analises.perguntas 2
```
O primeiro roda as 6 perguntas; o segundo, uma só.

Diferenças em relação ao item 4:
- **02.** adiciona a regressão log-log, com R² e elasticidade
- **05.** treina o modelo TF-IDF + kNN e grava a coleção `recomendacoes`
- Gera os gráficos `01_generos_crescimento.png` e `02_receita_vs_orcamento.png`

Recomendação para qualquer filme, sem treinar de novo:

```powershell
python -m analises.recomendacao "The Dark Knight" --sem-treino
```

## Ordem sugerida na apresentação

```powershell
python -m demo.cru_vs_estruturado --id 27205
python -m pipeline.main
python -m demo.consultas_demo
python -m analises.consultas_mongo
python -m analises.perguntas
```
1. Mostrar o dado cru.
2. Rodar o pipeline ao vivo.
3. Mostrar o dado estruturado no MongoDB.
4. Responder as perguntas com queries no banco.
5. Mostrar a análise com Pandas e scikit-learn e os gráficos.
