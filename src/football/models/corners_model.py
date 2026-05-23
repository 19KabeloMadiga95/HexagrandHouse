from pathlib import Path

import pandas as pd


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

FEATURES_CSV = (
    FEATURES_DIR
    / "football_features_all_leagues"
    / "match_features.csv"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "football_corners_model_predictions.xlsx"
)


CORNERS_FEATURE_COLUMNS = [
    "Home_CornersFor_Last3",
    "Home_CornersAgainst_Last3",
    "Away_CornersFor_Last3",
    "Away_CornersAgainst_Last3",
    "Home_CornersFor_Last5",
    "Home_CornersAgainst_Last5",
    "Away_CornersFor_Last5",
    "Away_CornersAgainst_Last5",
    "Home_CornersFor_Last10",
    "Home_CornersAgainst_Last10",
    "Away_CornersFor_Last10",
    "Away_CornersAgainst_Last10",
    "CornerAttackDiff_Last5",
    "Home_Over95Corners_Last5",
    "Away_Over95Corners_Last5",
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
    "HomeCorners",
    "AwayCorners",
    "TotalCorners",
    "Over75Corners",
    "Over85Corners",
    "Over95Corners",
    "Over105Corners",
    "Over115Corners",
]


def ensure_directories():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def safe_read_features():
    if FEATURES_CSV.exists():
        print(f"Reading CSV features: {FEATURES_CSV}")

        return pd.read_csv(
            FEATURES_CSV,
            low_memory=False
        )

    print("No football feature CSV found.")

    return pd.DataFrame()


def add_missing_columns(df, columns):
    df = df.copy()

    missing_columns = [
        col for col in columns
        if col not in df.columns
    ]

    if missing_columns:
        missing_df = pd.DataFrame(
            {
                col: None
                for col in missing_columns
            },
            index=df.index
        )

        df = pd.concat(
            [
                df,
                missing_df,
            ],
            axis=1
        )

    return df.copy()


def safe_numeric(df, col):
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    return df


def safe_value(row, col, default=0.0):
    value = row.get(
        col,
        default
    )

    if pd.isna(value):
        return default

    try:
        return float(value)

    except Exception:
        return default


def clamp_probability(value):
    if pd.isna(value):
        return 0.5

    value = float(value)

    if value < 0:
        return 0.0

    if value > 1:
        return 1.0

    return value


def classify_probability(probability):
    if probability >= 0.70:
        return "High"

    if probability >= 0.58:
        return "Medium"

    if probability >= 0.50:
        return "Low"

    return "Avoid"


def calculate_expected_corners(row):
    home_corners_for = safe_value(
        row,
        "Home_CornersFor_Last5"
    )

    home_corners_against = safe_value(
        row,
        "Home_CornersAgainst_Last5"
    )

    away_corners_for = safe_value(
        row,
        "Away_CornersFor_Last5"
    )

    away_corners_against = safe_value(
        row,
        "Away_CornersAgainst_Last5"
    )

    home_expected = (
        (home_corners_for * 0.60)
        + (away_corners_against * 0.40)
    )

    away_expected = (
        (away_corners_for * 0.60)
        + (home_corners_against * 0.40)
    )

    total_expected = home_expected + away_expected

    return home_expected, away_expected, total_expected


def calculate_corner_over_probability(
    expected_corners,
    line
):
    if expected_corners <= 0:
        return 0.0

    if line == 7.5:
        probability = 0.20 + (expected_corners / 14.0)

    elif line == 8.5:
        probability = 0.15 + (expected_corners / 15.5)

    elif line == 9.5:
        probability = 0.10 + (expected_corners / 17.0)

    elif line == 10.5:
        probability = 0.05 + (expected_corners / 18.5)

    else:
        probability = 0.5

    return clamp_probability(
        probability
    )


