from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import traceback
from typing import Any, Callable

import pandas as pd

from src.data.sqlite_store import append_sqlite_table, create_indexes, replace_sqlite_table
from src.football.ingestion.sqlite_football_ingestion import update_football_fixtures_sqlite
from src.football.features.export_football_features import export_football_features
from src.football.models.export_football_models import export_football_models
from src.football.predictions.sqlite_fixture_predictions import export_fixture_predictions
from src.football.reporting.export_football_reporting import export_football_reporting


# =========================================================
# SQLITE-FIRST DAILY FOOTBALL CYCLE
# =========================================================

RUN_LOG_TABLE = "platform_run_log"
REFRESH_STATUS_TABLE = "platform_refresh_status"
PIPELINE_NAME = "SQLite Football Daily Cycle"


@dataclass
class CycleStep:
    name: str
    function: Callable[[], Any]
    required: bool = True


def current_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _safe_row_count(result: Any) -> int | None:
    try:
        if isinstance(result, pd.DataFrame):
            return int(len(result))

        if isinstance(result, list):
            if all(isinstance(item, dict) for item in result):
                total = 0
                found = False
                for item in result:
                    for key in ["Rows", "RowCount", "RowsProcessed"]:
                        if key in item and item.get(key) is not None:
                            total += int(item.get(key) or 0)
                            found = True
                            break
                return total if found else len(result)
            return len(result)

        if isinstance(result, tuple):
            counts = [_safe_row_count(item) for item in result]
            counts = [count for count in counts if count is not None]
            return sum(counts) if counts else None

        if isinstance(result, dict):
            for key in ["Rows", "RowCount", "RowsProcessed"]:
                if key in result and result[key] is not None:
                    return int(result[key])

            total = 0
            found = False
            for value in result.values():
                count = _safe_row_count(value)
                if count is not None:
                    total += int(count)
                    found = True
            return total if found else None

    except Exception:
        return None

    return None


def _run_step(step: CycleStep, run_id: str) -> dict[str, Any]:
    print("\n======================================")
    print(f"RUNNING: {step.name}")
    print("======================================")

    started_at = datetime.now()

    try:
        result = step.function()
        finished_at = datetime.now()
        duration = round((finished_at - started_at).total_seconds(), 2)
        row_count = _safe_row_count(result)

        log_row = {
            "RunID": run_id,
            "PipelineName": PIPELINE_NAME,
            "StepName": step.name,
            "Status": "Success",
            "StartedAt": started_at.strftime("%Y-%m-%d %H:%M:%S"),
            "FinishedAt": finished_at.strftime("%Y-%m-%d %H:%M:%S"),
            "DurationSeconds": duration,
            "RowsProcessed": row_count,
            "ErrorMessage": "",
        }

        print(f"\nSUCCESS: {step.name}")
        print(f"Duration: {duration} sec")
        if row_count is not None:
            print(f"Rows: {row_count}")

        return log_row

    except Exception as exc:
        finished_at = datetime.now()
        duration = round((finished_at - started_at).total_seconds(), 2)
        error_message = str(exc)
        traceback_text = traceback.format_exc()

        log_row = {
            "RunID": run_id,
            "PipelineName": PIPELINE_NAME,
            "StepName": step.name,
            "Status": "Failed",
            "StartedAt": started_at.strftime("%Y-%m-%d %H:%M:%S"),
            "FinishedAt": finished_at.strftime("%Y-%m-%d %H:%M:%S"),
            "DurationSeconds": duration,
            "RowsProcessed": None,
            "ErrorMessage": error_message,
        }

        print(f"\nFAILED: {step.name}")
        print(f"Duration: {duration} sec")
        print(f"Error: {error_message}")
        print("\nTRACEBACK:")
        print(traceback_text)

        if step.required:
            raise

        return log_row


def _write_run_logs(logs: list[dict[str, Any]]) -> int:
    log_df = pd.DataFrame(logs)
    rows = append_sqlite_table(RUN_LOG_TABLE, log_df)
    create_indexes(RUN_LOG_TABLE, ["RunID", "PipelineName", "StepName", "Status", "StartedAt"])
    return rows


