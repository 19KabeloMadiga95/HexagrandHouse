from pathlib import Path

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

FEATURES_CSV = (
    FEATURES_DIR
    / "football_features_all_leagues"
    / "match_features.csv"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "football_result_model_predictions.xlsx"
)


# =========================================================
# CONFIG
# =========================================================

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
]


RESULT_FEATURE_COLUMNS = [
    "Home_FormPoints_Last3",
    "Away_FormPoints_Last3",
    "Home_FormPoints_Last5",
    "Away_FormPoints_Last5",
    "Home_FormPoints_Last10",
    "Away_FormPoints_Last10",

    "Home_WinRate_Last5",
    "Away_WinRate_Last5",
    "Home_DrawRate_Last5",
    "Away_DrawRate_Last5",
    "Home_LossRate_Last5",
    "Away_LossRate_Last5",

    "Home_GoalsFor_Last5",
    "Away_GoalsFor_Last5",
    "Home_GoalsAgainst_Last5",
    "Away_GoalsAgainst_Last5",

    "Home_ShotsFor_Last5",
    "Away_ShotsFor_Last5",
    "Home_ShotsOnTargetFor_Last5",
    "Away_ShotsOnTargetFor_Last5",

    "Home_CornersFor_Last5",
    "Away_CornersFor_Last5",

    "FormPointsDiff_Last5",
    "AttackStrengthDiff_Last5",
    "DefenceWeaknessDiff_Last5",
    "ShotDifference_Last5",
    "SOTDifference_Last5",
    "CornerAttackDiff_Last5",

    "Home_Points_VenueLast5",
    "Away_Points_VenueLast5",
    "Home_Win_VenueLast5",
    "Away_Win_VenueLast5",
    "Home_GoalsFor_VenueLast5",
    "Away_GoalsFor_VenueLast5",
    "Home_GoalsAgainst_VenueLast5",
    "Away_GoalsAgainst_VenueLast5",
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
        print("\nMissing columns added as blank:")
        for col in missing_columns:
            print(f"- {col}")

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
        return 0.333

    value = float(value)

    if value < 0:
        return 0.0

    if value > 1:
        return 1.0

    return value


def normalize_three_way(home_prob, draw_prob, away_prob):
    home_prob = clamp_probability(home_prob)
    draw_prob = clamp_probability(draw_prob)
    away_prob = clamp_probability(away_prob)

    total = home_prob + draw_prob + away_prob

    if total <= 0:
        return 0.333, 0.333, 0.333

    return (
        round(home_prob / total, 3),
        round(draw_prob / total, 3),
        round(away_prob / total, 3),
    )


def result_label_from_code(result):
    if result == "H":
        return "Home Win"

    if result == "D":
        return "Draw"

    if result == "A":
        return "Away Win"

    return "Unknown"


def classify_confidence(probability):
    if probability >= 0.62:
        return "High"

    if probability >= 0.52:
        return "Medium"

    if probability >= 0.42:
        return "Low"

    return "Avoid"


def choose_predicted_result(home_prob, draw_prob, away_prob):
    probabilities = {
        "Home Win": home_prob,
        "Draw": draw_prob,
        "Away Win": away_prob,
    }

    max_prob = max(
        probabilities.values()
    )

    tied_results = [
        result for result, prob in probabilities.items()
        if prob == max_prob
    ]

    if len(tied_results) > 1:
        return "No Clear Edge", max_prob

    return tied_results[0], max_prob


# =========================================================
# MODEL LOGIC
# =========================================================

def calculate_result_probabilities(row):
    form_diff = safe_value(
        row,
        "FormPointsDiff_Last5"
    )

    attack_diff = safe_value(
        row,
        "AttackStrengthDiff_Last5"
    )

    defence_weakness_diff = safe_value(
        row,
        "DefenceWeaknessDiff_Last5"
    )

    shot_diff = safe_value(
        row,
        "ShotDifference_Last5"
    )

    sot_diff = safe_value(
        row,
        "SOTDifference_Last5"
    )

    corner_diff = safe_value(
        row,
        "CornerAttackDiff_Last5"
    )

    home_venue_points = safe_value(
        row,
        "Home_Points_VenueLast5"
    )

    away_venue_points = safe_value(
        row,
        "Away_Points_VenueLast5"
    )

    home_win_rate = safe_value(
        row,
        "Home_WinRate_Last5"
    )

    away_win_rate = safe_value(
        row,
        "Away_WinRate_Last5"
    )

    home_draw_rate = safe_value(
        row,
        "Home_DrawRate_Last5"
    )

    away_draw_rate = safe_value(
        row,
        "Away_DrawRate_Last5"
    )

    home_loss_rate = safe_value(
        row,
        "Home_LossRate_Last5"
    )

    away_loss_rate = safe_value(
        row,
        "Away_LossRate_Last5"
    )

    home_goals_for = safe_value(
        row,
        "Home_GoalsFor_Last5"
    )

    away_goals_for = safe_value(
        row,
        "Away_GoalsFor_Last5"
    )

    home_goals_against = safe_value(
        row,
        "Home_GoalsAgainst_Last5"
    )

    away_goals_against = safe_value(
        row,
        "Away_GoalsAgainst_Last5"
    )

    # Positive score favours home.
    # Negative score favours away.
    strength_score = (
        (form_diff * 0.28)
        + (attack_diff * 0.18)
        - (defence_weakness_diff * 0.12)
        + (shot_diff * 0.03)
        + (sot_diff * 0.07)
        + (corner_diff * 0.03)
        + ((home_venue_points - away_venue_points) * 0.16)
        + ((home_win_rate - away_win_rate) * 0.20)
        + ((away_loss_rate - home_loss_rate) * 0.12)
        + ((home_goals_for - away_goals_for) * 0.10)
        + ((away_goals_against - home_goals_against) * 0.08)
    )

    # Home advantage remains real, but not dominant.
    home_base = 0.405
    draw_base = 0.255
    away_base = 0.340

    home_prob = home_base + (strength_score * 0.10)
    away_prob = away_base - (strength_score * 0.10)

    draw_signal = (
        home_draw_rate
        + away_draw_rate
    ) / 2.0

    balance_signal = max(
        0,
        1 - abs(strength_score)
    )

    draw_prob = (
        draw_base
        + (draw_signal * 0.12)
        + (balance_signal * 0.05)
        - (abs(strength_score) * 0.03)
    )

    return normalize_three_way(
        home_prob,
        draw_prob,
        away_prob
    )


def apply_result_model(df):
    model_df = df.copy()

    home_probs = []
    draw_probs = []
    away_probs = []

    predicted_results = []
    predicted_confidences = []
    result_confidence_labels = []

    for _, row in model_df.iterrows():
        home_prob, draw_prob, away_prob = calculate_result_probabilities(
            row
        )

        predicted_result, predicted_confidence = choose_predicted_result(
            home_prob,
            draw_prob,
            away_prob
        )

        home_probs.append(
            home_prob
        )

        draw_probs.append(
            draw_prob
        )

        away_probs.append(
            away_prob
        )

        predicted_results.append(
            predicted_result
        )

        predicted_confidences.append(
            round(
                predicted_confidence,
                3
            )
        )

        result_confidence_labels.append(
            classify_confidence(
                predicted_confidence
            )
        )

    model_df["HomeWinProbability"] = home_probs
    model_df["DrawProbability"] = draw_probs
    model_df["AwayWinProbability"] = away_probs

    model_df["PredictedResult"] = predicted_results
    model_df["PredictedResultProbability"] = predicted_confidences
    model_df["PredictedResultConfidence"] = result_confidence_labels

    return model_df


# =========================================================
# SCORING
# =========================================================

def score_predictions(model_df):
    scored_df = model_df.copy()

    scored_df["ActualResultLabel"] = scored_df["Result"].apply(
        result_label_from_code
    )

    scored_df["ResultCorrect"] = (
        scored_df["PredictedResult"]
        == scored_df["ActualResultLabel"]
    ).astype(int)

    scored_df["NoClearEdge"] = (
        scored_df["PredictedResult"] == "No Clear Edge"
    ).astype(int)

    scored_df["HomeWinPredicted"] = (
        scored_df["PredictedResult"] == "Home Win"
    ).astype(int)

    scored_df["DrawPredicted"] = (
        scored_df["PredictedResult"] == "Draw"
    ).astype(int)

    scored_df["AwayWinPredicted"] = (
        scored_df["PredictedResult"] == "Away Win"
    ).astype(int)

    return scored_df


# =========================================================
# SUMMARIES
# =========================================================

def build_summary(scored_df):
    if scored_df.empty:
        return pd.DataFrame()

    prediction_distribution = (
        scored_df["PredictedResult"]
        .value_counts(normalize=True)
        .to_dict()
    )

    rows = [
        {
            "Model": "Three-Way Result Model",
            "RowsScored": len(scored_df),
            "AverageHomeWinProbability": round(
                scored_df["HomeWinProbability"].mean(),
                3
            ),
            "AverageDrawProbability": round(
                scored_df["DrawProbability"].mean(),
                3
            ),
            "AverageAwayWinProbability": round(
                scored_df["AwayWinProbability"].mean(),
                3
            ),
            "PredictionAccuracy": round(
                scored_df["ResultCorrect"].mean(),
                3
            ),
            "ActualHomeWinRate": round(
                (scored_df["Result"] == "H").mean(),
                3
            ),
            "ActualDrawRate": round(
                (scored_df["Result"] == "D").mean(),
                3
            ),
            "ActualAwayWinRate": round(
                (scored_df["Result"] == "A").mean(),
                3
            ),
            "PredictedHomeWinRate": round(
                prediction_distribution.get("Home Win", 0),
                3
            ),
            "PredictedDrawRate": round(
                prediction_distribution.get("Draw", 0),
                3
            ),
            "PredictedAwayWinRate": round(
                prediction_distribution.get("Away Win", 0),
                3
            ),
            "NoClearEdgeRate": round(
                prediction_distribution.get("No Clear Edge", 0),
                3
            ),
        }
    ]

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
            AvgHomeWinProbability=("HomeWinProbability", "mean"),
            AvgDrawProbability=("DrawProbability", "mean"),
            AvgAwayWinProbability=("AwayWinProbability", "mean"),
            ResultAccuracy=("ResultCorrect", "mean"),
            ActualHomeWinRate=("Result", lambda x: (x == "H").mean()),
            ActualDrawRate=("Result", lambda x: (x == "D").mean()),
            ActualAwayWinRate=("Result", lambda x: (x == "A").mean()),
            PredictedHomeWinRate=("HomeWinPredicted", "mean"),
            PredictedDrawRate=("DrawPredicted", "mean"),
            PredictedAwayWinRate=("AwayWinPredicted", "mean"),
            NoClearEdgeRate=("NoClearEdge", "mean"),
        )
        .reset_index()
    )

    numeric_cols = [
        "AvgHomeWinProbability",
        "AvgDrawProbability",
        "AvgAwayWinProbability",
        "ResultAccuracy",
        "ActualHomeWinRate",
        "ActualDrawRate",
        "ActualAwayWinRate",
        "PredictedHomeWinRate",
        "PredictedDrawRate",
        "PredictedAwayWinRate",
        "NoClearEdgeRate",
    ]

    for col in numeric_cols:
        league_summary[col] = league_summary[col].round(
            3
        )

    return league_summary


