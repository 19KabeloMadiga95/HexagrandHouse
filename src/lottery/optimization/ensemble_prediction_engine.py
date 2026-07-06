from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.data.sqlite_store import create_indexes, read_sqlite_table, replace_sqlite_table
from src.lottery.models.export_all_predictions import export_all_predictions


ENSEMBLE_TABLE = "lottery_ensemble_predictions"
COMBINED_TABLE = "lottery_predictions"


# =========================================================
# SQLITE-FIRST ENSEMBLE EXPORT
# =========================================================


def _load_predictions() -> pd.DataFrame:
    df = read_sqlite_table(COMBINED_TABLE)

    if df.empty:
        print("lottery_predictions is empty. Generating base predictions first...")
        df = export_all_predictions()

    return df.copy()


def _confidence_label(score) -> str:
    try:
        value = float(score)
    except Exception:
        return "Unrated"

    if value >= 90:
        return "Elite"
    if value >= 80:
        return "High"
    if value >= 65:
        return "Medium"
    return "Low"


def build_ensemble_predictions() -> pd.DataFrame:
    df = _load_predictions()

    if df.empty:
        return df

    df = df.copy()

    if "GeneratedAt" in df.columns:
        df["GeneratedAt"] = pd.to_datetime(df["GeneratedAt"], errors="coerce")

    if "ConfidenceScore" not in df.columns:
        df["ConfidenceScore"] = 0

    df["ConfidenceScore"] = pd.to_numeric(df["ConfidenceScore"], errors="coerce").fillna(0)
    df["EnsembleConfidenceScore"] = df["ConfidenceScore"].round(1)
    df["ConfidenceLabel"] = df["EnsembleConfidenceScore"].apply(_confidence_label)
    df["ModelName"] = "SQLite Ensemble"
    df["ModelVersion"] = "SQLiteRuntime_v1"
    df["EnsembleGeneratedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sort_cols = [col for col in ["GameFamily", "GameName", "PredictionRank"] if col in df.columns]
    if sort_cols:
        df = df.sort_values(sort_cols).reset_index(drop=True)

    return df


def export_ensemble_predictions() -> pd.DataFrame:
    print("\n======================================")
    print("SQLITE LOTTERY ENSEMBLE ENGINE")
    print("======================================")

    final_df = build_ensemble_predictions()

    rows = replace_sqlite_table(ENSEMBLE_TABLE, final_df)
    create_indexes(ENSEMBLE_TABLE, ["GameFamily", "GameName", "GeneratedAt", "PredictionRank"])

    # Keep the main runtime table aligned with the ensemble result.
    replace_sqlite_table(COMBINED_TABLE, final_df)
    create_indexes(COMBINED_TABLE, ["GameFamily", "GameName", "GeneratedAt", "PredictionRank"])

    print("\nLottery ensemble predictions saved to SQLite.")
    print(f"Table: {ENSEMBLE_TABLE}")
    print(f"Rows : {rows}")
    print("Runtime table refreshed: lottery_predictions")
    print("======================================\n")

    return final_df


def export_all_game_ensembles() -> pd.DataFrame:
    return export_ensemble_predictions()


def main():
    export_ensemble_predictions()


if __name__ == "__main__":
    main()
