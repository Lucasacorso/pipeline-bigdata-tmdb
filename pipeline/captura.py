import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

from . import config

log = logging.getLogger("captura")


def _via_kaggle_api():
    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(config.KAGGLE_DATASET, path=str(config.RAW_DIR), unzip=True, quiet=False)


def _via_kagglehub():
    import kagglehub

    origem = Path(kagglehub.dataset_download(config.KAGGLE_DATASET))
    shutil.copy2(origem / config.CSV_NAME, config.RAW_DIR / config.CSV_NAME)


def capturar(forcar=False):
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    destino = config.RAW_DIR / config.CSV_NAME
    if destino.exists() and not forcar:
        log.info("CSV já presente em %s, download ignorado", destino)
    else:
        try:
            log.info("Baixando %s via Kaggle API", config.KAGGLE_DATASET)
            _via_kaggle_api()
        except Exception as erro:
            log.warning("Kaggle API indisponível (%s); usando kagglehub", erro)
            _via_kagglehub()
    if not destino.exists():
        raise FileNotFoundError(f"Arquivo {destino} não encontrado após a captura")
    manifesto = {
        "dataset": config.KAGGLE_DATASET,
        "arquivo": str(destino),
        "tamanho_mb": round(destino.stat().st_size / 1024**2, 1),
        "capturado_em": datetime.now(timezone.utc).isoformat(),
    }
    (config.RAW_DIR / "manifesto_captura.json").write_text(json.dumps(manifesto, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Captura concluída: %s MB", manifesto["tamanho_mb"])
    return manifesto
