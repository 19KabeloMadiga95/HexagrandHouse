from pathlib import Path
from datetime import datetime, timedelta
import traceback

import pandas as pd


# =========================================================
# IMPORT PIPELINES
# =========================================================

from src.lottery.pipelines.update_all_lottery_history import (
    update_all_lottery_history,
)

from src.lottery.analytics.lottery_quality_checks import (
    run_quality_checks,
)

from src.lottery.features.export_lottery_features import (
    export_all_lottery_features,
)

from src.lottery.models.export_all_predictions import (
    export_all_predictions,
)


# =========================================================
# BACKTESTING
# =========================================================

from src.lottery.backtesting.backtest_powerball_model import (
    export_powerball_backtest,
)

from src.lottery.backtesting.backtest_lotto_model import (
    export_lotto_backtest,
)

from src.lottery.backtesting.backtest_daily_lotto_model import (
    export_daily_lotto_backtest,
)

from src.lottery.backtesting.backtest_uk49s_model import (
    export_uk49s_backtest,
)


# =========================================================
# MODEL COMPARISONS
# =========================================================

from src.lottery.backtesting.powerball_model_comparison import (
    export_model_comparison_backtest,
)

from src.lottery.backtesting.lotto_model_comparison import (
    export_lotto_model_comparison_backtest,
)

from src.lottery.backtesting.daily_lotto_model_comparison import (
    export_daily_lotto_model_comparison_backtest,
)

from src.lottery.backtesting.uk49s_model_comparison import (
    export_uk49s_model_comparison_backtest,
)


# =========================================================
# OPTIMIZATION
# =========================================================

from src.lottery.optimization.powerball_genetic_optimizer import (
    run_powerball_genetic_optimizer,
)

from src.lottery.optimization.lotto_genetic_optimizer import (
    run_lotto_genetic_optimizer,
)

from src.lottery.optimization.daily_lotto_genetic_optimizer import (
    run_daily_lotto_genetic_optimizer,
)

from src.lottery.optimization.uk49s_genetic_optimizer import (
    run_uk49s_genetic_optimizer,
)

##from src.lottery.optimization.adaptive_weight_tuner import (
##    run_adaptive_weight_tuner,
##)


# =========================================================
# ENSEMBLE + SCORING
# =========================================================

from src.lottery.predictions.ensemble_prediction_engine import (
    export_all_game_ensembles,
)

from src.lottery.scoring.model_performance_dashboard import (
    export_model_performance_dashboard,
)

from src.lottery.scoring.unified_model_performance_dashboard import (
    export_unified_model_performance_dashboard,
)


# =========================================================
# REPORTING
# =========================================================

from src.lottery.reporting.executive_lottery_report import (
    export_executive_report,
)

from src.lottery.reporting.daily_lottery_summary_generator import (
    export_daily_summary,
)


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

LOG_DIR = (
    BASE_DIR
    / "data"
    / "logs"
)

LOG_FILE = (
    LOG_DIR
    / "daily_lottery_cycle_log.xlsx"
)


# =========================================================
# CONFIG
# =========================================================

INCREMENTAL_LOOKBACK_DAYS = 3


# =========================================================
# HELPERS
# =========================================================

def current_timestamp():
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def get_incremental_year_window(
    lookback_days=INCREMENTAL_LOOKBACK_DAYS
):
    today = datetime.today().date()

    start_date = today - timedelta(
        days=lookback_days
    )

    return start_date.year, today.year


def run_incremental_history_update():
    start_year, end_year = get_incremental_year_window()

    print("\nIncremental history refresh mode enabled.")
    print(f"Lookback days : {INCREMENTAL_LOOKBACK_DAYS}")
    print(f"Start year    : {start_year}")
    print(f"End year      : {end_year}")

    return update_all_lottery_history(
        start_year=start_year,
        end_year=end_year,
    )


def safe_row_count(result):
    try:
        if isinstance(result, pd.DataFrame):
            return len(result)

        if isinstance(result, tuple):
            for item in result:
                if isinstance(item, pd.DataFrame):
                    return len(item)

        if isinstance(result, dict):
            for value in result.values():
                if isinstance(value, pd.DataFrame):
                    return len(value)

        if isinstance(result, list):
            return len(result)

        return None

    except Exception:
        return None


# =========================================================
# STEP RUNNER
# =========================================================

def run_step(
    step_name,
    function,
    logs,
):
    print("\n======================================")
    print(f"RUNNING: {step_name}")
    print("======================================")

    start_time = datetime.now()

    try:
        result = function()

        end_time = datetime.now()

        duration = round(
            (
                end_time - start_time
            ).total_seconds(),
            2
        )

        row_count = safe_row_count(
            result
        )

        logs.append({
            "RunTimestamp": current_timestamp(),
            "StepName": step_name,
            "Status": "Success",
            "DurationSeconds": duration,
            "RowsProcessed": row_count,
            "ErrorMessage": "",
        })

        print(f"\nSUCCESS: {step_name}")
        print(f"Duration: {duration} sec")

        if row_count is not None:
            print(f"Rows: {row_count}")

        return True

    except Exception as e:
        end_time = datetime.now()

        duration = round(
            (
                end_time - start_time
            ).total_seconds(),
            2
        )

        error_message = str(e)
        traceback_text = traceback.format_exc()

        logs.append({
            "RunTimestamp": current_timestamp(),
            "StepName": step_name,
            "Status": "Failed",
            "DurationSeconds": duration,
            "RowsProcessed": None,
            "ErrorMessage": error_message,
        })

        print(f"\nFAILED: {step_name}")
        print(f"Error: {error_message}")

        print("\nTRACEBACK:")
        print(traceback_text)

        return False


# =========================================================
# LOGGING
# =========================================================

