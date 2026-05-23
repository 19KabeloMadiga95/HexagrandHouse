from pathlib import Path
from datetime import datetime

import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

MODELS_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "models"
)

PREDICTIONS_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "predictions"
)

REPORTING_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "reporting"
)

GOALS_MODEL_FILE = (
    MODELS_DIR
    / "football_goals_model_predictions.xlsx"
)

CORNERS_MODEL_FILE = (
    MODELS_DIR
    / "football_corners_model_predictions.xlsx"
)

RESULT_MODEL_FILE = (
    MODELS_DIR
    / "football_result_model_predictions.xlsx"
)

ENSEMBLE_FILE = (
    PREDICTIONS_DIR
    / "football_ensemble_predictions.xlsx"
)

FIXTURE_PREDICTIONS_FILE = (
    PREDICTIONS_DIR
    / "football_fixture_predictions.xlsx"
)

OUTPUT_FILE = (
    REPORTING_DIR
    / "football_model_performance_dashboard.xlsx"
)


# =========================================================
# HELPERS
# =========================================================

def ensure_directories():
    REPORTING_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def safe_read_excel(
    path,
    sheet_name
):
    try:
        if not path.exists():
            print(f"Missing file: {path}")
            return pd.DataFrame()

        return pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine="openpyxl"
        )

    except Exception as e:
        print(f"Could not read: {path}")
        print(f"Sheet: {sheet_name}")
        print(f"Error: {e}")

        return pd.DataFrame()


def file_metadata(path):
    exists = path.exists()

    return {
        "Exists": exists,
        "LastModified": (
            datetime.fromtimestamp(
                path.stat().st_mtime
            ).strftime("%Y-%m-%d %H:%M:%S")
            if exists
            else None
        ),
        "SizeMB": (
            round(
                path.stat().st_size / (1024 * 1024),
                2
            )
            if exists
            else 0
        ),
    }


def get_summary_value(
    summary_df,
    metric_name,
    default=0
):
    if summary_df.empty:
        return default

    if "Metric" not in summary_df.columns or "Value" not in summary_df.columns:
        return default

    match = summary_df[
        summary_df["Metric"].astype(str) == str(metric_name)
    ]

    if match.empty:
        return default

    return match.iloc[0]["Value"]


def get_first_numeric(
    df,
    col,
    default=0
):
    if df.empty or col not in df.columns:
        return default

    value = pd.to_numeric(
        df[col],
        errors="coerce"
    ).dropna()

    if value.empty:
        return default

    return round(
        value.mean(),
        3
    )


def get_rows_scored_from_summary(summary_df):
    if summary_df.empty:
        return 0

    if "RowsScored" in summary_df.columns:
        rows = pd.to_numeric(
            summary_df["RowsScored"],
            errors="coerce"
        ).dropna()

        if not rows.empty:
            return int(rows.max())

    return 0


# =========================================================
# DASHBOARD SUMMARY
# =========================================================

def build_dashboard_summary(
    goals_summary,
    corners_summary,
    result_summary,
    ensemble_summary,
    fixture_summary
):
    rows = []

    if not goals_summary.empty:
        for _, row in goals_summary.iterrows():
            rows.append({
                "Section": "Historical Model",
                "ModelArea": "Goals",
                "Metric": row.get("Model", ""),
                "RowsScored": row.get("RowsScored", None),
                "AverageProbability": row.get("AverageProbability", None),
                "ActualHitRate": row.get("ActualHitRate", None),
                "PredictionAccuracy": row.get("PredictionAccuracy", None),
            })

    if not corners_summary.empty:
        for _, row in corners_summary.iterrows():
            rows.append({
                "Section": "Historical Model",
                "ModelArea": "Corners",
                "Metric": row.get("Model", ""),
                "RowsScored": row.get("RowsScored", None),
                "AverageProbability": row.get("AverageProbability", None),
                "ActualHitRate": row.get("ActualHitRate", None),
                "PredictionAccuracy": row.get("PredictionAccuracy", None),
            })

    if not result_summary.empty:
        for _, row in result_summary.iterrows():
            rows.append({
                "Section": "Historical Model",
                "ModelArea": "Result",
                "Metric": row.get("Model", "Three-Way Result Model"),
                "RowsScored": row.get("RowsScored", None),
                "AverageProbability": row.get("AverageHomeWinProbability", None),
                "ActualHitRate": None,
                "PredictionAccuracy": row.get("PredictionAccuracy", None),
            })

    if not ensemble_summary.empty:
        for _, row in ensemble_summary.iterrows():
            rows.append({
                "Section": "Historical Ensemble",
                "ModelArea": "Ensemble",
                "Metric": row.get("Metric", None),
                "RowsScored": row.get("Value", None),
                "AverageProbability": None,
                "ActualHitRate": None,
                "PredictionAccuracy": None,
            })

    if not fixture_summary.empty:
        for _, row in fixture_summary.iterrows():
            rows.append({
                "Section": "Future Fixtures",
                "ModelArea": "Fixture Prediction",
                "Metric": row.get("Metric", None),
                "RowsScored": row.get("Value", None),
                "AverageProbability": None,
                "ActualHitRate": None,
                "PredictionAccuracy": None,
            })

    return pd.DataFrame(rows)


