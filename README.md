# Pipeline de Big Data — TMDB Movies → MongoDB

Avaliação N3 · ADS UniCesusc — implementação do pipeline especificado na N2.

**Equipe:** Henrique Hoepers Ferraz · Lucas de Azevedo Corso · Luis Gustavo Angelo · Richard

## Arquitetura

```
CSV Kaggle ──► Validação ──► Limpeza & ──► Parquet ──► MongoDB ──► Análise +
(captura)      Spark+schema  transformação  por ano    (Spark       recomendação
                             (PySpark)                  Connector)  (Pandas/sklearn)
```

| Etapa | Ferramenta | Código | Saída |
|---|---|---|---|
| 1. Captura | Kaggle API (fallback kagglehub) | `pipeline/captura.py` | `data/raw/TMDB_movie_dataset_v11.csv` + `manifesto_captura.json` |
| 2. Validação | PySpark, schema explícito, modo PERMISSIVE | `pipeline/validacao.py` | registros válidos + `data/quarentena/*.json` |
| 3. Limpeza e transformação | PySpark DataFrames | `pipeline/transformacao.py` | nulos tratados, datas normalizadas, tipos convertidos, duplicatas removidas, arrays parseados |
| 4. Armazenamento | Parquet (snappy) particionado por `ano` | `pipeline/armazenamento.py` | `data/parquet/filmes/ano=XXXX/` |
| 5. Ingestão | MongoDB Spark Connector 10.4 (upsert) | `pipeline/ingestao.py` | coleções `filmes` e `resumo_genero_ano` + índices |
| Análise | Pandas, NumPy, scikit-learn, Matplotlib | `analises/` | `saidas/*.csv`, `saidas/*.png`, coleções `recomendacoes` e `ranking_licenciamento` |

## Estrutura de pastas

```
n3/
├── pipeline/                 # pipeline de ingestão (PySpark)
│   ├── config.py             # caminhos, URI do Mongo, variáveis de ambiente
│   ├── sessao.py             # SparkSession + conector MongoDB
│   ├── captura.py            # etapa 1
│   ├── validacao.py          # etapa 2
│   ├── transformacao.py      # etapa 3
│   ├── armazenamento.py      # etapa 4
│   ├── ingestao.py           # etapa 5
│   └── main.py               # orquestrador (CLI)
├── analises/
│   ├── pipelines.py          # aggregation pipelines das 6 perguntas
│   ├── consultas_mongo.py    # executa os pipelines no MongoDB
│   ├── perguntas.py          # as 6 perguntas com Pandas, NumPy e scikit-learn + gráficos
│   └── recomendacao.py       # pergunta 05: TF-IDF + kNN
├── demo/
│   ├── cru_vs_estruturado.py # CSV cru x documento no MongoDB
│   └── consultas_demo.py     # tour pelas coleções, índices e explain
├── data/                     # gerado: raw, quarentena, parquet
├── saidas/                   # gerado: relatórios, CSVs e gráficos
├── conf/log4j2.properties    # logs do Spark enxutos para a demo
├── docs/
│   ├── COMO_RODAR.md         # passo a passo curto com saídas esperadas
│   ├── COMANDOS_PYTHON.md    # comandos para mostrar os dados no terminal
│   ├── QUERIES_COMPASS.md    # pipelines para colar no MongoDB Compass
│   └── ROTEIRO_APRESENTACAO.md
├── tools/                    # gerado pelo setup: hadoop (winutils), MongoDB e mongosh portáteis
├── requirements.txt
├── setup.ps1                 # instala tudo
├── ambiente.ps1              # carrega JAVA_HOME, venv e mongosh no terminal atual
├── iniciar_mongo.ps1         # sobe o MongoDB (serviço ou portátil)
└── executar.ps1              # roda pipeline + análises
```

## Modelo do documento (coleção `filmes`)

```json
{
  "_id": 157336,
  "titulo": "Interstellar",
  "idioma_original": "en",
  "popularidade": 140.24,
  "lancamento": { "data": "2014-11-05", "ano": 2014, "duracao_min": 169 },
  "financeiro": { "orcamento": 165000000, "receita": 701729206, "lucro": 536729206, "roi": 4.2529 },
  "avaliacao":  { "nota_media": 8.417, "votos": 32571 },
  "midia":      { "poster": "/gEU2Q...jpg", "backdrop": "/xJHo...jpg" },
  "generos": ["Adventure", "Drama", "Science Fiction"],
  "produtoras": ["Legendary Pictures", "Syncopy", "Lynda Obst Productions"],
  "paises_producao": ["United Kingdom", "United States of America"],
  "idiomas_falados": ["English"],
  "palavras_chave": ["rescue", "future", "spacecraft", "..."]
}
```