def export_logs(logs):
    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    new_log_df = pd.DataFrame(logs)

    if LOG_FILE.exists():
        try:
            existing = pd.read_excel(
                LOG_FILE,
                engine="openpyxl"
            )

            combined = pd.concat(
                [
                    existing,
                    new_log_df
                ],
                ignore_index=True
            )

        except Exception:
            combined = new_log_df

    else:
        combined = new_log_df

    combined.to_excel(
        LOG_FILE,
        sheet_name="Daily_Cycle_Log",
        index=False
    )

    return combined


# =========================================================
# MAIN AUTOMATION
# =========================================================

def run_daily_lottery_cycle():
    cycle_start = datetime.now()

    print("\n======================================")
    print("HEXAGRANDHOUSE PHASE 1 FULL LOTTERY CYCLE")
    print("======================================")
    print(f"Started: {current_timestamp()}")
    print("Mode   : Incremental refresh + full analytics")
    print("======================================\n")

    logs = []

    # -----------------------------------------------------
    # DATA LAYER
    # -----------------------------------------------------

    run_step(
        step_name="Incremental Historical Lottery Update",
        function=run_incremental_history_update,
        logs=logs,
    )

    run_step(
        step_name="Run Data Quality Checks",
        function=run_quality_checks,
        logs=logs,
    )

    run_step(
        step_name="Export Lottery Features",
        function=export_all_lottery_features,
        logs=logs,
    )

    # -----------------------------------------------------
    # PREDICTION LAYER
    # -----------------------------------------------------

    run_step(
        step_name="Generate Base Predictions",
        function=export_all_predictions,
        logs=logs,
    )

    # -----------------------------------------------------
    # BACKTESTING LAYER
    # -----------------------------------------------------

    run_step(
        step_name="Backtest PowerBall Model",
        function=export_powerball_backtest,
        logs=logs,
    )

    run_step(
        step_name="Backtest Lotto Model",
        function=export_lotto_backtest,
        logs=logs,
    )

    run_step(
        step_name="Backtest Daily Lotto Model",
        function=export_daily_lotto_backtest,
        logs=logs,
    )

    run_step(
        step_name="Backtest UK49s Model",
        function=export_uk49s_backtest,
        logs=logs,
    )

    # -----------------------------------------------------
    # MODEL COMPARISON LAYER
    # -----------------------------------------------------

    run_step(
        step_name="Compare PowerBall Models",
        function=export_model_comparison_backtest,
        logs=logs,
    )

    run_step(
        step_name="Compare Lotto Models",
        function=export_lotto_model_comparison_backtest,
        logs=logs,
    )

    run_step(
        step_name="Compare Daily Lotto Models",
        function=export_daily_lotto_model_comparison_backtest,
        logs=logs,
    )

    run_step(
        step_name="Compare UK49s Models",
        function=export_uk49s_model_comparison_backtest,
        logs=logs,
    )

    # -----------------------------------------------------
    # OPTIMIZATION LAYER
    # -----------------------------------------------------

    run_step(
        step_name="Run PowerBall Genetic Optimizer",
        function=run_powerball_genetic_optimizer,
        logs=logs,
    )

    run_step(
        step_name="Run Lotto Genetic Optimizer",
        function=run_lotto_genetic_optimizer,
        logs=logs,
    )

    run_step(
        step_name="Run Daily Lotto Genetic Optimizer",
        function=run_daily_lotto_genetic_optimizer,
        logs=logs,
    )

    run_step(
        step_name="Run UK49s Genetic Optimizer",
        function=run_uk49s_genetic_optimizer,
        logs=logs,
    )

##    run_step(
##        step_name="Run Adaptive Weight Tuner",
##        function=run_adaptive_weight_tuner,
##        logs=logs,
##    )

    # -----------------------------------------------------
    # SCORING + FINAL ENSEMBLE LAYER
    # -----------------------------------------------------

    run_step(
        step_name="Generate PowerBall Performance Dashboard",
        function=export_model_performance_dashboard,
        logs=logs,
    )

    run_step(
        step_name="Generate Unified Model Performance Dashboard",
        function=export_unified_model_performance_dashboard,
        logs=logs,
    )

    run_step(
        step_name="Generate Final Ensemble Predictions",
        function=export_all_game_ensembles,
        logs=logs,
    )

    # -----------------------------------------------------
    # REPORTING LAYER
    # -----------------------------------------------------

    run_step(
        step_name="Generate Executive Report",
        function=export_executive_report,
        logs=logs,
    )

    run_step(
        step_name="Generate Daily Summary",
        function=export_daily_summary,
        logs=logs,
    )

    # -----------------------------------------------------
    # FINALISE
    # -----------------------------------------------------

    cycle_end = datetime.now()

    total_duration = round(
        (
            cycle_end - cycle_start
        ).total_seconds(),
        2
    )

    success_count = len([
        x for x in logs
        if x["Status"] == "Success"
    ])

    failure_count = len([
        x for x in logs
        if x["Status"] == "Failed"
    ])

    export_logs(logs)

    print("\n======================================")
    print("PHASE 1 FULL LOTTERY CYCLE COMPLETE")
    print("======================================")
    print(f"Started : {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Finished: {cycle_end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {total_duration} sec")
    print(f"Success : {success_count}")
    print(f"Failed  : {failure_count}")
    print(f"Log File: {LOG_FILE}")
    print("======================================\n")

    return {
        "SuccessCount": success_count,
        "FailureCount": failure_count,
        "DurationSeconds": total_duration,
        "LogFile": str(LOG_FILE),
    }


# =========================================================
# CLI
# =========================================================

def main():
    run_daily_lottery_cycle()


if __name__ == "__main__":
    main()