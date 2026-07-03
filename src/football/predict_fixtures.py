from pathlib import Path
from datetime import datetime

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[3]

MASTER_DIR = BASE_DIR / "data" / "football" / "master"
FEATURES_DIR = BASE_DIR / "data" / "football" / "processed" / "features"
OUTPUT_DIR = BASE_DIR / "data" / "football" / "exports" / "predictions"

FIXTURES_CSV = MASTER_DIR / "football_fixtures.csv"

TEAM_FEATURES_CSV = (
    FEATURES_DIR
    / "football_features_all_leagues"
    / "team_features_long.csv"
)

OUTPUT_FILE = OUTPUT_DIR / "football_fixture_predictions.xlsx"
OUTPUT_CSV = OUTPUT_DIR / "football_fixture_predictions.csv"


RESULT_FEATURE_COLUMNS = [
    "FormPoints_Last5",
    "WinRate_Last5",
    "DrawRate_Last5",
    "LossRate_Last5",
    "GoalsFor_Last5",
    "GoalsAgainst_Last5",
    "ShotsFor_Last5",
    "ShotsOnTargetFor_Last5",
    "CornersFor_Last5",
    "CornersAgainst_Last5",
    "BTTS_Last5",
    "Over25Goals_Last5",
    "Over95Corners_Last5",
    "Points_VenueLast5",
    "Win_VenueLast5",
    "GoalsFor_VenueLast5",
    "GoalsAgainst_VenueLast5",
    "CornersFor_VenueLast5",
    "CornersAgainst_VenueLast5",
]

ODDS_COLUMNS = [
    "Bet365HomeOdds",
    "Bet365DrawOdds",
    "Bet365AwayOdds",
    "AverageHomeOdds",
    "AverageDrawOdds",
    "AverageAwayOdds",
    "Bet365Over25Odds",
    "Bet365Under25Odds",
    "AverageOver25Odds",
    "AverageUnder25Odds",
]


def ensure_directories():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_read_csv(path):
    try:
        return pd.read_csv(path, low_memory=False)
    except Exception as e:
        print(f"Could not read file: {path}")
        print(f"Error: {e}")
        return pd.DataFrame()


def safe_numeric(df, col):
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def safe_value(row, col, default=0.0):
    value = row.get(col, default)

    if pd.isna(value):
        return default

    try:
        return float(value)
    except Exception:
        return default


def clamp_probability(value):
    if pd.isna(value):
        return None

    try:
        value = float(value)
    except Exception:
        return None

    if value < 0:
        return 0.0

    if value > 1:
        return 1.0

    return round(value, 3)


def normalize_three_way(home_prob, draw_prob, away_prob):
    home_prob = 0.333 if pd.isna(home_prob) else float(home_prob)
    draw_prob = 0.333 if pd.isna(draw_prob) else float(draw_prob)
    away_prob = 0.333 if pd.isna(away_prob) else float(away_prob)

    total = home_prob + draw_prob + away_prob

    if total <= 0:
        return 0.333, 0.333, 0.333

    return (
        round(home_prob / total, 3),
        round(draw_prob / total, 3),
        round(away_prob / total, 3),
    )


def confidence_label(probability):
    if pd.isna(probability):
        return "No Data"

    if probability >= 0.75:
        return "Elite"

    if probability >= 0.65:
        return "High"

    if probability >= 0.58:
        return "Medium"

    if probability >= 0.50:
        return "Low"

    return "Avoid"


def betting_grade(score):
    if pd.isna(score):
        return "No Grade"

    try:
        score = float(score)
    except Exception:
        return "No Grade"

    if score <= 1:
        score = score * 100

    if score >= 90:
        return "S Tier"

    if score >= 80:
        return "A Tier"

    if score >= 70:
        return "B Tier"

    if score >= 60:
        return "C Tier"

    return "Avoid"


