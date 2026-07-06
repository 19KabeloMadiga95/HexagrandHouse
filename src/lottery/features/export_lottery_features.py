from __future__ import annotations

from datetime import datetime

from src.lottery.features.base_lottery_features import export_base_features
from src.lottery.features.powerball_features import export_powerball_features
from src.lottery.features.lotto_features import export_lotto_features
from src.lottery.features.daily_lotto_features import export_daily_lotto_features
from src.lottery.features.uk49s_features import export_uk49s_features


# =========================================================
# EXPORT ALL LOTTERY FEATURES TO SQLITE
# =========================================================


def export_all_lottery_features() -> list[dict]:
    print("\n======================================")
    print("HEXAGRANDHOUSE LOTTERY FEATURE BUILD")
    print("SQLite-first runtime mode")
    print("======================================")
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("======================================\n")

    results: list[dict] = []

    steps = [
        ("Base Features", export_base_features),
        ("PowerBall Features", export_powerball_features),
        ("Lotto Features", export_lotto_features),
        ("Daily Lotto Features", export_daily_lotto_features),
        ("UK49s Features", export_uk49s_features),
    ]

    for name, runner in steps:
        print("\n--------------------------------------")
        print(f"BUILDING: {name}")
        print("--------------------------------------")

        try:
            features = runner()
            results.append(
                {
                    "FeatureSet": name,
                    "Rows": len(features),
                    "Status": "Success",
                    "Error": "",
                }
            )
        except Exception as exc:
            print(f"FAILED: {name}: {exc}")
            results.append(
                {
                    "FeatureSet": name,
                    "Rows": 0,
                    "Status": "Failed",
                    "Error": str(exc),
                }
            )

    print("\n======================================")
    print("LOTTERY FEATURE BUILD COMPLETE")
    print("======================================")

    total_rows = 0

    for result in results:
        total_rows += int(result["Rows"])
        print(
            f"{result['FeatureSet']:<22} | "
            f"Rows: {result['Rows']:<6} | "
            f"Status: {result['Status']}"
        )

        if result["Error"]:
            print(f"  Error: {result['Error']}")

    print("--------------------------------------")
    print(f"{'TOTAL':<22} | Rows: {total_rows:<6}")
    print("======================================\n")

    return results


def main() -> None:
    export_all_lottery_features()


if __name__ == "__main__":
    main()