def apply_corners_model(df):
    model_df = df.copy()

    expected_home = []
    expected_away = []
    expected_total = []

    over75_probs = []
    over85_probs = []
    over95_probs = []
    over105_probs = []

    for _, row in model_df.iterrows():
        home_corners, away_corners, total_corners = calculate_expected_corners(
            row
        )

        expected_home.append(
            round(home_corners, 3)
        )

        expected_away.append(
            round(away_corners, 3)
        )

        expected_total.append(
            round(total_corners, 3)
        )

        over75_probs.append(
            round(
                calculate_corner_over_probability(
                    total_corners,
                    7.5
                ),
                3
            )
        )

        over85_probs.append(
            round(
                calculate_corner_over_probability(
                    total_corners,
                    8.5
                ),
                3
            )
        )

        over95_probs.append(
            round(
                calculate_corner_over_probability(
                    total_corners,
                    9.5
                ),
                3
            )
        )

        over105_probs.append(
            round(
                calculate_corner_over_probability(
                    total_corners,
                    10.5
                ),
                3
            )
        )

    model_df["ExpectedHomeCorners"] = expected_home
    model_df["ExpectedAwayCorners"] = expected_away
    model_df["ExpectedTotalCorners"] = expected_total

    model_df["Over75CornersProbability"] = over75_probs
    model_df["Over85CornersProbability"] = over85_probs
    model_df["Over95CornersProbability"] = over95_probs
    model_df["Over105CornersProbability"] = over105_probs

    model_df["Over75CornersPick"] = model_df[
        "Over75CornersProbability"
    ].apply(
        classify_probability
    )

    model_df["Over85CornersPick"] = model_df[
        "Over85CornersProbability"
    ].apply(
        classify_probability
    )

    model_df["Over95CornersPick"] = model_df[
        "Over95CornersProbability"
    ].apply(
        classify_probability
    )

    model_df["Over105CornersPick"] = model_df[
        "Over105CornersProbability"
    ].apply(
        classify_probability
    )

    return model_df


def score_predictions(model_df):
    scored_df = model_df.copy()

    scored_df["Over75CornersCorrect"] = (
        (
            scored_df["Over75CornersProbability"] >= 0.58
        )
        == (
            scored_df["Over75Corners"] == 1
        )
    ).astype(int)

    scored_df["Over85CornersCorrect"] = (
        (
            scored_df["Over85CornersProbability"] >= 0.58
        )
        == (
            scored_df["Over85Corners"] == 1
        )
    ).astype(int)

    scored_df["Over95CornersCorrect"] = (
        (
            scored_df["Over95CornersProbability"] >= 0.58
        )
        == (
            scored_df["Over95Corners"] == 1
        )
    ).astype(int)

    scored_df["Over105CornersCorrect"] = (
        (
            scored_df["Over105CornersProbability"] >= 0.58
        )
        == (
            scored_df["Over105Corners"] == 1
        )
    ).astype(int)

    return scored_df