def choose_predicted_result(home_prob, draw_prob, away_prob):
    probabilities = {
        "Home Win": home_prob,
        "Draw": draw_prob,
        "Away Win": away_prob,
    }

    max_prob = max(probabilities.values())

    tied_results = [
        result for result, prob in probabilities.items()
        if prob == max_prob
    ]

    if len(tied_results) > 1:
        return "No Clear Edge", max_prob

    return tied_results[0], max_prob


def best_probability_pick(row, pick_map):
    best_pick = None
    best_probability = None

    for pick_name, probability_col in pick_map.items():
        value = row.get(probability_col, None)

        if pd.isna(value):
            continue

        try:
            value = float(value)
        except Exception:
            continue

        if best_probability is None or value > best_probability:
            best_probability = value
            best_pick = pick_name

    if best_pick is None:
        return "No Data", None

    return best_pick, round(best_probability, 3)


def build_latest_team_feature_lookup(team_features_df):
    df = team_features_df.copy()

    df["MatchDate"] = pd.to_datetime(df["MatchDate"], errors="coerce")

    df = df[
        df["MatchDate"].notna()
        & df["LeagueCode"].notna()
        & df["Team"].notna()
    ].copy()

    for col in RESULT_FEATURE_COLUMNS:
        df = safe_numeric(df, col)

    df = df.sort_values(
        by=["LeagueCode", "Team", "MatchDate"],
        ascending=[True, True, False],
    )

    latest_df = (
        df.groupby(["LeagueCode", "Team"], dropna=False)
        .head(1)
        .copy()
    )

    return latest_df


def attach_fixture_features(fixtures_df, latest_team_features):
    fixtures = fixtures_df.copy()

    fixtures["FixtureDate"] = pd.to_datetime(
        fixtures["FixtureDate"],
        errors="coerce"
    )

    for col in ODDS_COLUMNS:
        fixtures = safe_numeric(fixtures, col)

    home_features = latest_team_features.copy()
    away_features = latest_team_features.copy()

    home_features["HomeTeam"] = home_features["Team"]
    away_features["AwayTeam"] = away_features["Team"]

    home_cols = ["LeagueCode", "HomeTeam"] + RESULT_FEATURE_COLUMNS
    away_cols = ["LeagueCode", "AwayTeam"] + RESULT_FEATURE_COLUMNS

    home_rename = {
        col: f"Home_{col}"
        for col in RESULT_FEATURE_COLUMNS
    }

    away_rename = {
        col: f"Away_{col}"
        for col in RESULT_FEATURE_COLUMNS
    }

    home_features = home_features[home_cols].rename(columns=home_rename)
    away_features = away_features[away_cols].rename(columns=away_rename)

    fixtures = fixtures.merge(
        home_features,
        on=["LeagueCode", "HomeTeam"],
        how="left"
    )

    fixtures = fixtures.merge(
        away_features,
        on=["LeagueCode", "AwayTeam"],
        how="left"
    )

    return fixtures


