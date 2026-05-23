from pathlib import Path
from datetime import datetime

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[3]

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

FIXTURE_PREDICTIONS_FILE = (
    PREDICTIONS_DIR
    / "football_fixture_predictions.xlsx"
)

OUTPUT_FILE = (
    REPORTING_DIR
    / "top_plays_report.xlsx"
)


# =========================================================
# THRESHOLDS
# =========================================================

MIN_RESULT_CONFIDENCE_FOR_RESULT_PICK = 0.50
MIN_PRIMARY_MARKET_CONFIDENCE = 0.70
MIN_ELITE_MARKET_CONFIDENCE = 0.80
MIN_ELITE_SIGNAL_COUNT = 3

TOP_GRADES = [
    "S Tier",
    "A Tier",
    "B Tier",
]


# =========================================================
# HELPERS
# =========================================================

def ensure_directories():
    REPORTING_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def safe_read_excel(path, sheet_name):
    try:
        return pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine="openpyxl"
        )

    except Exception as e:
        print(f"Could not read file: {path}")
        print(f"Error: {e}")

        return pd.DataFrame()


def safe_numeric(df, col):
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    return df


def get_value(row, col, default=0):
    value = row.get(col, default)

    try:
        if pd.isna(value):
            return default

        return float(value)

    except Exception:
        return default


