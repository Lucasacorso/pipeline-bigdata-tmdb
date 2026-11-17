import argparse
import json

import pandas as pd
from pymongo import MongoClient

from analises.pipelines import consultas
from pipeline import config

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 20)
pd.set_option("display.max_colwidth", 120)


def cabecalho(texto):
    print("\n" + "=" * 90 + f"\n{texto}\n" + "=" * 90)


def main():
    parser = argparse.ArgumentParser(description="Responde as perguntas da N2 com aggregation pipelines executados no MongoDB")
    parser.add_argument("perguntas", nargs="*", help="números das perguntas de 1 a 6 (padrão: todas)")
    parser.add_argument("--filme", default="Inception", help="filme usado na pergunta 5")
    parser.add_argument("--mostrar-pipeline", action="store_true", help="imprime o pipeline em JSON, pronto para colar no Compass")
    args = parser.parse_args()

    db = MongoClient(config.MONGO_URI)[config.MONGO_DB]
    for numero, titulo, colecao, pipeline in consultas(db.filmes.estimated_document_count(), args.filme):
        if args.perguntas and numero not in args.perguntas:
            continue
        cabecalho(f"{titulo}\ncoleção: {config.MONGO_DB}.{colecao}")
        if args.mostrar_pipeline:
            print(json.dumps(pipeline, indent=2, ensure_ascii=False))
            print("-" * 90)
        resultado = list(db[colecao].aggregate(pipeline))
        print(pd.DataFrame(resultado).to_string(index=False) if resultado else "(sem resultados)")


if __name__ == "__main__":
    main()