def calculate_result_probabilities(row):
    form_diff = safe_value(row, "Home_FormPoints_Last5") - safe_value(row, "Away_FormPoints_Last5")
    attack_diff = safe_value(row, "Home_GoalsFor_Last5") - safe_value(row, "Away_GoalsFor_Last5")
    defence_weakness_diff = safe_value(row, "Home_GoalsAgainst_Last5") - safe_value(row, "Away_GoalsAgainst_Last5")
    shot_diff = safe_value(row, "Home_ShotsFor_Last5") - safe_value(row, "Away_ShotsFor_Last5")
    sot_diff = safe_value(row, "Home_ShotsOnTargetFor_Last5") - safe_value(row, "Away_ShotsOnTargetFor_Last5")
    corner_diff = safe_value(row, "Home_CornersFor_Last5") - safe_value(row, "Away_CornersFor_Last5")
    venue_points_diff = safe_value(row, "Home_Points_VenueLast5") - safe_value(row, "Away_Points_VenueLast5")
    win_rate_diff = safe_value(row, "Home_WinRate_Last5") - safe_value(row, "Away_WinRate_Last5")
    loss_rate_edge = safe_value(row, "Away_LossRate_Last5") - safe_value(row, "Home_LossRate_Last5")

    home_draw_rate = safe_value(row, "Home_DrawRate_Last5")
    away_draw_rate = safe_value(row, "Away_DrawRate_Last5")

    strength_score = (
        (form_diff * 0.28)
        + (attack_diff * 0.18)
        - (defence_weakness_diff * 0.12)
        + (shot_diff * 0.03)
        + (sot_diff * 0.07)
        + (corner_diff * 0.03)
        + (venue_points_diff * 0.16)
        + (win_rate_diff * 0.20)
        + (loss_rate_edge * 0.12)
    )

    home_base = 0.405
    draw_base = 0.255
    away_base = 0.340

    home_prob = home_base + (strength_score * 0.10)
    away_prob = away_base - (strength_score * 0.10)

    draw_signal = (home_draw_rate + away_draw_rate) / 2.0
    balance_signal = max(0, 1 - abs(strength_score))

    draw_prob = (
        draw_base
        + (draw_signal * 0.12)
        + (balance_signal * 0.05)
        - (abs(strength_score) * 0.03)
    )

    return normalize_three_way(home_prob, draw_prob, away_prob)


def calculate_expected_goals(row):
    home_attack = safe_value(row, "Home_GoalsFor_Last5")
    home_concede = safe_value(row, "Home_GoalsAgainst_Last5")
    away_attack = safe_value(row, "Away_GoalsFor_Last5")
    away_concede = safe_value(row, "Away_GoalsAgainst_Last5")

    home_expected = (home_attack * 0.60) + (away_concede * 0.40)
    away_expected = (away_attack * 0.60) + (home_concede * 0.40)

    total_expected = home_expected + away_expected

    return home_expected, away_expected, total_expected


def calculate_over_probability(expected_goals, line):
    if expected_goals <= 0:
        return None

    if line == 1.5:
        probability = 0.25 + (expected_goals / 5.0)
    elif line == 2.5:
        probability = 0.15 + (expected_goals / 6.0)
    elif line == 3.5:
        probability = 0.05 + (expected_goals / 8.0)
    else:
        probability = None

    return clamp_probability(probability)


def calculate_btts_probability(row):
    home_scoring = safe_value(row, "Home_GoalsFor_Last5")
    away_scoring = safe_value(row, "Away_GoalsFor_Last5")
    home_conceding = safe_value(row, "Home_GoalsAgainst_Last5")
    away_conceding = safe_value(row, "Away_GoalsAgainst_Last5")

    home_btts_rate = safe_value(row, "Home_BTTS_Last5", 0.5)
    away_btts_rate = safe_value(row, "Away_BTTS_Last5", 0.5)

    scoring_component = (home_scoring + away_scoring) / 4.0
    conceding_component = (home_conceding + away_conceding) / 4.0
    trend_component = (home_btts_rate + away_btts_rate) / 2.0

    probability = (
        (scoring_component * 0.35)
        + (conceding_component * 0.25)
        + (trend_component * 0.40)
    )

    return clamp_probability(probability)


def calculate_expected_corners(row):
    home_corners_for = safe_value(row, "Home_CornersFor_Last5", None)
    home_corners_against = safe_value(row, "Home_CornersAgainst_Last5", None)
    away_corners_for = safe_value(row, "Away_CornersFor_Last5", None)
    away_corners_against = safe_value(row, "Away_CornersAgainst_Last5", None)

    required_values = [
        home_corners_for,
        home_corners_against,
        away_corners_for,
        away_corners_against,
    ]

    if any(pd.isna(value) for value in required_values):
        return None, None, None

    home_expected = (home_corners_for * 0.60) + (away_corners_against * 0.40)
    away_expected = (away_corners_for * 0.60) + (home_corners_against * 0.40)

    total_expected = home_expected + away_expected

    if total_expected <= 0:
        return None, None, None

    return home_expected, away_expected, total_expected


