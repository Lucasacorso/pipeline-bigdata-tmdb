import argparse
import csv
import json
import sys
from itertools import islice

from bson import json_util
from pymongo import MongoClient

from pipeline import config

csv.field_size_limit(2**31 - 1)


def secao(texto):
    print("\n" + "=" * 90 + f"\n{texto}\n" + "=" * 90)


def linhas_brutas(caminho, quantidade):
    with open(caminho, encoding="utf-8") as arquivo:
        return [linha.rstrip("\n") for linha in islice(arquivo, quantidade + 1)]


def registro_cru(caminho, filme_id):
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            if linha["id"] == str(filme_id):
                return linha
    return None


def main():
    parser = argparse.ArgumentParser(description="Compara o registro cru do CSV com o documento estruturado no MongoDB")
    parser.add_argument("--id", type=int, default=157336)
    parser.add_argument("--linhas", type=int, default=3)
    args = parser.parse_args()
    caminho = config.RAW_DIR / config.CSV_NAME

    secao(f"1) DADO CRU — primeiras {args.linhas} linhas de {caminho.name} ({caminho.stat().st_size / 1024**2:.0f} MB)")
    for linha in linhas_brutas(caminho, args.linhas):
        print(linha[:400] + (" ..." if len(linha) > 400 else ""))

    secao(f"2) DADO CRU — registro id={args.id} como texto (tudo string, listas em texto, zeros = desconhecido)")
    cru = registro_cru(caminho, args.id)
    if cru is None:
        sys.exit(f"id {args.id} não encontrado no CSV")
    print(json.dumps(cru, indent=2, ensure_ascii=False))

    secao(f"3) DADO ESTRUTURADO — documento {config.MONGO_DB}.filmes {{_id: {args.id}}}")
    db = MongoClient(config.MONGO_URI)[config.MONGO_DB]
    documento = db.filmes.find_one({"_id": args.id})
    if documento is None:
        sys.exit("documento não encontrado no MongoDB — rode a ingestão primeiro")
    print(json_util.dumps(documento, indent=2, ensure_ascii=False, json_options=json_util.RELAXED_JSON_OPTIONS))

    secao("4) RECOMENDAÇÕES E RANKING ligados ao mesmo _id")
    rec = db.recomendacoes.find_one({"_id": args.id})
    if rec:
        for s in rec["similares"][:5]:
            print(f"  {s['similaridade']:.3f}  {s['titulo']}")
    rank = db.ranking_licenciamento.find_one({"_id": args.id})
    print(f"  Ranking de licenciamento: {'posição ' + str(rank['posicao']) if rank else 'fora do top 20'}")


if __name__ == "__main__":
    main()
