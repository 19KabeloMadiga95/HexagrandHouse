from pathlib import Path
from datetime import datetime

import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

MASTER_FILE = (
    BASE_DIR
    / "data"
    / "master"
    / "lottery_historical_master.xlsx"
)

QUALITY_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "quality"
    / "lottery_quality_report.xlsx"
)

BACKTEST_DIR = (
    BASE_DIR
    / "data"
    / "exports"
    / "backtesting"
)

PREDICTIONS_DIR = (
    BASE_DIR
    / "data"
    / "exports"
    / "predictions"
)

FINAL_PREDICTIONS_DIR = (
    BASE_DIR
    / "data"
    / "exports"
    / "final_predictions"
)

REPORTING_DIR = (
    BASE_DIR
    / "data"
    / "exports"
    / "reporting"
)

OUTPUT_FILE = (
    REPORTING_DIR
    / "daily_lottery_summary.xlsx"
)

UNIFIED_DASHBOARD_FILE = (
    BACKTEST_DIR
    / "unified_model_performance_dashboard.xlsx"
)

ALL_ENSEMBLE_FILE = (
    FINAL_PREDICTIONS_DIR
    / "all_games_ensemble_predictions.xlsx"
)


# =========================================================
# INPUT PREDICTION FILES
# =========================================================

BASE_PREDICTION_FILES = [
    {
        "GameFamily": "PowerBall",
        "File": PREDICTIONS_DIR / "powerball_predictions.xlsx",
        "Sheet": "PowerBall_Predictions",
    },
    {
        "GameFamily": "Lotto",
        "File": PREDICTIONS_DIR / "lotto_predictions.xlsx",
        "Sheet": "Lotto_Predictions",
    },
    {
        "GameFamily": "Daily Lotto",
        "File": PREDICTIONS_DIR / "daily_lotto_predictions.xlsx",
        "Sheet": "Daily_Lotto_Predictions",
    },
    {
        "GameFamily": "UK49s",
        "File": PREDICTIONS_DIR / "uk49s_predictions.xlsx",
        "Sheet": "UK49s_Predictions",
    },
]


# =========================================================
# HELPERS
# =========================================================

def safe_read_excel(
    path,
    sheet_name=0
):
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine="openpyxl"
        )

    except Exception:
        return pd.DataFrame()


def clean_dataframe(df):
    if df.empty:
        return df

    df = df.copy()

    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str)

    return df


def dataframe_to_text(value):
    if pd.isna(value):
        return "-"

    return str(value)


# =========================================================
# LOADERS
# =========================================================

def load_master_data():
    df = safe_read_excel(
        MASTER_FILE
    )

    if df.empty:
        return df

    if "DrawDate" in df.columns:
        df["DrawDate"] = pd.to_datetime(
            df["DrawDate"],
            errors="coerce"
        )

    return df


def load_quality_summary():
    return clean_dataframe(
        safe_read_excel(
            QUALITY_FILE,
            "Summary"
        )
    )


def load_unified_leaderboard():
    return clean_dataframe(
        safe_read_excel(
            UNIFIED_DASHBOARD_FILE,
            "Unified_Leaderboard"
        )
    )


def load_best_by_game():
    return clean_dataframe(
        safe_read_excel(
            UNIFIED_DASHBOARD_FILE,
            "Best_By_Game"
        )
    )


def load_vs_random():
    return clean_dataframe(
        safe_read_excel(
            UNIFIED_DASHBOARD_FILE,
            "Vs_Random"
        )
    )


def load_final_ensembles():
    return clean_dataframe(
        safe_read_excel(
            ALL_ENSEMBLE_FILE,
            "All_Ensemble_Predictions"
        )
    )


def load_base_predictions():
    frames = []

    for item in BASE_PREDICTION_FILES:
        df = safe_read_excel(
            item["File"],
            item["Sheet"]
        )

        df = clean_dataframe(
            df
        )

        if df.empty:
            continue

        df.insert(
            0,
            "GameFamily",
            item["GameFamily"]
        )

        df["PredictionLayer"] = "BasePrediction"

        frames.append(
            df
        )

    if frames:
        return pd.concat(
            frames,
            ignore_index=True
        )

    return pd.DataFrame()