def calculate_corner_over_probability(expected_corners, line):
    if expected_corners is None or pd.isna(expected_corners):
        return None

    if expected_corners <= 0:
        return None

    if line == 7.5:
        probability = 0.20 + (expected_corners / 14.0)
    elif line == 8.5:
        probability = 0.15 + (expected_corners / 15.5)
    elif line == 9.5:
        probability = 0.10 + (expected_corners / 17.0)
    elif line == 10.5:
        probability = 0.05 + (expected_corners / 18.5)
    else:
        probability = None

    return clamp_probability(probability)


def apply_fixture_predictions(fixtures_df):
    df = fixtures_df.copy()

    result_home = []
    result_draw = []
    result_away = []
    predicted_result = []
    predicted_result_probability = []

    expected_home_goals = []
    expected_away_goals = []
    expected_total_goals = []

    over15 = []
    over25 = []
    over35 = []
    btts = []

    expected_home_corners = []
    expected_away_corners = []
    expected_total_corners = []

    over75_corners = []
    over85_corners = []
    over95_corners = []
    over105_corners = []

    for _, row in df.iterrows():
        home_prob, draw_prob, away_prob = calculate_result_probabilities(row)

        pick, pick_probability = choose_predicted_result(
            home_prob,
            draw_prob,
            away_prob
        )

        result_home.append(home_prob)
        result_draw.append(draw_prob)
        result_away.append(away_prob)
        predicted_result.append(pick)
        predicted_result_probability.append(round(pick_probability, 3))

        home_goals, away_goals, total_goals = calculate_expected_goals(row)

        expected_home_goals.append(round(home_goals, 3))
        expected_away_goals.append(round(away_goals, 3))
        expected_total_goals.append(round(total_goals, 3))

        over15.append(calculate_over_probability(total_goals, 1.5))
        over25.append(calculate_over_probability(total_goals, 2.5))
        over35.append(calculate_over_probability(total_goals, 3.5))
        btts.append(calculate_btts_probability(row))

        home_corners, away_corners, total_corners = calculate_expected_corners(row)

        expected_home_corners.append(None if home_corners is None else round(home_corners, 3))
        expected_away_corners.append(None if away_corners is None else round(away_corners, 3))
        expected_total_corners.append(None if total_corners is None else round(total_corners, 3))

        over75_corners.append(calculate_corner_over_probability(total_corners, 7.5))
        over85_corners.append(calculate_corner_over_probability(total_corners, 8.5))
        over95_corners.append(calculate_corner_over_probability(total_corners, 9.5))
        over105_corners.append(calculate_corner_over_probability(total_corners, 10.5))

    df["HomeWinProbability"] = result_home
    df["DrawProbability"] = result_draw
    df["AwayWinProbability"] = result_away
    df["PredictedResult"] = predicted_result
    df["PredictedResultProbability"] = predicted_result_probability

    df["ExpectedHomeGoals"] = expected_home_goals
    df["ExpectedAwayGoals"] = expected_away_goals
    df["ExpectedTotalGoals"] = expected_total_goals

    df["Over15Probability"] = over15
    df["Over25Probability"] = over25
    df["Over35Probability"] = over35
    df["BTTSProbability"] = btts

    df["ExpectedHomeCorners"] = expected_home_corners
    df["ExpectedAwayCorners"] = expected_away_corners
    df["ExpectedTotalCorners"] = expected_total_corners

    df["Over75CornersProbability"] = over75_corners
    df["Over85CornersProbability"] = over85_corners
    df["Over95CornersProbability"] = over95_corners
    df["Over105CornersProbability"] = over105_corners

    goals_pick_map = {
        "Over 1.5 Goals": "Over15Probability",
        "Over 2.5 Goals": "Over25Probability",
        "Over 3.5 Goals": "Over35Probability",
        "BTTS": "BTTSProbability",
    }

    corners_pick_map = {
        "Over 7.5 Corners": "Over75CornersProbability",
        "Over 8.5 Corners": "Over85CornersProbability",
        "Over 9.5 Corners": "Over95CornersProbability",
        "Over 10.5 Corners": "Over105CornersProbability",
    }

    best_goals = df.apply(
        lambda row: best_probability_pick(row, goals_pick_map),
        axis=1
    )

    best_corners = df.apply(
        lambda row: best_probability_pick(row, corners_pick_map),
        axis=1
    )

    df["BestGoalsPick"] = [item[0] for item in best_goals]
    df["BestGoalsProbability"] = [item[1] for item in best_goals]

    df["BestCornersPick"] = [item[0] for item in best_corners]
    df["BestCornersProbability"] = [item[1] for item in best_corners]

    df["HasCornersPrediction"] = df["BestCornersProbability"].notna().astype(int)

    df["ResultConfidenceLabel"] = df["PredictedResultProbability"].apply(confidence_label)
    df["GoalsConfidenceLabel"] = df["BestGoalsProbability"].apply(confidence_label)
    df["CornersConfidenceLabel"] = df["BestCornersProbability"].apply(confidence_label)

    def ensemble_score(row):
        result_prob = row.get("PredictedResultProbability")
        goals_prob = row.get("BestGoalsProbability")
        corners_prob = row.get("BestCornersProbability")

        weighted_scores = []
        weights = []

        if not pd.isna(result_prob):
            weighted_scores.append(result_prob * 0.35)
            weights.append(0.35)

        if not pd.isna(goals_prob):
            weighted_scores.append(goals_prob * 0.40)
            weights.append(0.40)

        if not pd.isna(corners_prob):
            weighted_scores.append(corners_prob * 0.25)
            weights.append(0.25)

        if not weights:
            return None

        return round(sum(weighted_scores) / sum(weights), 3)

    df["EnsembleConfidenceScore"] = df.apply(ensemble_score, axis=1)
    df["EnsembleConfidenceLabel"] = df["EnsembleConfidenceScore"].apply(confidence_label)
    df["BettingGrade"] = df["EnsembleConfidenceScore"].apply(betting_grade)

    df["StrongResultSignal"] = (
        df["PredictedResultProbability"].fillna(0) >= 0.58
    ).astype(int)

    df["StrongGoalsSignal"] = (
        df["BestGoalsProbability"].fillna(0) >= 0.58
    ).astype(int)

    df["StrongCornersSignal"] = (
        df["BestCornersProbability"].fillna(0) >= 0.58
    ).astype(int)

    df["SignalCount"] = (
        df["StrongResultSignal"]
        + df["StrongGoalsSignal"]
        + df["StrongCornersSignal"]
    )

    df["ElitePrediction"] = (
        (df["EnsembleConfidenceScore"].fillna(0) >= 0.65)
        & (df["SignalCount"] >= 2)
    ).astype(int)

    df["PredictionPack"] = (
        "Result: "
        + df["PredictedResult"].astype(str)
        + " | Goals: "
        + df["BestGoalsPick"].astype(str)
        + " | Corners: "
        + df["BestCornersPick"].astype(str)
    )

    df["GeneratedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return df


def build_summary(predictions_df):
    if predictions_df.empty:
        return pd.DataFrame([
            {
                "Metric": "Rows",
                "Value": 0,
            }
        ])

    rows_with_odds = 0

    if "AverageHomeOdds" in predictions_df.columns:
        rows_with_odds = int(predictions_df["AverageHomeOdds"].notna().sum())

    return pd.DataFrame([
        {
            "Metric": "Fixtures Predicted",
            "Value": len(predictions_df),
        },
        {
            "Metric": "Leagues",
            "Value": predictions_df["League"].nunique(),
        },
        {
            "Metric": "Rows With Odds",
            "Value": rows_with_odds,
        },
        {
            "Metric": "Rows With Corners Prediction",
            "Value": int(predictions_df["HasCornersPrediction"].sum()),
        },
        {
            "Metric": "Elite Predictions",
            "Value": int(predictions_df["ElitePrediction"].sum()),
        },
        {
            "Metric": "Average Ensemble Confidence",
            "Value": round(predictions_df["EnsembleConfidenceScore"].mean(), 3),
        },
        {
            "Metric": "Earliest Fixture",
            "Value": str(predictions_df["FixtureDate"].min().date()),
        },
        {
            "Metric": "Latest Fixture",
            "Value": str(predictions_df["FixtureDate"].max().date()),
        },
        {
            "Metric": "Generated At",
            "Value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    ])


def build_league_summary(predictions_df):
    if predictions_df.empty:
        return pd.DataFrame()

    league_summary = (
        predictions_df
        .groupby(["Tier", "Country", "League"], dropna=False)
        .agg(
            Fixtures=("League", "count"),
            ElitePredictions=("ElitePrediction", "sum"),
            AvgEnsembleConfidence=("EnsembleConfidenceScore", "mean"),
            AvgResultProbability=("PredictedResultProbability", "mean"),
            AvgGoalsProbability=("BestGoalsProbability", "mean"),
            AvgCornersProbability=("BestCornersProbability", "mean"),
            RowsWithCornersPrediction=("HasCornersPrediction", "sum"),
            RowsWithOdds=("AverageHomeOdds", lambda x: x.notna().sum())
            if "AverageHomeOdds" in predictions_df.columns
            else ("League", "count"),
            AvgSignalCount=("SignalCount", "mean"),
        )
        .reset_index()
    )

    numeric_cols = [
        "AvgEnsembleConfidence",
        "AvgResultProbability",
        "AvgGoalsProbability",
        "AvgCornersProbability",
        "AvgSignalCount",
    ]

    for col in numeric_cols:
        league_summary[col] = league_summary[col].round(3)

    return league_summary


def build_elite_predictions(predictions_df):
    if predictions_df.empty:
        return pd.DataFrame()

    elite_df = predictions_df[
        predictions_df["ElitePrediction"] == 1
    ].copy()

    return elite_df.sort_values(
        by=["EnsembleConfidenceScore", "SignalCount"],
        ascending=[False, False],
    )


def export_fixture_predictions():
    ensure_directories()

    fixtures_df = safe_read_csv(FIXTURES_CSV)
    team_features_df = safe_read_csv(TEAM_FEATURES_CSV)

    if fixtures_df.empty:
        print("No fixtures found.")
        return pd.DataFrame()

    if team_features_df.empty:
        print("No team features found.")
        return pd.DataFrame()

    latest_team_features = build_latest_team_feature_lookup(team_features_df)

    fixture_features = attach_fixture_features(
        fixtures_df,
        latest_team_features
    )

    predictions_df = apply_fixture_predictions(fixture_features)

    predictions_df = predictions_df.sort_values(
        by=["FixtureDate", "EnsembleConfidenceScore"],
        ascending=[True, False],
    ).reset_index(drop=True)

    summary_df = build_summary(predictions_df)
    league_summary_df = build_league_summary(predictions_df)
    elite_df = build_elite_predictions(predictions_df)

    predictions_df.to_csv(OUTPUT_CSV, index=False)

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:

        predictions_df.to_excel(
            writer,
            sheet_name="Fixture_Predictions",
            index=False
        )

        elite_df.to_excel(
            writer,
            sheet_name="Elite_Predictions",
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
    print("FOOTBALL FIXTURE PREDICTIONS EXPORTED")
    print("======================================")
    print(f"Rows: {len(predictions_df)}")
    print(f"Excel: {OUTPUT_FILE}")
    print(f"CSV  : {OUTPUT_CSV}")
    print("======================================\n")

    return predictions_df


def main():
    export_fixture_predictions()


if __name__ == "__main__":
    main()