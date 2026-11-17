# Como rodar

Todos os comandos no PowerShell, dentro da pasta `n3`.

## 0. Instalar (só na primeira vez)

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
.\setup.ps1
```
O primeiro comando libera os scripts `.ps1`; sem ele aparece o erro *"a execução de scripts foi desabilitada"*.
**Espere:** `Ambiente pronto. Execute: .\executar.ps1`

## 1. Preparar o terminal (sempre que abrir um novo)

```powershell
. .\ambiente.ps1
.\iniciar_mongo.ps1
```
Atenção ao **ponto + espaço** antes de `.\ambiente.ps1`: sem ele as variáveis não ficam no terminal.

**Espere:**
- `Ambiente carregado: JAVA_HOME=... | venv ativo | mongosh no PATH`
- `MongoDB ... rodando em localhost:27017`

## 2. Rodar o pipeline

```powershell
python -m pipeline.main
```
Por padrão o pipeline processa os **primeiros 1.000 filmes** do CSV, em cerca de 20 segundos.

**Espere:**
- `===== Etapa: captura =====` → `CSV já presente` ou o download
- `===== Etapa: processamento =====` → `Validação: {'total_lido': 1000, 'total_rejeitado': 0, ...}` e `Duplicatas removidas: 0`
- `===== Etapa: ingestao =====` → `Documentos no MongoDB: {'filmes': 1000, 'resumo_genero_ano': 628}`
- No fim, `Relatório final` em JSON
- As linhas `ÊXITO: o processo ... foi finalizado` no final são normais

**Arquivos gerados:**
- `data\parquet\filmes\ano=XXXX\`
- `data\quarentena\`
- `saidas\relatorio_execucao.json`

Outro tamanho: `$env:SAMPLE_ROWS="50000"; python -m pipeline.main` (use `"0"` para a base inteira, ~1,5 milhão de linhas, cerca de 10 minutos).

## 3. Responder as 6 perguntas da N2

```powershell
python -m analises.perguntas
```
Para uma pergunta só: `python -m analises.perguntas 1` ou `python -m analises.perguntas 5 6`.

**Espere:** 6 blocos numerados de `01.` a `06.`:
- **01.** gêneros que mais crescem
- **02.** correlação entre receita e orçamento
- **03.** produtoras mais bem avaliadas
- **04.** idiomas com mais alcance
- **05.** os 10 filmes recomendados para *Inception*
- **06.** os 20 títulos para licenciar

**Arquivos gerados:** `saidas\01..06_*.csv` e os gráficos `01_generos_crescimento.png` e `02_receita_vs_orcamento.png`.

## 4. Recomendação para outro filme

```powershell
python -m analises.recomendacao "The Dark Knight" --sem-treino
```
**Espere:** a lista `Porque você assistiu 'The Dark Knight'` com 10 filmes e a similaridade de cada um.

## 5. Mostrar dado cru x estruturado

```powershell
python -m demo.cru_vs_estruturado --id 157336
```
Outros ids que estão entre os 1.000 carregados: `27205` (Inception) e `155` (The Dark Knight).
**Espere:**
1. As primeiras linhas do CSV
2. O registro do filme como texto puro
3. O mesmo filme no MongoDB, com `lancamento`, `financeiro`, `avaliacao`, `midia` e as listas
4. Filmes similares e a posição no ranking de licenciamento

## 6. Consultas no MongoDB

```powershell
python -m demo.consultas_demo
python -m analises.consultas_mongo
```
O segundo comando responde as 6 perguntas com queries no banco. Veja `docs\COMANDOS_PYTHON.md` e `docs\QUERIES_COMPASS.md`.

**Espere** (no primeiro comando):
- Contagem de documentos por coleção
- O documento de Interstellar
- Top 5 de ficção científica de 2014
- Drama x Terror por ano
- O `explain` mostrando o índice sendo usado
- Top 5 do ranking

## 7. Ver no MongoDB Compass

1. Abra o **MongoDB Compass** pelo menu Iniciar.
2. Conecte em `mongodb://localhost:27017`.
3. Abra o banco **`tmdb`** e a coleção **`filmes`**.
4. Filtre com `{ titulo: "Interstellar" }`.
5. Veja também as abas **Schema** e **Indexes**.

---

**Tudo de uma vez:** `.\executar.ps1` (use `.\executar.ps1 -Amostra 0` para a base inteira)