def build_diagnostics(scored_df):
    if scored_df.empty:
        return pd.DataFrame()

    probability_cols = [
        "HomeWinProbability",
        "DrawProbability",
        "AwayWinProbability",
    ]

    rows = []

    for col in probability_cols:
        rows.append({
            "Column": col,
            "Min": round(scored_df[col].min(), 3),
            "Max": round(scored_df[col].max(), 3),
            "Mean": round(scored_df[col].mean(), 3),
            "UniqueValues": scored_df[col].nunique(),
        })

    prediction_counts = (
        scored_df["PredictedResult"]
        .value_counts()
        .reset_index()
    )

    prediction_counts.columns = [
        "PredictedResult",
        "Count",
    ]

    prediction_counts["Share"] = (
        prediction_counts["Count"]
        / len(scored_df)
    ).round(3)

    probability_diagnostics = pd.DataFrame(
        rows
    )

    probability_diagnostics["DiagnosticType"] = "Probability Spread"

    prediction_counts["DiagnosticType"] = "Prediction Distribution"

    prediction_counts = prediction_counts.rename(
        columns={
            "PredictedResult": "Column",
            "Count": "Min",
            "Share": "Mean",
        }
    )

    prediction_counts["Max"] = None
    prediction_counts["UniqueValues"] = None

    diagnostics_df = pd.concat(
        [
            probability_diagnostics,
            prediction_counts[
                probability_diagnostics.columns
            ],
        ],
        ignore_index=True
    )

    return diagnostics_df