def build_summary(scored_df, excluded_rows):
    if scored_df.empty:
        return pd.DataFrame()

    metrics = [
        {
            "Model": "Over 7.5 Corners",
            "ProbabilityColumn": "Over75CornersProbability",
            "ActualColumn": "Over75Corners",
            "CorrectColumn": "Over75CornersCorrect",
        },
        {
            "Model": "Over 8.5 Corners",
            "ProbabilityColumn": "Over85CornersProbability",
            "ActualColumn": "Over85Corners",
            "CorrectColumn": "Over85CornersCorrect",
        },
        {
            "Model": "Over 9.5 Corners",
            "ProbabilityColumn": "Over95CornersProbability",
            "ActualColumn": "Over95Corners",
            "CorrectColumn": "Over95CornersCorrect",
        },
        {
            "Model": "Over 10.5 Corners",
            "ProbabilityColumn": "Over105CornersProbability",
            "ActualColumn": "Over105Corners",
            "CorrectColumn": "Over105CornersCorrect",
        },
    ]

    rows = []

    for metric in metrics:
        rows.append({
            "Model": metric["Model"],
            "RowsScored": len(scored_df),
            "RowsExcludedMissingCorners": excluded_rows,
            "AverageProbability": round(
                scored_df[metric["ProbabilityColumn"]].mean(),
                3
            ),
            "ActualHitRate": round(
                scored_df[metric["ActualColumn"]].mean(),
                3
            ),
            "PredictionAccuracy": round(
                scored_df[metric["CorrectColumn"]].mean(),
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
            AvgExpectedCorners=("ExpectedTotalCorners", "mean"),
            AvgOver75Probability=("Over75CornersProbability", "mean"),
            AvgOver85Probability=("Over85CornersProbability", "mean"),
            AvgOver95Probability=("Over95CornersProbability", "mean"),
            Over75Accuracy=("Over75CornersCorrect", "mean"),
            Over85Accuracy=("Over85CornersCorrect", "mean"),
            Over95Accuracy=("Over95CornersCorrect", "mean"),
            Over105Accuracy=("Over105CornersCorrect", "mean"),
        )
        .reset_index()
    )

    numeric_cols = [
        "AvgExpectedCorners",
        "AvgOver75Probability",
        "AvgOver85Probability",
        "AvgOver95Probability",
        "Over75Accuracy",
        "Over85Accuracy",
        "Over95Accuracy",
        "Over105Accuracy",
    ]

    for col in numeric_cols:
        league_summary[col] = league_summary[col].round(
            3
        )

    return league_summary


def build_diagnostics(original_df, model_input_df):
    rows = [
        {
            "Metric": "Original Rows",
            "Value": len(original_df),
        },
        {
            "Metric": "Rows With Valid Corners",
            "Value": len(model_input_df),
        },
        {
            "Metric": "Rows Excluded Missing Corners",
            "Value": len(original_df) - len(model_input_df),
        },
        {
            "Metric": "Leagues With Corner Data",
            "Value": model_input_df["League"].nunique()
            if "League" in model_input_df.columns
            else 0,
        },
    ]

    if not model_input_df.empty and "Tier" in model_input_df.columns:
        tier_counts = (
            model_input_df["Tier"]
            .value_counts()
            .reset_index()
        )

        tier_counts.columns = [
            "Metric",
            "Value",
        ]

        tier_counts["Metric"] = (
            "Rows - "
            + tier_counts["Metric"].astype(str)
        )

        rows_df = pd.DataFrame(rows)

        return pd.concat(
            [
                rows_df,
                tier_counts,
            ],
            ignore_index=True
        )

    return pd.DataFrame(rows)


def export_corners_model():
    ensure_directories()

    features_df = safe_read_features()

    if features_df.empty:
        print("No feature data available.")

        return pd.DataFrame()

    features_df = add_missing_columns(
        features_df,
        BASE_COLUMNS + CORNERS_FEATURE_COLUMNS
    )

    features_df["MatchDate"] = pd.to_datetime(
        features_df["MatchDate"],
        errors="coerce"
    )

    for col in (
        CORNERS_FEATURE_COLUMNS
        + [
            "HomeCorners",
            "AwayCorners",
            "TotalCorners",
            "Over75Corners",
            "Over85Corners",
            "Over95Corners",
            "Over105Corners",
            "Over115Corners",
        ]
    ):
        features_df = safe_numeric(
            features_df,
            col
        )

    original_rows = len(features_df)

    model_input_df = features_df[
        features_df["MatchDate"].notna()
    ].copy()

    model_input_df = model_input_df[
        model_input_df["HomeCorners"].notna()
        & model_input_df["AwayCorners"].notna()
        & model_input_df["TotalCorners"].notna()
    ].copy()

    model_input_df = model_input_df[
        model_input_df["TotalCorners"] > 0
    ].copy()

    excluded_rows = original_rows - len(model_input_df)

    scored_df = apply_corners_model(
        model_input_df
    )

    scored_df = score_predictions(
        scored_df
    )

    output_cols = [
        col for col in (
            BASE_COLUMNS
            + [
                "ExpectedHomeCorners",
                "ExpectedAwayCorners",
                "ExpectedTotalCorners",
                "Over75CornersProbability",
                "Over75CornersPick",
                "Over75CornersCorrect",
                "Over85CornersProbability",
                "Over85CornersPick",
                "Over85CornersCorrect",
                "Over95CornersProbability",
                "Over95CornersPick",
                "Over95CornersCorrect",
                "Over105CornersProbability",
                "Over105CornersPick",
                "Over105CornersCorrect",
            ]
        )
        if col in scored_df.columns
    ]

    output_df = scored_df[
        output_cols
    ].copy()

    summary_df = build_summary(
        scored_df,
        excluded_rows
    )

    league_summary_df = build_league_summary(
        scored_df
    )

    diagnostics_df = build_diagnostics(
        features_df,
        model_input_df
    )

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:

        output_df.to_excel(
            writer,
            sheet_name="Corners_Model_Predictions",
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

        diagnostics_df.to_excel(
            writer,
            sheet_name="Diagnostics",
            index=False
        )

    print("\n======================================")
    print("FOOTBALL CORNERS MODEL EXPORTED")
    print("======================================")
    print(f"Rows scored: {len(output_df)}")
    print(f"Rows excluded missing corners: {excluded_rows}")
    print(f"File: {OUTPUT_FILE}")
    print("======================================\n")

    return output_df


def main():
    export_corners_model()


if __name__ == "__main__":
    main()