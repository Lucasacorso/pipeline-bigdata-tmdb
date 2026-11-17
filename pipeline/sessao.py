import os
import sys

from pyspark.sql import SparkSession

from . import config

LOG4J = config.BASE_DIR / "conf" / "log4j2.properties"


def criar_sessao():
    if os.name == "nt" and config.HADOOP_HOME.exists():
        os.environ["HADOOP_HOME"] = str(config.HADOOP_HOME)
        os.environ["PATH"] = str(config.HADOOP_HOME / "bin") + os.pathsep + os.environ.get("PATH", "")
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    spark = (
        SparkSession.builder.appName("pipeline-tmdb")
        .master("local[*]")
        .config("spark.driver.memory", config.SPARK_DRIVER_MEMORY)
        .config("spark.driver.extraJavaOptions", f"-Dlog4j.configurationFile={LOG4J.as_uri()} -Duser.timezone=UTC")
        .config("spark.jars.packages", config.MONGO_SPARK_PACKAGE)
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.shuffle.partitions", "16")
        .config("spark.sql.legacy.timeParserPolicy", "CORRECTED")
        .config("spark.ui.showConsoleProgress", "true")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    return spark
