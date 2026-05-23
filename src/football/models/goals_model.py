from pathlib import Path
from datetime import datetime

import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

FEATURES_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "processed"
    / "features"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "models"
)

FEATURES_FOLDER = (
    FEATURES_DIR
    / "football_features_all_leagues"
)

FEATURES_CSV = (
    FEATURES_FOLDER
    / "match_features.csv"
)

FEATURES_XLSX = (
    FEATURES_DIR
    / "football_features_all_leagues.xlsx"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "football_goals_model_predictions.xlsx"
)


# =========================================================
# CONFIG
# =========================================================

MIN_FEATURE_ROWS_PER_LEAGUE = 100

GOALS_FEATURE_COLUMNS = [
    "Home_GoalsFor_Last3",
    "Home_GoalsAgainst_Last3",
    "Away_GoalsFor_Last3",
    "Away_GoalsAgainst_Last3",
    "Home_GoalsFor_Last5",
    "Home_GoalsAgainst_Last5",
    "Away_GoalsFor_Last5",
    "Away_GoalsAgainst_Last5",
    "Home_GoalsFor_Last10",
    "Home_GoalsAgainst_Last10",
    "Away_GoalsFor_Last10",
    "Away_GoalsAgainst_Last10",
    "AttackStrengthDiff_Last5",
    "DefenceWeaknessDiff_Last5",
    "Home_Over25Goals_Last5",
    "Away_Over25Goals_Last5",
    "Home_BTTS_Last5",
    "Away_BTTS_Last5",
]


BASE_COLUMNS = [
    "Season",
    "SeasonCode",
    "LeagueCode",
    "League",
    "Country",
    "Tier",
    "MatchDate",
    "HomeTeam",
    "AwayTeam",
    "HomeGoals",
    "AwayGoals",
    "TotalGoals",
    "Result",
    "ResultLabel",
    "BTTS",
    "Over15Goals",
    "Over25Goals",
    "Over35Goals",
]


# =========================================================
# HELPERS
# =========================================================

def ensure_directories():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def safe_read_features():
    if FEATURES_CSV.exists():
        print(f"Reading CSV features: {FEATURES_CSV}")
        return pd.read_csv(
            FEATURES_CSV
        )

    if FEATURES_XLSX.exists():
        print(f"Reading Excel features: {FEATURES_XLSX}")
        return pd.read_excel(
            FEATURES_XLSX,
            sheet_name="Match_Features",
            engine="openpyxl"
        )

    print("No football feature file found.")
    return pd.DataFrame()


def add_missing_columns(
    df,
    columns
):
    for col in columns:
        if col not in df.columns:
            df[col] = None

    return df


def safe_numeric(
    df,
    col
):
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    return df


def clamp_probability(value):
    if pd.isna(value):
        return 0.5

    if value < 0:
        return 0.0

    if value > 1:
        return 1.0

    return float(value)


def classify_probability(probability):
    if probability >= 0.70:
        return "High"

    if probability >= 0.58:
        return "Medium"

    if probability >= 0.50:
        return "Low"

    return "Avoid"


# =========================================================
# MODEL LOGIC
# =========================================================

def calculate_expected_goals(row):
    home_attack = row.get(
        "Home_GoalsFor_Last5",
        0
    )

    home_concede = row.get(
        "Home_GoalsAgainst_Last5",
        0
    )

    away_attack = row.get(
        "Away_GoalsFor_Last5",
        0
    )

    away_concede = row.get(
        "Away_GoalsAgainst_Last5",
        0
    )

    home_expected = (
        (home_attack * 0.60)
        + (away_concede * 0.40)
    )

    away_expected = (
        (away_attack * 0.60)
        + (home_concede * 0.40)
    )

    total_expected = home_expected + away_expected

    return home_expected, away_expected, total_expected


def calculate_over_probability(
    expected_goals,
    line
):
    if expected_goals <= 0:
        return 0.5

    if line == 1.5:
        probability = (
            0.25
            + (expected_goals / 5.0)
        )

    elif line == 2.5:
        probability = (
            0.15
            + (expected_goals / 6.0)
        )

    elif line == 3.5:
        probability = (
            0.05
            + (expected_goals / 8.0)
        )

    else:
        probability = 0.5

    return clamp_probability(
        probability
    )


