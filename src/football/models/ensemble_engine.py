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

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "predictions"
)

GOALS_FILE = MODELS_DIR / "football_goals_model_predictions.xlsx"
CORNERS_FILE = MODELS_DIR / "football_corners_model_predictions.xlsx"
RESULT_FILE = MODELS_DIR / "football_result_model_predictions.xlsx"

OUTPUT_FILE = OUTPUT_DIR / "football_ensemble_predictions.xlsx"


# =========================================================
# THRESHOLDS
# =========================================================

STRONG_SIGNAL_THRESHOLD = 0.70
ELITE_SIGNAL_THRESHOLD = 0.85
RESULT_CONFIDENCE_THRESHOLD = 0.55


# =========================================================
# HELPERS
# =========================================================

def ensure_directories():
    OUTPUT_DIR.mkdir(
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


def normalize_probability(value):
    if pd.isna(value):
        return None

    try:
        value = float(value)

    except Exception:
        return None

    if value > 1:
        value = value / 100

    if value < 0:
        return 0.0

    if value > 1:
        return 1.0

    return round(value, 3)


def confidence_label(probability):
    if pd.isna(probability):
        return "No Data"

    if probability >= 0.85:
        return "Elite"

    if probability >= 0.75:
        return "Strong"

    if probability >= 0.65:
        return "Medium"

    if probability >= 0.55:
        return "Small"

    return "Weak"


def add_match_key(df):
    df = df.copy()

    df["MatchDate"] = pd.to_datetime(
        df["MatchDate"],
        errors="coerce"
    )

    df["MatchDateKey"] = df["MatchDate"].dt.strftime(
        "%Y-%m-%d"
    )

    df["MatchKey"] = (
        df["LeagueCode"].astype(str)
        + "_"
        + df["MatchDateKey"].astype(str)
        + "_"
        + df["HomeTeam"].astype(str)
        + "_"
        + df["AwayTeam"].astype(str)
    )

    return df


def best_probability_pick(row, pick_map):
    best_pick = None
    best_probability = None

    for pick_name, probability_col in pick_map.items():
        value = row.get(
            probability_col,
            None
        )

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


# =========================================================
# PRIMARY MARKET ENGINE
# =========================================================

def determine_primary_market(row):
    result_probability = row.get(
        "PredictedResultProbability",
        0
    )

    goals_probability = row.get(
        "BestGoalsProbability",
        0
    )

    corners_probability = row.get(
        "BestCornersProbability",
        0
    )

    candidates = []

    if not pd.isna(result_probability):
        candidates.append(
            {
                "Market": "Result",
                "Signal": row.get(
                    "PredictedResult",
                    "-"
                ),
                "Probability": result_probability,
            }
        )

    if not pd.isna(goals_probability):
        candidates.append(
            {
                "Market": "Goals",
                "Signal": row.get(
                    "BestGoalsPick",
                    "-"
                ),
                "Probability": goals_probability,
            }
        )

    if not pd.isna(corners_probability):
        candidates.append(
            {
                "Market": "Corners",
                "Signal": row.get(
                    "BestCornersPick",
                    "-"
                ),
                "Probability": corners_probability,
            }
        )

    if not candidates:
        return pd.Series(
            {
                "PrimaryMarket": "Unknown",
                "PrimarySignal": "-",
                "PrimaryMarketProbability": None,
            }
        )

    best_market = max(
        candidates,
        key=lambda item: item["Probability"]
    )

    return pd.Series(
        {
            "PrimaryMarket": best_market["Market"],
            "PrimarySignal": best_market["Signal"],
            "PrimaryMarketProbability": round(
                best_market["Probability"],
                3
            ),
        }
    )


# =========================================================
# MARKET-AWARE ENSEMBLE SCORE
# =========================================================

def calculate_market_aware_score(row):
    result_prob = row.get(
        "PredictedResultProbability",
        None
    )

    goals_prob = row.get(
        "BestGoalsProbability",
        None
    )

    corners_prob = row.get(
        "BestCornersProbability",
        None
    )

    available_probs = []

    for value in [
        result_prob,
        goals_prob,
        corners_prob,
    ]:
        if not pd.isna(value):
            available_probs.append(value)

    if not available_probs:
        return None

    primary_market_probability = max(
        available_probs
    )

    signal_bonus = (
        row.get("SignalCount", 0) * 0.02
    )

    result_penalty = 0

    if (
        not pd.isna(result_prob)
        and result_prob < 0.45
    ):
        result_penalty = 0.05

    final_score = (
        primary_market_probability
        + signal_bonus
        - result_penalty
    )

    if final_score > 1:
        final_score = 1

    if final_score < 0:
        final_score = 0

    return round(final_score, 3)


# =========================================================
# BETTING GRADE ENGINE
# =========================================================

def determine_betting_grade(row):
    primary_probability = row.get(
        "PrimaryMarketProbability",
        0
    )

    signal_count = row.get(
        "SignalCount",
        0
    )

    result_probability = row.get(
        "PredictedResultProbability",
        0
    )

    if (
        primary_probability >= 0.90
        and signal_count >= 3
    ):
        return "S Tier"

    if (
        primary_probability >= 0.82
        and signal_count >= 2
    ):
        return "A Tier"

    if primary_probability >= 0.72:
        return "B Tier"

    if (
        result_probability >= RESULT_CONFIDENCE_THRESHOLD
    ):
        return "C Tier"

    return "Watchlist"


def determine_elite_flag(row):
    primary_probability = row.get(
        "PrimaryMarketProbability",
        0
    )

    signal_count = row.get(
        "SignalCount",
        0
    )

    if (
        primary_probability >= ELITE_SIGNAL_THRESHOLD
        and signal_count >= 3
    ):
        return 1

    return 0


# =========================================================
# LOAD MODEL OUTPUTS
# =========================================================

def load_goals_model():
    return safe_read_excel(
        GOALS_FILE,
        "Goals_Model_Predictions"
    )


def load_corners_model():
    return safe_read_excel(
        CORNERS_FILE,
        "Corners_Model_Predictions"
    )


def load_result_model():
    return safe_read_excel(
        RESULT_FILE,
        "Result_Model_Predictions"
    )


# =========================================================
# BUILD ENSEMBLE
# =========================================================

def build_ensemble_predictions(
    goals_df,
    corners_df,
    result_df
):
    goals_df = add_match_key(
        goals_df
    )

    corners_df = add_match_key(
        corners_df
    )

    result_df = add_match_key(
        result_df
    )

    ensemble_df = result_df.copy()

    goals_cols = [
        "MatchKey",
        "ExpectedTotalGoals",
        "Over15Probability",
        "Over25Probability",
        "Over35Probability",
        "BTTSProbability",
    ]

    corners_cols = [
        "MatchKey",
        "ExpectedTotalCorners",
        "Over75CornersProbability",
        "Over85CornersProbability",
        "Over95CornersProbability",
        "Over105CornersProbability",
    ]

    goals_cols = [
        col for col in goals_cols
        if col in goals_df.columns
    ]

    corners_cols = [
        col for col in corners_cols
        if col in corners_df.columns
    ]

    ensemble_df = ensemble_df.merge(
        goals_df[goals_cols],
        on="MatchKey",
        how="left"
    )

    ensemble_df = ensemble_df.merge(
        corners_df[corners_cols],
        on="MatchKey",
        how="left"
    )

    probability_cols = [
        "HomeWinProbability",
        "DrawProbability",
        "AwayWinProbability",
        "PredictedResultProbability",
        "Over15Probability",
        "Over25Probability",
        "Over35Probability",
        "BTTSProbability",
        "Over75CornersProbability",
        "Over85CornersProbability",
        "Over95CornersProbability",
        "Over105CornersProbability",
    ]

    for col in probability_cols:
        if col in ensemble_df.columns:
            ensemble_df[col] = ensemble_df[col].apply(
                normalize_probability
            )

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

    best_goals = ensemble_df.apply(
        lambda row: best_probability_pick(
            row,
            goals_pick_map
        ),
        axis=1
    )

    best_corners = ensemble_df.apply(
        lambda row: best_probability_pick(
            row,
            corners_pick_map
        ),
        axis=1
    )

    ensemble_df["BestGoalsPick"] = [
        item[0] for item in best_goals
    ]

    ensemble_df["BestGoalsProbability"] = [
        item[1] for item in best_goals
    ]

    ensemble_df["BestCornersPick"] = [
        item[0] for item in best_corners
    ]

    ensemble_df["BestCornersProbability"] = [
        item[1] for item in best_corners
    ]

    ensemble_df["StrongResultSignal"] = (
        ensemble_df["PredictedResultProbability"].fillna(0)
        >= STRONG_SIGNAL_THRESHOLD
    ).astype(int)

    ensemble_df["StrongGoalsSignal"] = (
        ensemble_df["BestGoalsProbability"].fillna(0)
        >= STRONG_SIGNAL_THRESHOLD
    ).astype(int)

    ensemble_df["StrongCornersSignal"] = (
        ensemble_df["BestCornersProbability"].fillna(0)
        >= STRONG_SIGNAL_THRESHOLD
    ).astype(int)

    ensemble_df["SignalCount"] = (
        ensemble_df["StrongResultSignal"]
        + ensemble_df["StrongGoalsSignal"]
        + ensemble_df["StrongCornersSignal"]
    )

    primary_market_df = ensemble_df.apply(
        determine_primary_market,
        axis=1
    )

    ensemble_df = pd.concat(
        [
            ensemble_df,
            primary_market_df,
        ],
        axis=1
    )

    ensemble_df["EnsembleConfidenceScore"] = ensemble_df.apply(
        calculate_market_aware_score,
        axis=1
    )

    ensemble_df["EnsembleConfidenceLabel"] = ensemble_df[
        "EnsembleConfidenceScore"
    ].apply(
        confidence_label
    )

    ensemble_df["BettingGrade"] = ensemble_df.apply(
        determine_betting_grade,
        axis=1
    )

    ensemble_df["ElitePrediction"] = ensemble_df.apply(
        determine_elite_flag,
        axis=1
    )

    ensemble_df["PredictionPack"] = (
        ensemble_df["PrimaryMarket"].astype(str)
        + ": "
        + ensemble_df["PrimarySignal"].astype(str)
    )

    ensemble_df["GeneratedAt"] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    ensemble_df = ensemble_df.sort_values(
        by=[
            "MatchDate",
            "PrimaryMarketProbability",
        ],
        ascending=[
            False,
            False,
        ]
    ).reset_index(drop=True)

    return ensemble_df


# =========================================================
# SUMMARIES
# =========================================================

def build_summary(ensemble_df):
    if ensemble_df.empty:
        return pd.DataFrame()

    rows = [
        {
            "Metric": "Rows",
            "Value": len(ensemble_df),
        },
        {
            "Metric": "Elite Predictions",
            "Value": int(
                ensemble_df["ElitePrediction"].sum()
            ),
        },
        {
            "Metric": "Average Primary Market Probability",
            "Value": round(
                ensemble_df["PrimaryMarketProbability"].mean(),
                3
            ),
        },
        {
            "Metric": "Average Ensemble Confidence",
            "Value": round(
                ensemble_df["EnsembleConfidenceScore"].mean(),
                3
            ),
        },
        {
            "Metric": "Generated At",
            "Value": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        },
    ]

    return pd.DataFrame(rows)


# =========================================================
# EXPORT
# =========================================================

def export_ensemble_engine():
    ensure_directories()

    goals_df = load_goals_model()
    corners_df = load_corners_model()
    result_df = load_result_model()

    if goals_df.empty or result_df.empty:
        print("Goals or result model file is missing.")
        return pd.DataFrame()

    ensemble_df = build_ensemble_predictions(
        goals_df=goals_df,
        corners_df=corners_df,
        result_df=result_df
    )

    summary_df = build_summary(
        ensemble_df
    )

    elite_df = ensemble_df[
        ensemble_df["ElitePrediction"] == 1
    ].copy()

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:

        ensemble_df.to_excel(
            writer,
            sheet_name="Ensemble_Predictions",
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

    print("\n======================================")
    print("FOOTBALL ENSEMBLE ENGINE EXPORTED")
    print("======================================")
    print(f"Rows: {len(ensemble_df)}")
    print(f"Elite predictions: {len(elite_df)}")
    print(f"File: {OUTPUT_FILE}")
    print("======================================\n")

    return ensemble_df


# =========================================================
# CLI
# =========================================================

def main():
    export_ensemble_engine()


if __name__ == "__main__":
    main()