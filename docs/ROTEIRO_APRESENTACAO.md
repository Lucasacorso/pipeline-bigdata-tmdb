# Roteiro de apresentação — N3 (≈15 min)

**Equipe:** Henrique · Lucas · Luis Gustavo

## Antes de começar (checklist, 10 min antes)

- [ ] `Get-Service MongoDB` → *Running*
- [ ] Pipeline já executado uma vez (Parquet e Mongo carregados) — demo ao vivo usa amostra
- [ ] 3 janelas abertas: **VS Code** (código), **PowerShell** na pasta `n3` com `. .\ambiente.ps1` já rodado, **MongoDB Compass** conectado em `mongodb://localhost:27017`
- [ ] Explorador de arquivos na pasta `n3\data`
- [ ] Repositório do GitHub aberto no navegador
- [ ] Apagar a amostra anterior: `Remove-Item -Recurse data\parquet, data\quarentena` (para mostrar sendo gerado)

---

## 1. Abertura — o problema (1 min) · *Henrique*

> "Na N2 especificamos um pipeline para responder: **qual filme merece entrar no catálogo de um streaming?** Hoje mostramos ele implementado e rodando, do CSV bruto do Kaggle até documentos prontos no MongoDB."

Mostrar o diagrama do README: **Captura → Validação → Limpeza → Parquet → MongoDB → Análise**.

## 2. Estrutura do código (2 min) · *Henrique*

No VS Code, mostrar a árvore de pastas e explicar rapidamente:

- `pipeline/` — uma etapa por arquivo, igual ao slide "Pipeline em 5 etapas" da N2
- `pipeline/main.py` — orquestrador, mede tempo e gera o relatório
- `analises/` — as 6 perguntas da N2
- `setup.ps1` / `executar.ps1` — reprodutível em qualquer máquina Windows

## 3. Dado cru (2 min) · *Lucas*

```powershell
python -m demo.cru_vs_estruturado --id 157336
```

Parar nas seções **1** e **2** e apontar:

- CSV de ~930 mil filmes, um arquivo só
- **Tudo é texto**: `genres = "Adventure, Drama, Science Fiction"` é uma string, não uma lista
- `budget = 0` e `revenue = 0` significam *desconhecido*, não zero
- sinopses com vírgulas, aspas e quebras de linha → por isso o Spark lê com `multiLine` e `escape`

## 4. Rodando o pipeline ao vivo (4 min) · *Lucas*

```powershell
python -m pipeline.main
```

Enquanto roda, narrar os logs de cada etapa e mostrar o código correspondente:

| Log | Mostrar no código |
|---|---|
| `captura` — "CSV já presente" | `captura.py`: Kaggle API com fallback e manifesto |
| `validacao` | `validacao.py`: `SCHEMA` explícito + dicionário `REGRAS` |
| `transformacao` — duplicatas removidas | `transformacao.py`: `_para_array`, datas, zeros → nulo, `row_number` por id |
| `parquet` | `armazenamento.py`: `partitionBy("ano")` |
| `ingestao` | `ingestao.py`: `documentos_filmes` (structs = subdocumentos) e upsert por `_id` |

Ao terminar:

- Abrir `data\parquet\filmes\` → pastas `ano=2014`, `ano=2015`… (**particionamento**)
- Abrir `data\quarentena\` → registros rejeitados com o **motivo**
- Abrir `saidas\relatorio_execucao.json` → contagens e tempo por etapa

> Citar os números da **execução completa**: ver seção "Números para citar" abaixo.

## 5. Dado estruturado no MongoDB (3 min) · *Luis Gustavo*

Na sequência do `demo.cru_vs_estruturado`, seção **3**: o mesmo filme agora é um documento com `lancamento`, `financeiro`, `avaliacao`, `midia` e arrays — **o modelo da N2 exatamente**.

No Compass:

1. Banco `tmdb` → coleções `filmes`, `resumo_genero_ano`, `recomendacoes`, `ranking_licenciamento`
2. Filtro em `filmes`: `{ generos: "Science Fiction", "lancamento.ano": 2014 }` → sem `$lookup`
3. Aba **Indexes** → índices em `generos`, `lancamento.ano`, `produtoras`
4. `resumo_genero_ano` → coleção pré-agregada

Opcional no terminal:

```powershell
python -m demo.consultas_demo
```

Para responder as perguntas direto no Compass, cole os pipelines de `docs\QUERIES_COMPASS.md` na aba **Aggregations**. No terminal, o equivalente é `python -m analises.consultas_mongo`.

## 6. Perguntas que o pipeline destrava (2 min) · *Luis Gustavo*

```powershell
python -m analises.perguntas
```

Ou uma por vez, enquanto comenta: `python -m analises.perguntas 1`, depois `2`, e assim por diante. Para pedir recomendação de outro filme: `python -m analises.recomendacao "The Dark Knight" --sem-treino`.

Mostrar as tabelas no terminal e abrir os gráficos em `saidas\`:

- **01** gêneros que mais crescem (`01_generos_crescimento.png`)
- **02** receita × orçamento (`02_receita_vs_orcamento.png`) — correlação e R²
- **03** produtoras mais bem avaliadas
- **04** idiomas com mais alcance
- **05** "Porque você assistiu…" — recomendação por conteúdo
- **06** top 20 títulos para licenciar

## 7. Fechamento (1 min) · *Henrique*

> "Saímos de um CSV bruto e chegamos a dados confiáveis, particionados e consultáveis, com respostas para as seis perguntas de negócio. O pipeline é idempotente: rodar de novo atualiza os documentos por `_id` sem duplicar — pronto para execução diária em lote, como especificado na N2."

Mostrar o repositório no GitHub com o README de instruções. **Perguntas?**

---

## Números para citar (execução completa, base inteira)

| Métrica | Valor |
|---|---|
| CSV bruto | 646 MB |
| Linhas lidas | **1.538.765** |
| Rejeitadas na validação | **28** (26 sem título, 1 valor financeiro negativo, 1 duração negativa) |
| Duplicatas removidas | **1.407** |
| Filmes no MongoDB | **1.537.330** |
| Documentos em `resumo_genero_ano` | **2.563** |
| Tempo até gravar o Parquet | cerca de 1 min (validação ~30 s, Parquet ~35 s) |

Na demo ao vivo usamos os **primeiros 1.000 filmes** (`SAMPLE_ROWS=1000`, o padrão), que rodam em cerca de 20 s. Mesmo código e mesmas etapas; muda só o volume.

## Perguntas prováveis da banca

- **Por que Parquet antes do Mongo?** Camada confiável e colunar: reprocessar ou reingerir sem reler o CSV; partição por ano permite carga incremental.
- **Por que embutir em vez de referenciar?** Gêneros/produtoras são lidos junto com o filme; embutir evita `$lookup`. O resumo pré-agregado cobre as consultas analíticas.
- **E se rodar duas vezes?** Upsert por `_id` (`operationType=replace`) — idempotente.
- **Como tratam dado ruim?** Schema explícito, modo PERMISSIVE, regras nomeadas; rejeitados vão para quarentena com o motivo.
- **Escala?** O mesmo código roda num cluster Spark trocando `master("local[*]")`; o Mongo pode ser shardeado por `_id`.