def calculate_btts_probability(row):
    home_scoring = row.get(
        "Home_GoalsFor_Last5",
        0
    )

    away_scoring = row.get(
        "Away_GoalsFor_Last5",
        0
    )

    home_conceding = row.get(
        "Home_GoalsAgainst_Last5",
        0
    )

    away_conceding = row.get(
        "Away_GoalsAgainst_Last5",
        0
    )

    home_btts_rate = row.get(
        "Home_BTTS_Last5",
        0.5
    )

    away_btts_rate = row.get(
        "Away_BTTS_Last5",
        0.5
    )

    scoring_component = (
        (home_scoring + away_scoring)
        / 4.0
    )

    conceding_component = (
        (home_conceding + away_conceding)
        / 4.0
    )

    trend_component = (
        home_btts_rate + away_btts_rate
    ) / 2.0

    probability = (
        (scoring_component * 0.35)
        + (conceding_component * 0.25)
        + (trend_component * 0.40)
    )

    return clamp_probability(
        probability
    )


def apply_goals_model(df):
    model_df = df.copy()

    expected_home = []
    expected_away = []
    expected_total = []

    over15_probs = []
    over25_probs = []
    over35_probs = []
    btts_probs = []

    for _, row in model_df.iterrows():
        home_xg, away_xg, total_xg = calculate_expected_goals(
            row
        )

        expected_home.append(
            round(home_xg, 3)
        )

        expected_away.append(
            round(away_xg, 3)
        )

        expected_total.append(
            round(total_xg, 3)
        )

        over15_probs.append(
            round(
                calculate_over_probability(
                    total_xg,
                    1.5
                ),
                3
            )
        )

        over25_probs.append(
            round(
                calculate_over_probability(
                    total_xg,
                    2.5
                ),
                3
            )
        )

        over35_probs.append(
            round(
                calculate_over_probability(
                    total_xg,
                    3.5
                ),
                3
            )
        )

        btts_probs.append(
            round(
                calculate_btts_probability(
                    row
                ),
                3
            )
        )

    model_df["ExpectedHomeGoals"] = expected_home
    model_df["ExpectedAwayGoals"] = expected_away
    model_df["ExpectedTotalGoals"] = expected_total

    model_df["Over15Probability"] = over15_probs
    model_df["Over25Probability"] = over25_probs
    model_df["Over35Probability"] = over35_probs
    model_df["BTTSProbability"] = btts_probs

    model_df["Over15Pick"] = model_df["Over15Probability"].apply(
        classify_probability
    )

    model_df["Over25Pick"] = model_df["Over25Probability"].apply(
        classify_probability
    )

    model_df["Over35Pick"] = model_df["Over35Probability"].apply(
        classify_probability
    )

    model_df["BTTSPick"] = model_df["BTTSProbability"].apply(
        classify_probability
    )

    return model_df


# =========================================================
# BACKTEST SCORING
# =========================================================

def score_predictions(model_df):
    scored_df = model_df.copy()

    scored_df["Over15Correct"] = (
        (
            scored_df["Over15Probability"] >= 0.58
        )
        == (
            scored_df["Over15Goals"] == 1
        )
    ).astype(int)

    scored_df["Over25Correct"] = (
        (
            scored_df["Over25Probability"] >= 0.58
        )
        == (
            scored_df["Over25Goals"] == 1
        )
    ).astype(int)

    scored_df["Over35Correct"] = (
        (
            scored_df["Over35Probability"] >= 0.58
        )
        == (
            scored_df["Over35Goals"] == 1
        )
    ).astype(int)

    scored_df["BTTSCorrect"] = (
        (
            scored_df["BTTSProbability"] >= 0.58
        )
        == (
            scored_df["BTTS"] == 1
        )
    ).astype(int)

    return scored_df


def build_summary(scored_df):
    if scored_df.empty:
        return pd.DataFrame()

    rows = []

    metrics = [
        {
            "Model": "Over 1.5 Goals",
            "ProbabilityColumn": "Over15Probability",
            "ActualColumn": "Over15Goals",
            "CorrectColumn": "Over15Correct",
        },
        {
            "Model": "Over 2.5 Goals",
            "ProbabilityColumn": "Over25Probability",
            "ActualColumn": "Over25Goals",
            "CorrectColumn": "Over25Correct",
        },
        {
            "Model": "Over 3.5 Goals",
            "ProbabilityColumn": "Over35Probability",
            "ActualColumn": "Over35Goals",
            "CorrectColumn": "Over35Correct",
        },
        {
            "Model": "BTTS",
            "ProbabilityColumn": "BTTSProbability",
            "ActualColumn": "BTTS",
            "CorrectColumn": "BTTSCorrect",
        },
    ]

    for metric in metrics:
        correct_col = metric["CorrectColumn"]
        probability_col = metric["ProbabilityColumn"]
        actual_col = metric["ActualColumn"]

        rows.append({
            "Model": metric["Model"],
            "RowsScored": len(scored_df),
            "AverageProbability": round(
                scored_df[probability_col].mean(),
                3
            ),
            "ActualHitRate": round(
                scored_df[actual_col].mean(),
                3
            ),
            "PredictionAccuracy": round(
                scored_df[correct_col].mean(),
                3
            ),
        })

    return pd.DataFrame(rows)