# =========================================================
# SUMMARY TABLES
# =========================================================

def build_today_snapshot(
    master_df,
    leaderboard_df,
    ensemble_df
):
    rows = []

    rows.append({
        "Metric": "Generated At",
        "Value": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    })

    rows.append({
        "Metric": "Historical Rows",
        "Value": len(master_df),
    })

    rows.append({
        "Metric": "Games Covered",
        "Value": (
            master_df["GameFamily"].nunique()
            if not master_df.empty and "GameFamily" in master_df.columns
            else 0
        ),
    })

    rows.append({
        "Metric": "Latest Draw Date",
        "Value": (
            str(master_df["DrawDate"].max().date())
            if not master_df.empty and "DrawDate" in master_df.columns
            else "-"
        ),
    })

    rows.append({
        "Metric": "Unified Models Compared",
        "Value": len(leaderboard_df),
    })

    if not leaderboard_df.empty:
        rows.append({
            "Metric": "Top Game",
            "Value": leaderboard_df.iloc[0].get(
                "GameFamily",
                "-"
            ),
        })

        rows.append({
            "Metric": "Top Model",
            "Value": leaderboard_df.iloc[0].get(
                "ModelName",
                "-"
            ),
        })

    rows.append({
        "Metric": "Final Ensemble Rows",
        "Value": len(ensemble_df),
    })

    rows.append({
        "Metric": "Platform Status",
        "Value": "Operational",
    })

    return pd.DataFrame(rows)


def build_latest_results(
    master_df
):
    if master_df.empty:
        return pd.DataFrame()

    df = master_df.copy()

    if "DrawDate" in df.columns:
        df = df.sort_values(
            by="DrawDate",
            ascending=False
        )

    preferred_cols = [
        "GameFamily",
        "GameName",
        "DrawType",
        "DrawNumber",
        "DrawDate",
        "DrawDay",
        "N1",
        "N2",
        "N3",
        "N4",
        "N5",
        "N6",
        "Bonus",
        "Jackpot",
        "Outcome",
        "SourceName",
    ]

    cols = [
        col for col in preferred_cols
        if col in df.columns
    ]

    return df[cols].head(25)


def build_top_predictions(
    ensemble_df,
    base_predictions_df
):
    if not ensemble_df.empty:
        df = ensemble_df.copy()

        if "EnsembleRank" in df.columns:
            df["EnsembleRank"] = pd.to_numeric(
                df["EnsembleRank"],
                errors="coerce"
            )

            df = df.sort_values(
                by=[
                    "GameFamily",
                    "EnsembleRank"
                ]
            )

        return df.head(80)

    if not base_predictions_df.empty:
        df = base_predictions_df.copy()

        return df.head(80)

    return pd.DataFrame()


def build_best_model_snapshot(
    best_by_game_df
):
    if best_by_game_df.empty:
        return pd.DataFrame()

    preferred_cols = [
        "GameFamily",
        "UnifiedRank",
        "Rank",
        "ModelName",
        "DrawsTested",
        "AverageBestRegularMatch_PerDraw",
        "DrawsWithAtLeast3RegularMatches",
        "BonusHitDrawRate",
    ]

    cols = [
        col for col in preferred_cols
        if col in best_by_game_df.columns
    ]

    return best_by_game_df[cols]


