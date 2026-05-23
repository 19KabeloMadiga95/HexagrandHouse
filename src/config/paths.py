from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / 'data'
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'
MASTER_DIR = DATA_DIR / 'master'
EXPORTS_DIR = DATA_DIR / 'exports'
