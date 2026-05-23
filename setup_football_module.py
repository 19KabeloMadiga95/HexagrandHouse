from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

folders = [
    "src/football",
    "src/football/data_ingestion",
    "src/football/preprocessing",
    "src/football/features",
    "src/football/models",
    "src/football/predictions",
    "src/football/backtesting",
    "src/football/optimization",
    "src/football/reporting",
    "src/football/automation",
    "src/football/frontend",
    "data/football/raw",
    "data/football/master",
    "data/football/processed/features",
    "data/football/exports/predictions",
    "data/football/exports/backtesting",
    "data/football/exports/reporting",
    "data/football/logs",
]

files = [
    "src/football/__init__.py",
    "src/football/data_ingestion/__init__.py",
    "src/football/preprocessing/__init__.py",
    "src/football/features/__init__.py",
    "src/football/models/__init__.py",
    "src/football/predictions/__init__.py",
    "src/football/backtesting/__init__.py",
    "src/football/optimization/__init__.py",
    "src/football/reporting/__init__.py",
    "src/football/automation/__init__.py",
    "src/football/frontend/__init__.py",
]

for folder in folders:
    path = BASE_DIR / folder
    path.mkdir(parents=True, exist_ok=True)
    print(f"Created folder: {path}")

for file in files:
    path = BASE_DIR / file
    path.touch(exist_ok=True)
    print(f"Created file: {path}")

print("\nFootball module foundation created successfully.")