def clean_text(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def choose_primary_market(row):
    result_probability = get_value(
        row,
        "PredictedResultProbability",
        0
    )

    goals_probability = get_value(
        row,
        "BestGoalsProbability",
        0
    )

    corners_probability = get_value(
        row,
        "BestCornersProbability",
        0
    )

    predicted_result = clean_text(
        row.get("PredictedResult")
    )

    best_goals_pick = clean_text(
        row.get("BestGoalsPick")
    )

    best_corners_pick = clean_text(
        row.get("BestCornersPick")
    )

    market_candidates = []

    if predicted_result:
        market_candidates.append(
            {
                "PrimaryMarket": "Result",
                "PrimarySignal": predicted_result,
                "PrimaryMarketProbability": result_probability,
            }
        )

    if best_goals_pick:
        market_candidates.append(
            {
                "PrimaryMarket": "Goals",
                "PrimarySignal": best_goals_pick,
                "PrimaryMarketProbability": goals_probability,
            }
        )

    if best_corners_pick:
        market_candidates.append(
            {
                "PrimaryMarket": "Corners",
                "PrimarySignal": best_corners_pick,
                "PrimaryMarketProbability": corners_probability,
            }
        )

    if not market_candidates:
        return pd.Series(
            {
                "PrimaryMarket": "Unknown",
                "PrimarySignal": "-",
                "PrimaryMarketProbability": 0,
            }
        )

    best_market = max(
        market_candidates,
        key=lambda x: x["PrimaryMarketProbability"]
    )

    return pd.Series(best_market)


def classify_result_quality(probability):
    if probability >= 0.60:
        return "Strong"

    if probability >= 0.50:
        return "Medium"

    if probability >= 0.40:
        return "Weak"

    return "Low"


def classify_market_quality(probability):
    if probability >= 0.85:
        return "Elite"

    if probability >= 0.75:
        return "Strong"

    if probability >= 0.65:
        return "Medium"

    if probability >= 0.55:
        return "Small"

    return "Weak"


def assign_clean_grade(row):
    primary_probability = get_value(
        row,
        "PrimaryMarketProbability",
        0
    )

    signal_count = get_value(
        row,
        "SignalCount",
        0
    )

    result_probability = get_value(
        row,
        "PredictedResultProbability",
        0
    )

    primary_market = clean_text(
        row.get("PrimaryMarket")
    )

    if (
        primary_probability >= 0.90
        and signal_count >= 3
    ):
        return "S Tier"

    if (
        primary_probability >= 0.80
        and signal_count >= 2
    ):
        return "A Tier"

    if primary_probability >= 0.70:
        return "B Tier"

    if (
        primary_market == "Result"
        and result_probability >= 0.50
    ):
        return "C Tier"

    return "Watchlist"


def assign_clean_elite_flag(row):
    primary_probability = get_value(
        row,
        "PrimaryMarketProbability",
        0
    )

    signal_count = get_value(
        row,
        "SignalCount",
        0
    )

    result_probability = get_value(
        row,
        "PredictedResultProbability",
        0
    )

    primary_market = clean_text(
        row.get("PrimaryMarket")
    )

    if primary_probability < MIN_ELITE_MARKET_CONFIDENCE:
        return 0

    if signal_count < MIN_ELITE_SIGNAL_COUNT:
        return 0

    if (
        primary_market == "Result"
        and result_probability < MIN_RESULT_CONFIDENCE_FOR_RESULT_PICK
    ):
        return 0

    return 1


def assign_display_signal(row):
    primary_market = clean_text(
        row.get("PrimaryMarket")
    )

    primary_signal = clean_text(
        row.get("PrimarySignal")
    )

    if not primary_signal:
        return "-"

    return f"{primary_market}: {primary_signal}"


def add_market_intelligence(df):
    if df.empty:
        return df

    df = df.copy()

    numeric_cols = [
        "PredictedResultProbability",
        "BestGoalsProbability",
        "BestCornersProbability",
        "EnsembleConfidenceScore",
        "SignalCount",
        "ElitePrediction",
    ]

    for col in numeric_cols:
        df = safe_numeric(
            df,
            col
        )

    market_cols = df.apply(
        choose_primary_market,
        axis=1
    )

    df = pd.concat(
        [
            df,
            market_cols,
        ],
        axis=1
    )

    df["ResultQuality"] = df[
        "PredictedResultProbability"
    ].apply(
        classify_result_quality
    )

    df["PrimaryMarketQuality"] = df[
        "PrimaryMarketProbability"
    ].apply(
        classify_market_quality
    )

    df["CleanBettingGrade"] = df.apply(
        assign_clean_grade,
        axis=1
    )

    df["CleanElitePrediction"] = df.apply(
        assign_clean_elite_flag,
        axis=1
    )

    df["DisplaySignal"] = df.apply(
        assign_display_signal,
        axis=1
    )

    df["OriginalBettingGrade"] = df.get(
        "BettingGrade",
        None
    )

    df["OriginalElitePrediction"] = df.get(
        "ElitePrediction",
        None
    )

    df["BettingGrade"] = df["CleanBettingGrade"]
    df["ElitePrediction"] = df["CleanElitePrediction"]

    df["EnsembleConfidenceScore"] = df[
        "PrimaryMarketProbability"
    ]

    df["EnsembleConfidenceLabel"] = df[
        "PrimaryMarketQuality"
    ]

    return df


def build_fixture_datetime(df):
    if df.empty:
        return df

    df = df.copy()

    if "FixtureDate" not in df.columns:
        df["FixtureDateTime"] = pd.NaT
        return df

    if "KickoffTime" not in df.columns:
        df["KickoffTime"] = "12:00"

    df["FixtureDateTime"] = pd.to_datetime(
        df["FixtureDate"].astype(str)
        + " "
        + df["KickoffTime"].fillna("12:00").astype(str),
        errors="coerce"
    )

    return df


def remove_past_fixtures(df):
    if df.empty:
        return df

    df = build_fixture_datetime(df)

    now = pd.Timestamp.now()

    df = df[
        df["FixtureDateTime"].notna()
        & (df["FixtureDateTime"] >= now)
    ].copy()

    return df


# =========================================================
# TOP PLAYS
# =========================================================

def build_top_plays(fixtures_df):
    if fixtures_df.empty:
        return pd.DataFrame()

    df = fixtures_df.copy()

    df = remove_past_fixtures(df)

    df = add_market_intelligence(df)

    df = df[
        df["PrimaryMarketProbability"] >= MIN_PRIMARY_MARKET_CONFIDENCE
    ].copy()

    df = df[
        df["BettingGrade"].isin(TOP_GRADES)
    ].copy()

    df = df.sort_values(
        by=[
            "FixtureDateTime",
            "BettingGrade",
            "PrimaryMarketProbability",
            "SignalCount",
        ],
        ascending=[
            True,
            True,
            False,
            False,
        ]
    ).reset_index(drop=True)

    return df


# =========================================================
# SUMMARIES
# =========================================================

def build_summary(top_plays_df):
    rows = [
        {
            "Metric": "Top Plays",
            "Value": len(top_plays_df),
        },
        {
            "Metric": "Generated At",
            "Value": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        },
    ]

    if not top_plays_df.empty:
        rows.extend(
            [
                {
                    "Metric": "Leagues",
                    "Value": top_plays_df["League"].nunique()
                    if "League" in top_plays_df.columns
                    else 0,
                },
                {
                    "Metric": "Average Primary Market Confidence",
                    "Value": round(
                        pd.to_numeric(
                            top_plays_df["PrimaryMarketProbability"],
                            errors="coerce"
                        ).mean(),
                        3
                    )
                    if "PrimaryMarketProbability" in top_plays_df.columns
                    else 0,
                },
                {
                    "Metric": "Elite Picks",
                    "Value": int(
                        pd.to_numeric(
                            top_plays_df["ElitePrediction"],
                            errors="coerce"
                        ).fillna(0).sum()
                    )
                    if "ElitePrediction" in top_plays_df.columns
                    else 0,
                },
                {
                    "Metric": "Best Grade",
                    "Value": top_plays_df["BettingGrade"].min()
                    if "BettingGrade" in top_plays_df.columns
                    else "-",
                },
            ]
        )

    return pd.DataFrame(rows)


def build_grade_summary(top_plays_df):
    if top_plays_df.empty or "BettingGrade" not in top_plays_df.columns:
        return pd.DataFrame()

    return (
        top_plays_df
        .groupby("BettingGrade", dropna=False)
        .agg(
            Picks=("BettingGrade", "count"),
            AvgPrimaryMarketConfidence=("PrimaryMarketProbability", "mean"),
            AvgSignalCount=("SignalCount", "mean"),
            ElitePicks=("ElitePrediction", "sum"),
        )
        .reset_index()
        .round(3)
    )


def build_league_summary(top_plays_df):
    if top_plays_df.empty:
        return pd.DataFrame()

    return (
        top_plays_df
        .groupby(
            [
                "Tier",
                "Country",
                "League",
            ],
            dropna=False
        )
        .agg(
            Picks=("League", "count"),
            AvgPrimaryMarketConfidence=("PrimaryMarketProbability", "mean"),
            AvgSignalCount=("SignalCount", "mean"),
            ElitePicks=("ElitePrediction", "sum"),
        )
        .reset_index()
        .round(3)
    )


def build_market_summary(top_plays_df):
    if top_plays_df.empty or "PrimaryMarket" not in top_plays_df.columns:
        return pd.DataFrame()

    return (
        top_plays_df
        .groupby("PrimaryMarket", dropna=False)
        .agg(
            Picks=("PrimaryMarket", "count"),
            AvgConfidence=("PrimaryMarketProbability", "mean"),
            ElitePicks=("ElitePrediction", "sum"),
        )
        .reset_index()
        .round(3)
    )


# =========================================================
# EXPORT
# =========================================================

def export_top_plays_report():
    ensure_directories()

    fixtures_df = safe_read_excel(
        FIXTURE_PREDICTIONS_FILE,
        "Fixture_Predictions"
    )

    top_plays_df = build_top_plays(
        fixtures_df
    )

    summary_df = build_summary(
        top_plays_df
    )

    grade_summary_df = build_grade_summary(
        top_plays_df
    )

    league_summary_df = build_league_summary(
        top_plays_df
    )

    market_summary_df = build_market_summary(
        top_plays_df
    )

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:

        top_plays_df.to_excel(
            writer,
            sheet_name="Top_Plays",
            index=False
        )

        summary_df.to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

        grade_summary_df.to_excel(
            writer,
            sheet_name="Grade_Summary",
            index=False
        )

        league_summary_df.to_excel(
            writer,
            sheet_name="League_Summary",
            index=False
        )

        market_summary_df.to_excel(
            writer,
            sheet_name="Market_Summary",
            index=False
        )

    print("\n======================================")
    print("TOP PLAYS REPORT EXPORTED")
    print("======================================")
    print(f"Rows: {len(top_plays_df)}")
    print(f"File: {OUTPUT_FILE}")
    print("======================================\n")

    return top_plays_df


def main():
    export_top_plays_report()


if __name__ == "__main__":
    main()