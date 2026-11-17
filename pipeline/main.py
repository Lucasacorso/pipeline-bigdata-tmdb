import argparse
import json
import logging
import time
from datetime import datetime, timezone

from . import config
from .armazenamento import gravar_parquet, ler_parquet, resumo_particoes
from .captura import capturar
from .ingestao import ingerir
from .sessao import criar_sessao
from .transformacao import transformar
from .validacao import validar

ETAPAS = ["captura", "processamento", "ingestao"]

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)-14s | %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("pipeline")


def cronometrar(relatorio, nome, funcao, *args):
    inicio = time.perf_counter()
    log.info("===== Etapa: %s =====", nome)
    resultado = funcao(*args)
    relatorio["tempos_s"][nome] = round(time.perf_counter() - inicio, 1)
    return resultado


def processar(spark, relatorio):
    validos, estatisticas = validar(spark)
    relatorio["validacao"] = estatisticas
    tratado, estat_transf = transformar(validos)
    relatorio["transformacao"] = estat_transf
    gravar_parquet(tratado)
    relatorio["parquet"] = resumo_particoes(ler_parquet(spark))


def executar(etapas, forcar_download=False):
    relatorio = {"inicio": datetime.now(timezone.utc).isoformat(), "etapas": etapas, "tempos_s": {}}
    if "captura" in etapas:
        relatorio["captura"] = cronometrar(relatorio, "captura", capturar, forcar_download)
    spark = None
    if "processamento" in etapas or "ingestao" in etapas:
        spark = criar_sessao()
    try:
        if "processamento" in etapas:
            cronometrar(relatorio, "processamento", processar, spark, relatorio)
        if "ingestao" in etapas:
            relatorio["mongodb"] = cronometrar(relatorio, "ingestao", lambda: ingerir(ler_parquet(spark)))
    finally:
        if spark is not None:
            spark.stop()
    relatorio["fim"] = datetime.now(timezone.utc).isoformat()
    config.SAIDAS_DIR.mkdir(parents=True, exist_ok=True)
    caminho = config.SAIDAS_DIR / "relatorio_execucao.json"
    caminho.write_text(json.dumps(relatorio, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    log.info("Relatório final:\n%s", json.dumps(relatorio, indent=2, ensure_ascii=False, default=str))
    return relatorio


def main():
    parser = argparse.ArgumentParser(description="Pipeline Big Data TMDB -> MongoDB")
    parser.add_argument("--etapas", default=",".join(ETAPAS), help="captura,processamento,ingestao")
    parser.add_argument("--forcar-download", action="store_true")
    args = parser.parse_args()
    etapas = [e.strip() for e in args.etapas.split(",") if e.strip()]
    invalidas = set(etapas) - set(ETAPAS)
    if invalidas:
        parser.error(f"Etapas inválidas: {invalidas}")
    executar(etapas, args.forcar_download)


if __name__ == "__main__":
    main()