# =========================================================
# EXPORT
# =========================================================

def export_result_model():
    ensure_directories()

    features_df = safe_read_features()

    if features_df.empty:
        print("No feature data available.")

        return pd.DataFrame()

    features_df = add_missing_columns(
        features_df,
        BASE_COLUMNS + RESULT_FEATURE_COLUMNS
    )

    features_df["MatchDate"] = pd.to_datetime(
        features_df["MatchDate"],
        errors="coerce"
    )

    for col in (
        RESULT_FEATURE_COLUMNS
        + [
            "HomeGoals",
            "AwayGoals",
            "TotalGoals",
        ]
    ):
        features_df = safe_numeric(
            features_df,
            col
        )

    model_input_df = features_df[
        features_df["MatchDate"].notna()
    ].copy()

    model_input_df = model_input_df[
        model_input_df["Result"].notna()
    ].copy()

    scored_df = apply_result_model(
        model_input_df
    )

    scored_df = score_predictions(
        scored_df
    )

    output_cols = [
        col for col in (
            BASE_COLUMNS
            + [
                "HomeWinProbability",
                "DrawProbability",
                "AwayWinProbability",
                "PredictedResult",
                "PredictedResultProbability",
                "PredictedResultConfidence",
                "ActualResultLabel",
                "ResultCorrect",
                "NoClearEdge",
                "HomeWinPredicted",
                "DrawPredicted",
                "AwayWinPredicted",
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

    diagnostics_df = build_diagnostics(
        scored_df
    )

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:

        output_df.to_excel(
            writer,
            sheet_name="Result_Model_Predictions",
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
    print("FOOTBALL RESULT MODEL EXPORTED")
    print("======================================")
    print(f"Rows: {len(output_df)}")
    print(f"File: {OUTPUT_FILE}")
    print("======================================\n")

    return output_df


# =========================================================
# CLI
# =========================================================

def main():
    export_result_model()


if __name__ == "__main__":
    main()