def build_quick_insights(
    master_df,
    leaderboard_df,
    best_by_game_df,
    vs_random_df,
    ensemble_df
):
    rows = []

    rows.append({
        "Insight": "Phase 1 platform status",
        "Details": (
            "Historical ingestion, features, predictions, backtesting, "
            "optimization, unified scoring and final ensemble predictions are active."
        ),
    })

    if not leaderboard_df.empty:
        top = leaderboard_df.iloc[0]

        rows.append({
            "Insight": "Top overall model",
            "Details": (
                f"{top.get('GameFamily', '-')}: "
                f"{top.get('ModelName', '-')} is currently ranked first."
            ),
        })

    if not best_by_game_df.empty:
        rows.append({
            "Insight": "Best-by-game coverage",
            "Details": (
                f"{best_by_game_df['GameFamily'].nunique()} games have "
                "best-model summaries available."
            ),
        })

    if not vs_random_df.empty and "BeatsRandom_AvgBestRegular" in vs_random_df.columns:
        beats_random_count = (
            vs_random_df["BeatsRandom_AvgBestRegular"]
            .astype(str)
            .str.lower()
            .eq("yes")
            .sum()
        )

        rows.append({
            "Insight": "Models beating random",
            "Details": (
                f"{beats_random_count} model/game combinations are currently "
                "beating Random_Baseline."
            ),
        })

    if not ensemble_df.empty:
        rows.append({
            "Insight": "Final ensemble output",
            "Details": (
                f"{len(ensemble_df)} final ensemble prediction rows are available."
            ),
        })

    rows.append({
        "Insight": "Important limitation",
        "Details": (
            "Lottery results remain random. Outputs are analytical indicators, "
            "not guaranteed outcomes."
        ),
    })

    return pd.DataFrame(rows)


def build_quality_snapshot():
    summary_df = load_quality_summary()

    if summary_df.empty:
        return pd.DataFrame([
            {
                "Metric": "Quality Status",
                "Value": "Quality summary unavailable",
            }
        ])

    return summary_df


# =========================================================
# EXPORT
# =========================================================

def export_daily_summary():
    REPORTING_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    master_df = load_master_data()
    leaderboard_df = load_unified_leaderboard()
    best_by_game_df = load_best_by_game()
    vs_random_df = load_vs_random()
    ensemble_df = load_final_ensembles()
    base_predictions_df = load_base_predictions()

    today_snapshot = build_today_snapshot(
        master_df,
        leaderboard_df,
        ensemble_df
    )

    latest_results = build_latest_results(
        master_df
    )

    top_predictions = build_top_predictions(
        ensemble_df,
        base_predictions_df
    )

    best_model_snapshot = build_best_model_snapshot(
        best_by_game_df
    )

    quality_snapshot = build_quality_snapshot()

    quick_insights = build_quick_insights(
        master_df,
        leaderboard_df,
        best_by_game_df,
        vs_random_df,
        ensemble_df
    )

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:

        today_snapshot.to_excel(
            writer,
            sheet_name="Today_Snapshot",
            index=False
        )

        latest_results.to_excel(
            writer,
            sheet_name="Latest_Results",
            index=False
        )

        top_predictions.to_excel(
            writer,
            sheet_name="Top_Predictions",
            index=False
        )

        best_model_snapshot.to_excel(
            writer,
            sheet_name="Best_Models",
            index=False
        )

        quality_snapshot.to_excel(
            writer,
            sheet_name="Quality_Snapshot",
            index=False
        )

        quick_insights.to_excel(
            writer,
            sheet_name="Quick_Insights",
            index=False
        )

        leaderboard_df.to_excel(
            writer,
            sheet_name="Unified_Leaderboard",
            index=False
        )

        best_by_game_df.to_excel(
            writer,
            sheet_name="Best_By_Game",
            index=False
        )

        vs_random_df.to_excel(
            writer,
            sheet_name="Vs_Random",
            index=False
        )

    print("\nDaily lottery summary exported.")
    print(f"File: {OUTPUT_FILE}")

    return {
        "TodaySnapshot": today_snapshot,
        "LatestResults": latest_results,
        "TopPredictions": top_predictions,
        "BestModels": best_model_snapshot,
        "QualitySnapshot": quality_snapshot,
        "QuickInsights": quick_insights,
        "File": str(OUTPUT_FILE),
    }


# =========================================================
# CLI
# =========================================================

def main():
    export_daily_summary()


if __name__ == "__main__":
    main()