Coleção pré-agregada `resumo_genero_ano`: `{ _id: "Drama|2014", genero, ano, qtd_filmes, nota_media, votos_total, receita_total, orcamento_total, popularidade_media }`.

## Pré-requisitos

- Windows 10/11 com `winget`
- Python 3.11, Java 17 (Temurin), MongoDB Server 8 + mongosh, Git
- ~3 GB livres em disco e 8 GB+ de RAM

## Instalação

```powershell
cd n3
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

O `setup.ps1` instala Python, JDK 17 e Git via winget, baixa o `winutils.exe`/`hadoop.dll` e o MongoDB + mongosh portáteis para `tools\` (sem precisar de administrador), cria o `.venv` e instala o `requirements.txt`. Se já existir um serviço `MongoDB` instalado no Windows, o `iniciar_mongo.ps1` usa esse serviço.

### Credenciais do Kaggle (opcional)

A captura usa a Kaggle API se existir `%USERPROFILE%\.kaggle\kaggle.json` (Kaggle → Settings → *Create New Token*). Sem credenciais, cai para o `kagglehub` (download público). Também é possível baixar manualmente o CSV de
<https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies> e colocá-lo em `data\raw\`.

## Execução

Pipeline completo + análises:

```powershell
powershell -ExecutionPolicy Bypass -File .\executar.ps1
```

Por padrão processa os **primeiros 1.000 filmes** (demo em ~20 s). Opções:

```powershell
.\executar.ps1 -Amostra 0                      # base inteira (~1,5 milhão de linhas)
.\executar.ps1 -Amostra 50000                  # primeiras 50 mil linhas
.\executar.ps1 -Etapas processamento           # só validação/limpeza/parquet
.\executar.ps1 -Etapas ingestao -SemAnalises   # só Parquet -> MongoDB
```

Executando os módulos manualmente:

```powershell
. .\ambiente.ps1
.\iniciar_mongo.ps1
python -m pipeline.main --etapas captura,processamento,ingestao
python -m analises.perguntas
python -m analises.perguntas 2 6
python -m analises.recomendacao "The Dark Knight" --sem-treino
python -m demo.cru_vs_estruturado --id 157336
python -m demo.consultas_demo
python -m analises.consultas_mongo
```

## Saídas esperadas

| Saída | Onde | O que mostra |
|---|---|---|
| Relatório da execução | `saidas/relatorio_execucao.json` | linhas lidas/rejeitadas por regra, duplicatas, partições, docs no Mongo, tempo por etapa |
| Quarentena | `data/quarentena/*.json` | registros rejeitados com o motivo |
| Parquet | `data/parquet/filmes/ano=*/` | dado confiável particionado por ano |
| MongoDB | banco `tmdb` | `filmes`, `resumo_genero_ano`, `recomendacoes`, `ranking_licenciamento` |
| Análises | `saidas/01..06_*.csv` e `*.png` | respostas às 6 perguntas da N2 |

## Perguntas respondidas

1. **Quais gêneros crescem a cada ano?** — inclinação da regressão linear de filmes/ano por gênero (2000–2023) sobre `resumo_genero_ano`.
2. **Receita acompanha orçamento?** — correlação de Pearson/Spearman e regressão log-log (scikit-learn).
3. **Que produtoras têm melhor avaliação?** — `$unwind` em `produtoras`, mínimo de 15 filmes com 200+ votos.
4. **Quais idiomas ampliam o alcance?** — votos e popularidade médios por idioma original e por quantidade de idiomas falados.
5. **Que padrões apoiam recomendações?** — TF-IDF sobre gêneros, palavras-chave e produtoras + kNN por cosseno, gravado em `recomendacoes`.
6. **Quais títulos priorizar no licenciamento?** — nota ponderada (fórmula IMDb) + percentil de popularidade, gravado em `ranking_licenciamento`.

## Problemas comuns

| Sintoma | Solução |
|---|---|
| `JAVA_HOME is not set` | rode via `executar.ps1` ou `$env:JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-17..."` |
| `UnsatisfiedLinkError ... NativeIO` | confirme `tools\hadoop\bin\hadoop.dll` e `winutils.exe` |
| `Connection refused 27017` | `.\iniciar_mongo.ps1` |
| `DLL load failed ... política de Controle de Aplicativo` | o Controle Inteligente de Aplicativos do Windows bloqueia wheels muito novas; use as versões fixadas no `requirements.txt` |
| Linhas `ÊXITO: o processo ... foi finalizado` no fim | normal: é o PySpark encerrando os processos Java no Windows |
| `java.lang.OutOfMemoryError` | `$env:SPARK_DRIVER_MEMORY="4g"` ou use `-Amostra` |
