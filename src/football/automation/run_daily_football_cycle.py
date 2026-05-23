import importlib
import traceback
from datetime import datetime
from pathlib import Path
from time import perf_counter

import pandas as pd


# =========================================================
# IMPORT FOOTBALL PIPELINE - DAILY CORE
# =========================================================

from src.football.data_ingestion.build_football_fixtures import (
    export_fixtures,
)

from src.football.predictions.predict_fixtures import (
    export_fixture_predictions,
)

from src.football.backtesting.archive_daily_predictions import (
    archive_daily_predictions,
)

from src.football.backtesting.fixture_prediction_backtester import (
    export_fixture_prediction_backtest,
)

from src.football.backtesting.cleanup_past_fixtures import (
    cleanup_past_fixtures,
)

from src.football.reporting.football_model_performance_dashboard import (
    export_football_model_performance_dashboard,
)

from src.football.reporting.top_plays_report import (
    export_top_plays_report,
)

from src.football.value.value_bet_engine import (
    export_value_bets,
)


# =========================================================
# OPTIONAL HEAVY TASK SETTINGS
# =========================================================

ENABLE_FULL_MASTER_REFRESH = True
ENABLE_FULL_FEATURE_REFRESH = True
ENABLE_FULL_MODEL_REFRESH = True


# =========================================================
# SAFE OPTIONAL IMPORT HELPER
# =========================================================

def optional_import(module_path, possible_function_names):
    try:
        module = importlib.import_module(module_path)

        for function_name in possible_function_names:
            if hasattr(module, function_name):
                return getattr(module, function_name)

        print("\nWARNING:")
        print(f"No matching function found in {module_path}")
        print(f"Tried: {possible_function_names}")
        return None

    except Exception as e:
        print("\nWARNING:")
        print(f"Could not import optional module: {module_path}")
        print(f"Error: {e}")
        return None


build_football_master_dataset = optional_import(
    "src.football.data_ingestion.build_UKDATA27_football_master_dataset",
    [
        "build_football_master_dataset",
        "export_football_master_dataset",
        "build_UKDATA27_football_master_dataset",
        "export_master_dataset",
        "main",
    ],
)

build_football_features = optional_import(
    "src.football.features.build_football_features",
    [
        "build_football_features",
        "export_football_features",
        "main",
    ],
)

export_goals_model = optional_import(
    "src.football.models.goals_model",
    [
        "export_goals_model",
        "main",
    ],
)

export_result_model = optional_import(
    "src.football.models.result_model",
    [
        "export_result_model",
        "main",
    ],
)

export_corners_model = optional_import(
    "src.football.models.corners_model",
    [
        "export_corners_model",
        "main",
    ],
)

export_ensemble_predictions = optional_import(
    "src.football.models.ensemble_engine",
    [
        "export_ensemble_predictions",
        "main",
    ],
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

LOG_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "logs"
)

LOG_FILE = (
    LOG_DIR
    / "daily_football_cycle_log.xlsx"
)


# =========================================================
# HELPERS
# =========================================================

