import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
QUARENTENA_DIR = DATA_DIR / "quarentena"
PARQUET_DIR = DATA_DIR / "parquet" / "filmes"
SAIDAS_DIR = BASE_DIR / "saidas"
HADOOP_HOME = BASE_DIR / "tools" / "hadoop"

KAGGLE_DATASET = "asaniczka/tmdb-movies-dataset-2023-930k-movies"
CSV_NAME = "TMDB_movie_dataset_v11.csv"

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "tmdb")
MONGO_SPARK_PACKAGE = "org.mongodb.spark:mongo-spark-connector_2.12:10.4.0"

SAMPLE_ROWS = int(os.getenv("SAMPLE_ROWS", "1000"))
SPARK_DRIVER_MEMORY = os.getenv("SPARK_DRIVER_MEMORY", "6g")