def _write_refresh_status(
    run_id: str,
    logs: list[dict[str, Any]],
    started_at: datetime,
    finished_at: datetime,
) -> pd.DataFrame:
    success_count = sum(1 for row in logs if row["Status"] == "Success")
    failure_count = sum(1 for row in logs if row["Status"] == "Failed")
    total_duration = round((finished_at - started_at).total_seconds(), 2)

    status_df = pd.DataFrame(
        [
            {
                "RunID": run_id,
                "PipelineName": PIPELINE_NAME,
                "Status": "Success" if failure_count == 0 else "Failed",
                "StartedAt": started_at.strftime("%Y-%m-%d %H:%M:%S"),
                "FinishedAt": finished_at.strftime("%Y-%m-%d %H:%M:%S"),
                "DurationSeconds": total_duration,
                "SuccessCount": success_count,
                "FailureCount": failure_count,
                "UpdatedAt": current_timestamp(),
            }
        ]
    )

    replace_sqlite_table(REFRESH_STATUS_TABLE, status_df)
    create_indexes(REFRESH_STATUS_TABLE, ["RunID", "PipelineName", "Status", "UpdatedAt"])
    return status_df


def build_cycle_steps() -> list[CycleStep]:
    return [
        CycleStep(
            name="Update Football Fixtures from Web",
            function=update_football_fixtures_sqlite,
            required=False,
        ),
        CycleStep(
            name="Build Football Feature Tables",
            function=export_football_features,
            required=True,
        ),
        CycleStep(
            name="Generate Football Historical Model Tables",
            function=export_football_models,
            required=True,
        ),
        CycleStep(
            name="Generate Football Fixture Picks",
            function=export_fixture_predictions,
            required=False,
        ),
        CycleStep(
            name="Build Football Reporting Tables",
            function=export_football_reporting,
            required=False,
        ),
    ]


def run_daily_football_cycle() -> dict[str, Any]:
    cycle_start = datetime.now()
    run_id = cycle_start.strftime("%Y%m%d_%H%M%S")

    print("\n======================================")
    print("HEXAGRANDHOUSE FOOTBALL DAILY CYCLE")
    print("SQLite-first runtime mode")
    print("======================================")
    print(f"Run ID : {run_id}")
    print(f"Started: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print("======================================\n")

    logs: list[dict[str, Any]] = []

    for step in build_cycle_steps():
        try:
            logs.append(_run_step(step, run_id=run_id))
        except Exception:
            failed_log = logs[-1] if logs else None
            if failed_log is None or failed_log.get("StepName") != step.name:
                logs.append(
                    {
                        "RunID": run_id,
                        "PipelineName": PIPELINE_NAME,
                        "StepName": step.name,
                        "Status": "Failed",
                        "StartedAt": current_timestamp(),
                        "FinishedAt": current_timestamp(),
                        "DurationSeconds": 0,
                        "RowsProcessed": None,
                        "ErrorMessage": "Step failed before log row could be captured.",
                    }
                )
            break

    cycle_end = datetime.now()
    _write_run_logs(logs)
    status_df = _write_refresh_status(run_id, logs, cycle_start, cycle_end)

    success_count = int(status_df.iloc[0]["SuccessCount"])
    failure_count = int(status_df.iloc[0]["FailureCount"])
    duration = float(status_df.iloc[0]["DurationSeconds"])

    print("\n======================================")
    print("FOOTBALL DAILY CYCLE COMPLETE")
    print("======================================")
    print(f"Run ID  : {run_id}")
    print(f"Finished: {cycle_end.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {duration} sec")
    print(f"Success : {success_count}")
    print(f"Failed  : {failure_count}")
    print(f"Log Tbl : {RUN_LOG_TABLE}")
    print("======================================\n")

    return {
        "RunID": run_id,
        "PipelineName": PIPELINE_NAME,
        "Status": "Success" if failure_count == 0 else "Failed",
        "SuccessCount": success_count,
        "FailureCount": failure_count,
        "DurationSeconds": duration,
        "RunLogTable": RUN_LOG_TABLE,
        "RefreshStatusTable": REFRESH_STATUS_TABLE,
    }


def main() -> dict[str, Any]:
    return run_daily_football_cycle()


if __name__ == "__main__":
    main()
