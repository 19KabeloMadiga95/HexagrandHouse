from datetime import datetime

from src.lottery.models.powerball_prediction_model import export_powerball_predictions
from src.lottery.models.lotto_prediction_model import export_lotto_predictions
from src.lottery.models.daily_lotto_prediction_model import export_daily_lotto_predictions
from src.lottery.models.uk49s_prediction_model import export_uk49s_predictions


# =========================================================
# EXPORT ALL LOTTERY PREDICTIONS
# =========================================================

def export_all_predictions():
    print("\n======================================")
    print("HEXAGRANDHOUSE LOTTERY PREDICTIONS")
    print("======================================")
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("======================================\n")

    results = []

    steps = [
        ("PowerBall", export_powerball_predictions),
        ("Lotto", export_lotto_predictions),
        ("Daily Lotto", export_daily_lotto_predictions),
        ("UK49s", export_uk49s_predictions),
    ]

    for name, runner in steps:
        print("\n--------------------------------------")
        print(f"GENERATING: {name}")
        print("--------------------------------------")

        try:
            predictions = runner()

            results.append({
                "Model": name,
                "Rows": len(predictions),
                "Status": "Success",
                "Error": "",
            })

        except Exception as e:
            print(f"❌ {name} failed: {e}")

            results.append({
                "Model": name,
                "Rows": 0,
                "Status": "Failed",
                "Error": str(e),
            })

    print("\n======================================")
    print("PREDICTION EXPORT COMPLETE")
    print("======================================")

    total_rows = 0

    for result in results:
        total_rows += result["Rows"]

        print(
            f"{result['Model']:<15} | "
            f"Rows: {result['Rows']:<6} | "
            f"Status: {result['Status']}"
        )

        if result["Error"]:
            print(f"  Error: {result['Error']}")

    print("--------------------------------------")
    print(f"{'TOTAL':<15} | Rows: {total_rows:<6}")
    print("======================================\n")

    return results


# =========================================================
# CLI
# =========================================================

def main():
    export_all_predictions()


if __name__ == "__main__":
    main()