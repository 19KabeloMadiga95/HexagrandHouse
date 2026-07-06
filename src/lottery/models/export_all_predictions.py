from __future__ import annotations

from datetime import datetime

from src.lottery.models.sqlite_prediction_engine import export_all_prediction_groups


# =========================================================
# EXPORT ALL LOTTERY PREDICTIONS - SQLITE RUNTIME
# =========================================================


def export_all_predictions():
    print("\n======================================")
    print("HEXAGRANDHOUSE LOTTERY PREDICTIONS")
    print("SQLite-first runtime mode")
    print("======================================")
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("======================================\n")

    predictions = export_all_prediction_groups()

    print("\n======================================")
    print("PREDICTION EXPORT COMPLETE")
    print("======================================")
    print(f"Rows: {len(predictions)}")
    print("Table: lottery_predictions")
    print("======================================\n")

    return predictions


def main():
    export_all_predictions()


if __name__ == "__main__":
    main()