def build_high_level_kpis(
    goals_summary,
    corners_summary,
    result_summary,
    ensemble_summary,
    fixture_summary
):
    rows = [
        {
            "KPI": "Goals Prediction Rows",
            "Value": get_rows_scored_from_summary(
                goals_summary
            ),
        },
        {
            "KPI": "Corners Prediction Rows",
            "Value": get_rows_scored_from_summary(
                corners_summary
            ),
        },
        {
            "KPI": "Result Prediction Rows",
            "Value": get_rows_scored_from_summary(
                result_summary
            ),
        },
        {
            "KPI": "Historical Ensemble Rows",
            "Value": get_summary_value(
                ensemble_summary,
                "Rows",
                0
            ),
        },
        {
            "KPI": "Future Fixture Prediction Rows",
            "Value": get_summary_value(
                fixture_summary,
                "Fixtures Predicted",
                0
            ),
        },
        {
            "KPI": "Historical Elite Predictions",
            "Value": get_summary_value(
                ensemble_summary,
                "Elite Predictions",
                0
            ),
        },
        {
            "KPI": "Future Elite Predictions",
            "Value": get_summary_value(
                fixture_summary,
                "Elite Predictions",
                0
            ),
        },
        {
            "KPI": "Average Historical Ensemble Confidence",
            "Value": get_summary_value(
                ensemble_summary,
                "Average Ensemble Confidence",
                0
            ),
        },
        {
            "KPI": "Average Future Fixture Confidence",
            "Value": get_summary_value(
                fixture_summary,
                "Average Ensemble Confidence",
                0
            ),
        },
        {
            "KPI": "Generated At",
            "Value": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        },
    ]

    return pd.DataFrame(rows)


def build_model_file_status():
    files = [
        {
            "FileType": "Goals Model",
            "Path": GOALS_MODEL_FILE,
        },
        {
            "FileType": "Corners Model",
            "Path": CORNERS_MODEL_FILE,
        },
        {
            "FileType": "Result Model",
            "Path": RESULT_MODEL_FILE,
        },
        {
            "FileType": "Historical Ensemble",
            "Path": ENSEMBLE_FILE,
        },
        {
            "FileType": "Fixture Predictions",
            "Path": FIXTURE_PREDICTIONS_FILE,
        },
    ]

    rows = []

    for item in files:
        metadata = file_metadata(
            item["Path"]
        )

        rows.append({
            "FileType": item["FileType"],
            "Exists": metadata["Exists"],
            "Path": str(item["Path"]),
            "LastModified": metadata["LastModified"],
            "SizeMB": metadata["SizeMB"],
        })

    return pd.DataFrame(rows)


def combine_league_summaries(
    goals_league,
    corners_league,
    result_league,
    ensemble_league,
    fixture_league
):
    frames = []

    if not goals_league.empty:
        df = goals_league.copy()
        df["ModelArea"] = "Goals"
        frames.append(df)

    if not corners_league.empty:
        df = corners_league.copy()
        df["ModelArea"] = "Corners"
        frames.append(df)

    if not result_league.empty:
        df = result_league.copy()
        df["ModelArea"] = "Result"
        frames.append(df)

    if not ensemble_league.empty:
        df = ensemble_league.copy()
        df["ModelArea"] = "Historical Ensemble"
        frames.append(df)

    if not fixture_league.empty:
        df = fixture_league.copy()
        df["ModelArea"] = "Fixture Predictions"
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(
        frames,
        ignore_index=True,
        sort=False
    )


# =========================================================
# EXPORT
# =========================================================

def export_football_model_performance_dashboard():
    ensure_directories()

    print("Reading lightweight summary sheets only...")

    goals_summary = safe_read_excel(
        GOALS_MODEL_FILE,
        "Summary"
    )

    goals_league = safe_read_excel(
        GOALS_MODEL_FILE,
        "League_Summary"
    )

    corners_summary = safe_read_excel(
        CORNERS_MODEL_FILE,
        "Summary"
    )

    corners_league = safe_read_excel(
        CORNERS_MODEL_FILE,
        "League_Summary"
    )

    result_summary = safe_read_excel(
        RESULT_MODEL_FILE,
        "Summary"
    )

    result_league = safe_read_excel(
        RESULT_MODEL_FILE,
        "League_Summary"
    )

    ensemble_summary = safe_read_excel(
        ENSEMBLE_FILE,
        "Summary"
    )

    ensemble_league = safe_read_excel(
        ENSEMBLE_FILE,
        "League_Summary"
    )

    fixture_summary = safe_read_excel(
        FIXTURE_PREDICTIONS_FILE,
        "Summary"
    )

    fixture_league = safe_read_excel(
        FIXTURE_PREDICTIONS_FILE,
        "League_Summary"
    )

    dashboard_summary = build_dashboard_summary(
        goals_summary=goals_summary,
        corners_summary=corners_summary,
        result_summary=result_summary,
        ensemble_summary=ensemble_summary,
        fixture_summary=fixture_summary
    )

    high_level_kpis = build_high_level_kpis(
        goals_summary=goals_summary,
        corners_summary=corners_summary,
        result_summary=result_summary,
        ensemble_summary=ensemble_summary,
        fixture_summary=fixture_summary
    )

    file_status = build_model_file_status()

    league_summary = combine_league_summaries(
        goals_league=goals_league,
        corners_league=corners_league,
        result_league=result_league,
        ensemble_league=ensemble_league,
        fixture_league=fixture_league
    )

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:

        high_level_kpis.to_excel(
            writer,
            sheet_name="High_Level_KPIs",
            index=False
        )

        dashboard_summary.to_excel(
            writer,
            sheet_name="Dashboard_Summary",
            index=False
        )

        league_summary.to_excel(
            writer,
            sheet_name="League_Performance",
            index=False
        )

        file_status.to_excel(
            writer,
            sheet_name="File_Status",
            index=False
        )

    print("\n======================================")
    print("FOOTBALL MODEL PERFORMANCE DASHBOARD EXPORTED")
    print("======================================")
    print("Mode: Lightweight summary-only")
    print(f"File: {OUTPUT_FILE}")
    print("======================================\n")

    return OUTPUT_FILE


def main():
    export_football_model_performance_dashboard()


if __name__ == "__main__":
    main()