def build_league_summary(scored_df):
    if scored_df.empty:
        return pd.DataFrame()

    league_summary = (
        scored_df
        .groupby(
            [
                "Tier",
                "Country",
                "League",
            ],
            dropna=False
        )
        .agg(
            Rows=("League", "count"),
            AvgExpectedGoals=("ExpectedTotalGoals", "mean"),
            AvgOver15Probability=("Over15Probability", "mean"),
            AvgOver25Probability=("Over25Probability", "mean"),
            AvgBTTSProbability=("BTTSProbability", "mean"),
            Over15Accuracy=("Over15Correct", "mean"),
            Over25Accuracy=("Over25Correct", "mean"),
            Over35Accuracy=("Over35Correct", "mean"),
            BTTSAccuracy=("BTTSCorrect", "mean"),
        )
        .reset_index()
    )

    numeric_cols = [
        "AvgExpectedGoals",
        "AvgOver15Probability",
        "AvgOver25Probability",
        "AvgBTTSProbability",
        "Over15Accuracy",
        "Over25Accuracy",
        "Over35Accuracy",
        "BTTSAccuracy",
    ]

    for col in numeric_cols:
        league_summary[col] = league_summary[col].round(
            3
        )

    return league_summary


# =========================================================
# EXPORT
# =========================================================

def export_goals_model():
    ensure_directories()

    features_df = safe_read_features()

    if features_df.empty:
        print("No feature data available.")
        return pd.DataFrame()

    features_df = add_missing_columns(
        features_df,
        BASE_COLUMNS + GOALS_FEATURE_COLUMNS
    )

    features_df["MatchDate"] = pd.to_datetime(
        features_df["MatchDate"],
        errors="coerce"
    )

    for col in GOALS_FEATURE_COLUMNS + [
        "HomeGoals",
        "AwayGoals",
        "TotalGoals",
        "BTTS",
        "Over15Goals",
        "Over25Goals",
        "Over35Goals",
    ]:
        features_df = safe_numeric(
            features_df,
            col
        )

    model_input_df = features_df[
        features_df["MatchDate"].notna()
    ].copy()

    model_input_df = model_input_df[
        model_input_df["TotalGoals"].notna()
    ].copy()

    scored_df = apply_goals_model(
        model_input_df
    )

    scored_df = score_predictions(
        scored_df
    )

    output_cols = [
        col for col in (
            BASE_COLUMNS
            + [
                "ExpectedHomeGoals",
                "ExpectedAwayGoals",
                "ExpectedTotalGoals",
                "Over15Probability",
                "Over15Pick",
                "Over15Correct",
                "Over25Probability",
                "Over25Pick",
                "Over25Correct",
                "Over35Probability",
                "Over35Pick",
                "Over35Correct",
                "BTTSProbability",
                "BTTSPick",
                "BTTSCorrect",
            ]
        )
        if col in scored_df.columns
    ]

    output_df = scored_df[
        output_cols
    ].copy()

    summary_df = build_summary(
        scored_df
    )

    league_summary_df = build_league_summary(
        scored_df
    )

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:

        output_df.to_excel(
            writer,
            sheet_name="Goals_Model_Predictions",
            index=False
        )

        summary_df.to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

        league_summary_df.to_excel(
            writer,
            sheet_name="League_Summary",
            index=False
        )

    print("\n======================================")
    print("FOOTBALL GOALS MODEL EXPORTED")
    print("======================================")
    print(f"Rows: {len(output_df)}")
    print(f"File: {OUTPUT_FILE}")
    print("======================================\n")

    return output_df


# =========================================================
# CLI
# =========================================================

def main():
    export_goals_model()


if __name__ == "__main__":
    main()