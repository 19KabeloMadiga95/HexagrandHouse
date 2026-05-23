from datetime import datetime
import traceback

from src.lottery.pipelines.update_all_lottery_history import (
    update_all_lottery_history,
)

from src.lottery.features.export_lottery_features import (
    export_all_lottery_features,
)

from src.lottery.analytics.lottery_quality_checks import (
    run_quality_checks,
)

from src.lottery.models.export_all_predictions import (
    export_all_predictions,
)


# =========================================================
# FULL LOTTERY PIPELINE
# =========================================================

def run_full_lottery_pipeline():
    start_time = datetime.now()

    print("\n==================================================")
    print("HEXAGRANDHOUSE FULL LOTTERY PIPELINE")
    print("==================================================")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("==================================================\n")

    results = []

    steps = [
        (
            "Update Historical Data",
            update_all_lottery_history,
        ),
        (
            "Export Feature Engineering",
            export_all_lottery_features,
        ),
        (
            "Run Quality Checks",
            run_quality_checks,
        ),
        (
            "Generate Predictions",
            export_all_predictions,
        ),
    ]

    for step_name, runner in steps:
        print("\n--------------------------------------------------")
        print(f"RUNNING: {step_name}")
        print("--------------------------------------------------")

        step_start = datetime.now()

        try:
            result = runner()

            duration = round(
                (datetime.now() - step_start).total_seconds(),
                2
            )

            results.append({
                "Step": step_name,
                "Status": "Success",
                "DurationSeconds": duration,
                "Error": "",
            })

            print(f"\n✅ {step_name} completed successfully.")
            print(f"Duration: {duration} seconds")

        except Exception as e:
            duration = round(
                (datetime.now() - step_start).total_seconds(),
                2
            )

            error_message = str(e)

            results.append({
                "Step": step_name,
                "Status": "Failed",
                "DurationSeconds": duration,
                "Error": error_message,
            })

            print(f"\n❌ {step_name} failed.")
            print(f"Duration: {duration} seconds")
            print(f"Error: {error_message}")

            print("\nTRACEBACK:")
            traceback.print_exc()

            print("\nPipeline stopped due to failure.")

            break

    end_time = datetime.now()

    total_duration = round(
        (end_time - start_time).total_seconds(),
        2
    )

    print("\n==================================================")
    print("FULL PIPELINE SUMMARY")
    print("==================================================")

    for result in results:
        print(
            f"{result['Step']:<30} | "
            f"{result['Status']:<10} | "
            f"{result['DurationSeconds']} sec"
        )

        if result["Error"]:
            print(f"  Error: {result['Error']}")

    print("--------------------------------------------------")
    print(f"Total Duration: {total_duration} seconds")
    print(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("==================================================\n")

    return results


# =========================================================
# CLI
# =========================================================

def main():
    run_full_lottery_pipeline()


if __name__ == "__main__":
    main()