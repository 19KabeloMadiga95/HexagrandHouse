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
    / "executive_lottery_report.xlsx"
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


# =========================================================
# LOADERS
# =========================================================

def load_master_data():
    df = safe_read_excel(
        MASTER_FILE
    )

    if df.empty:
        return df

    df["DrawDate"] = pd.to_datetime(
        df["DrawDate"],
        errors="coerce"
    )

    return df


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


def load_game_summary():
    return clean_dataframe(
        safe_read_excel(
            UNIFIED_DASHBOARD_FILE,
            "Game_Summary"
        )
    )


def load_final_ensembles():
    return clean_dataframe(
        safe_read_excel(
            ALL_ENSEMBLE_FILE,
            "All_Ensemble_Predictions"
        )
    )


# =========================================================
# REPORT TABLES
# =========================================================

def build_executive_summary(
    master_df,
    leaderboard_df,
    ensemble_df
):
    rows = []

    rows.append({
        "Metric": "Report Generated At",
        "Value": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    })

    rows.append({
        "Metric": "Platform Phase",
        "Value": "Phase 1 Complete",
    })

    rows.append({
        "Metric": "Historical Records",
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
            "Metric": "Best Overall Game",
            "Value": leaderboard_df.iloc[0].get(
                "GameFamily",
                "-"
            ),
        })

        rows.append({
            "Metric": "Best Overall Model",
            "Value": leaderboard_df.iloc[0].get(
                "ModelName",
                "-"
            ),
        })

        rows.append({
            "Metric": "Best Avg Regular Match / Draw",
            "Value": leaderboard_df.iloc[0].get(
                "AverageBestRegularMatch_PerDraw",
                "-"
            ),
        })

    rows.append({
        "Metric": "Final Ensemble Rows",
        "Value": len(ensemble_df),
    })

    rows.append({
        "Metric": "Status",
        "Value": "Operational",
    })

    return pd.DataFrame(rows)


def build_latest_results(master_df):
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

    return df[cols].head(50)


def build_coverage_summary(master_df):
    if master_df.empty:
        return pd.DataFrame()

    summary = (
        master_df
        .groupby(
            [
                "GameFamily",
                "GameName"
            ],
            dropna=False
        )
        .agg(
            Rows=("GameName", "count"),
            EarliestDrawDate=("DrawDate", "min"),
            LatestDrawDate=("DrawDate", "max"),
        )
        .reset_index()
    )

    return summary.sort_values(
        by=[
            "GameFamily",
            "GameName"
        ]
    )


def build_platform_status():
    return pd.DataFrame([
        {
            "Component": "Historical Ingestion",
            "Status": "Operational",
        },
        {
            "Component": "Data Quality Checks",
            "Status": "Operational",
        },
        {
            "Component": "Feature Engineering",
            "Status": "Operational",
        },
        {
            "Component": "Base Prediction Models",
            "Status": "Operational",
        },
        {
            "Component": "Backtesting",
            "Status": "Operational",
        },
        {
            "Component": "Model Comparison",
            "Status": "Operational",
        },
        {
            "Component": "Genetic Optimization",
            "Status": "Operational",
        },
        {
            "Component": "Unified Model Dashboard",
            "Status": "Operational",
        },
        {
            "Component": "Final Ensemble Predictions",
            "Status": "Operational",
        },
        {
            "Component": "Streamlit Frontend",
            "Status": "Operational",
        },
    ])


def build_statistical_insights(
    leaderboard_df,
    vs_random_df
):
    rows = []

    rows.append({
        "Insight": "Random baseline remains critical.",
        "Explanation": (
            "The platform compares every model against random selection. "
            "If random performs better, the model requires tuning."
        ),
    })

    rows.append({
        "Insight": "Unified leaderboard is now active.",
        "Explanation": (
            "PowerBall, Lotto, Daily Lotto and UK49s are evaluated "
            "through one cross-game performance view."
        ),
    })

    rows.append({
        "Insight": "Final ensemble layer is active.",
        "Explanation": (
            "Base predictions and genetic optimizer outputs are combined "
            "into final ranked ensemble predictions."
        ),
    })

    if not leaderboard_df.empty:
        top = leaderboard_df.iloc[0]

        rows.append({
            "Insight": "Current top model",
            "Explanation": (
                f"{top.get('GameFamily', '-')}: "
                f"{top.get('ModelName', '-')} currently ranks highest "
                f"on AverageBestRegularMatch_PerDraw."
            ),
        })

    if not vs_random_df.empty and "BeatsRandom_AvgBestRegular" in vs_random_df.columns:
        beats_count = (
            vs_random_df["BeatsRandom_AvgBestRegular"]
            .astype(str)
            .str.lower()
            .eq("yes")
            .sum()
        )

        rows.append({
            "Insight": "Models beating random",
            "Explanation": (
                f"{beats_count} model/game combinations are currently "
                "beating the random baseline on average best regular match."
            ),
        })

    rows.append({
        "Insight": "Important limitation",
        "Explanation": (
            "Lottery systems remain random. These analytics measure "
            "historical behaviour only and do not guarantee future outcomes."
        ),
    })

    return pd.DataFrame(rows)


# =========================================================
# EXPORT
# =========================================================

def export_executive_report():
    REPORTING_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    master_df = load_master_data()
    leaderboard_df = load_unified_leaderboard()
    best_by_game_df = load_best_by_game()
    vs_random_df = load_vs_random()
    game_summary_df = load_game_summary()
    ensemble_df = load_final_ensembles()

    executive_summary = build_executive_summary(
        master_df,
        leaderboard_df,
        ensemble_df
    )

    latest_results = build_latest_results(
        master_df
    )

    coverage_summary = build_coverage_summary(
        master_df
    )

    platform_status = build_platform_status()

    statistical_insights = build_statistical_insights(
        leaderboard_df,
        vs_random_df
    )

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:

        executive_summary.to_excel(
            writer,
            sheet_name="Executive_Summary",
            index=False
        )

        platform_status.to_excel(
            writer,
            sheet_name="Platform_Status",
            index=False
        )

        coverage_summary.to_excel(
            writer,
            sheet_name="Coverage_Summary",
            index=False
        )

        latest_results.to_excel(
            writer,
            sheet_name="Latest_Results",
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

        game_summary_df.to_excel(
            writer,
            sheet_name="Game_Summary",
            index=False
        )

        ensemble_df.to_excel(
            writer,
            sheet_name="Final_Ensembles",
            index=False
        )

        statistical_insights.to_excel(
            writer,
            sheet_name="Statistical_Insights",
            index=False
        )

    print("\nExecutive lottery report exported.")
    print(f"File: {OUTPUT_FILE}")

    return {
        "ExecutiveSummary": executive_summary,
        "PlatformStatus": platform_status,
        "CoverageSummary": coverage_summary,
        "LatestResults": latest_results,
        "UnifiedLeaderboard": leaderboard_df,
        "BestByGame": best_by_game_df,
        "VsRandom": vs_random_df,
        "GameSummary": game_summary_df,
        "FinalEnsembles": ensemble_df,
        "StatisticalInsights": statistical_insights,
        "File": str(OUTPUT_FILE),
    }


# =========================================================
# CLI
# =========================================================

def main():
    export_executive_report()


if __name__ == "__main__":
    main()