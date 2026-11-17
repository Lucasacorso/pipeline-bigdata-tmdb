# Divisão das falas (≈15 min, 4 integrantes)

> O PDF da N2 tem 3 nomes. Troque **Integrante 4** pelo nome do quarto membro.

---

## 1. Henrique · Problema e arquitetura (≈3 min)

**Mostrar:** diagrama do `README.md` e a árvore de pastas no VS Code.

**Falar:**
- **O problema:** um streaming precisa decidir quais filmes licenciar e recomendar. Isso exige dados confiáveis.
- **A fonte:** o dataset TMDB do Kaggle, um CSV de 646 MB com cerca de 1,5 milhão de linhas.
- **A solução:** um pipeline em lote com 5 etapas: Captura → Validação → Limpeza → Parquet → MongoDB.
- **O código** segue a especificação da N2:
  - uma etapa por arquivo em `pipeline/`
  - análises em `analises/`
  - scripts `.ps1` para instalar e rodar em qualquer Windows

**Passa para o Lucas:** "Vamos ver como esse dado chega."

---

## 2. Lucas · Dado cru e processamento com Spark (≈4 min)

**Rodar:**
```powershell
python -m demo.cru_vs_estruturado --id 27205
python -m pipeline.main
```
Do primeiro comando, mostrar só as partes 1 e 2. O segundo é o pipeline ao vivo.

**Falar:**
- **Dado cru:** é tudo texto. Gêneros e produtoras vêm numa string separada por vírgula, `budget = 0` significa *desconhecido*, e as sinopses têm aspas e vírgulas.
- **Validação:** schema explícito e 6 regras nomeadas. Quem falha vai para a **quarentena** com o motivo.
- **Limpeza:**
  - zeros viram nulo
  - datas normalizadas
  - listas viram arrays
  - duplicatas removidas por `id`
- **Números da base completa:** 1.538.765 linhas lidas, 28 rejeitadas, 1.407 duplicatas removidas. Ao vivo rodamos 1.000 filmes; o código é o mesmo.

**Mostrar ao final:**
- `data\quarentena\`
- `saidas\relatorio_execucao.json`

**Passa para o Luis:** "O dado limpo vai para o Parquet e o MongoDB."

---

## 3. Luis Gustavo · Parquet e MongoDB (≈4 min)

**Mostrar:**
- `data\parquet\filmes\`, com as pastas `ano=2014`, `ano=2015`…
- A parte 3 do `demo.cru_vs_estruturado`
- O MongoDB Compass

**Falar:**
- **Parquet particionado por ano:** formato colunar e comprimido. Dá para reprocessar sem reler o CSV, e permite carga incremental.
- **Ingestão:** feita com o **Spark Connector** em *upsert* por `_id`. É idempotente: rodar de novo não duplica.
- **Modelo da N2:** um documento por filme, com subdocumentos (`lancamento`, `financeiro`, `avaliacao`, `midia`) e arrays (`generos`, `produtoras`…). O que é consultado junto fica junto, sem `$lookup`.
- **No Compass, mostrar:**
  - o filtro `{ "titulo": "Interstellar" }`
  - a aba **Indexes**
  - a coleção pré-agregada `resumo_genero_ano`

**Passa para o Integrante 4:** "Com o dado pronto, respondemos as perguntas de negócio."

---

## 4. Integrante 4 · Perguntas de negócio e fechamento (≈4 min)

**Rodar:**
```powershell
python -m analises.consultas_mongo
```
Ou cole os pipelines de `docs\QUERIES_COMPASS.md` no Compass. Depois, abrir os gráficos em `saidas\`.

**Falar, uma frase por pergunta:**
1. **Gêneros que crescem:** Action, Adventure e Sci-Fi lideram.
2. **Receita x orçamento:** correlação de 0,67. Investir mais tende a render mais, mas não garante.
3. **Produtoras mais bem avaliadas:** Studio Ghibli, A Band Apart, Miramax.
4. **Idiomas:** filmes em francês, coreano e japonês têm mais engajamento médio. Filmes com 4+ idiomas têm a maior receita.
5. **Recomendação:** um modelo TF-IDF + kNN sobre gêneros e palavras-chave. Quem viu *Inception* recebe *The Matrix*.
6. **Licenciamento:** nota ponderada (fórmula do IMDb) + popularidade. O top 3 é Avengers: Infinity War, Coco e Spider-Man: No Way Home.

**Fechamento:** "Saímos de um CSV bruto e chegamos a dados confiáveis e consultáveis, que respondem as 6 perguntas da N2. O código e as instruções estão no GitHub." Mostrar o repositório e abrir para perguntas.

---

## Perguntas da banca: quem responde

| Pergunta provável | Quem |
|---|---|
| Por que Parquet antes do Mongo? | Luis Gustavo |
| Por que embutir em vez de referenciar? | Luis Gustavo |
| Como tratam dado ruim? | Lucas |
| E se rodar duas vezes? (idempotência) | Luis Gustavo |
| Escala para mais dados? | Henrique: o mesmo código roda num cluster Spark trocando o `master` |
| Como funciona a recomendação ou o ranking? | Integrante 4 |