def ensure_directories():
    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def append_log(rows):
    log_df = pd.DataFrame(rows)

    if LOG_FILE.exists():
        try:
            existing_df = pd.read_excel(
                LOG_FILE,
                sheet_name="Football_Cycle_Log",
                engine="openpyxl"
            )

            log_df = pd.concat(
                [
                    existing_df,
                    log_df,
                ],
                ignore_index=True
            )

        except Exception:
            pass

    with pd.ExcelWriter(
        LOG_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:
        log_df.to_excel(
            writer,
            sheet_name="Football_Cycle_Log",
            index=False
        )


def execute_step(
    step_name,
    function_reference,
    log_rows
):
    print("\n================================================")
    print(f"RUNNING: {step_name}")
    print("================================================")

    start_time = perf_counter()

    status = "Success"
    error_message = ""

    try:
        if function_reference is None:
            status = "Skipped"
            error_message = "Function reference not available."
            print(error_message)

        else:
            function_reference()

    except Exception as e:
        status = "Failed"
        error_message = str(e)

        print("\nERROR:")
        print(error_message)

        traceback.print_exc()

    duration = round(
        perf_counter() - start_time,
        2
    )

    log_rows.append(
        {
            "RunTimestamp": datetime.now(),
            "StepName": step_name,
            "Status": status,
            "DurationSeconds": duration,
            "ErrorMessage": error_message,
        }
    )

    print(f"\nSTATUS   : {status}")
    print(f"DURATION : {duration} seconds")

    return status == "Success"


def add_step(
    pipeline_steps,
    step_name,
    function_reference,
    enabled=True
):
    if enabled:
        pipeline_steps.append(
            (
                step_name,
                function_reference,
            )
        )


# =========================================================
# MAIN DAILY FOOTBALL PIPELINE
# =========================================================

def run_daily_football_cycle():
    ensure_directories()

    print("\n================================================")
    print("DAILY FOOTBALL PIPELINE")
    print("================================================")

    log_rows = []
    pipeline_steps = []

    # =====================================================
    # 1. SCORE HISTORICAL PREDICTIONS FIRST
    # =====================================================

    add_step(
        pipeline_steps,
        "Backtest Previous Fixture Predictions",
        export_fixture_prediction_backtest,
        enabled=True
    )

    # =====================================================
    # 2. CLEANUP EXPIRED FIXTURES
    # =====================================================

    add_step(
        pipeline_steps,
        "Cleanup Past Fixtures",
        cleanup_past_fixtures,
        enabled=True
    )

    # =====================================================
    # 3. OPTIONAL HEAVY REFRESHES
    # =====================================================

    add_step(
        pipeline_steps,
        "Build Football Master Dataset",
        build_football_master_dataset,
        enabled=ENABLE_FULL_MASTER_REFRESH
    )

    add_step(
        pipeline_steps,
        "Build Football Features",
        build_football_features,
        enabled=ENABLE_FULL_FEATURE_REFRESH
    )

    add_step(
        pipeline_steps,
        "Goals Model",
        export_goals_model,
        enabled=ENABLE_FULL_MODEL_REFRESH
    )

    add_step(
        pipeline_steps,
        "Result Model",
        export_result_model,
        enabled=ENABLE_FULL_MODEL_REFRESH
    )

    add_step(
        pipeline_steps,
        "Corners Model",
        export_corners_model,
        enabled=ENABLE_FULL_MODEL_REFRESH
    )

    add_step(
        pipeline_steps,
        "Historical Ensemble Engine",
        export_ensemble_predictions,
        enabled=ENABLE_FULL_MODEL_REFRESH
    )

    # =====================================================
    # 4. BUILD FRESH FIXTURES
    # =====================================================

    add_step(
        pipeline_steps,
        "Build Football Fixtures",
        export_fixtures,
        enabled=True
    )

    # =====================================================
    # 5. GENERATE PREDICTIONS
    # =====================================================

    add_step(
        pipeline_steps,
        "Predict Football Fixtures",
        export_fixture_predictions,
        enabled=True
    )

    # =====================================================
    # 6. ARCHIVE PREDICTIONS
    # =====================================================

    add_step(
        pipeline_steps,
        "Archive Daily Predictions",
        archive_daily_predictions,
        enabled=True
    )

    # =====================================================
    # 7. VALUE ENGINE
    # =====================================================

    add_step(
        pipeline_steps,
        "Football Value Bet Engine",
        export_value_bets,
        enabled=True
    )

    # =====================================================
    # 8. DASHBOARDS
    # =====================================================

    add_step(
        pipeline_steps,
        "Football Performance Dashboard",
        export_football_model_performance_dashboard,
        enabled=True
    )

    add_step(
        pipeline_steps,
        "Top Plays Report",
        export_top_plays_report,
        enabled=True
    )

    successful_steps = 0
    failed_steps = 0
    skipped_steps = 0

    overall_start = perf_counter()

    for step_name, function_reference in pipeline_steps:

        execute_step(
            step_name=step_name,
            function_reference=function_reference,
            log_rows=log_rows
        )

        latest_status = log_rows[-1]["Status"]

        if latest_status == "Success":
            successful_steps += 1

        elif latest_status == "Skipped":
            skipped_steps += 1

        else:
            failed_steps += 1

    total_duration = round(
        perf_counter() - overall_start,
        2
    )

    append_log(log_rows)

    print("\n================================================")
    print("DAILY FOOTBALL PIPELINE COMPLETE")
    print("================================================")
    print(f"Successful Steps : {successful_steps}")
    print(f"Failed Steps     : {failed_steps}")
    print(f"Skipped Steps    : {skipped_steps}")
    print(f"Total Duration   : {total_duration} seconds")
    print(f"Log File         : {LOG_FILE}")
    print("================================================\n")


# =========================================================
# CLI
# =========================================================

def main():
    run_daily_football_cycle()


if __name__ == "__main__":
    main()