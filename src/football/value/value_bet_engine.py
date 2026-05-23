from pathlib import Path
from datetime import datetime

import pandas as pd


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

PREDICTIONS_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "predictions"
)

VALUE_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "value"
)

FIXTURE_PREDICTIONS_FILE = (
    PREDICTIONS_DIR
    / "football_fixture_predictions.xlsx"
)

OUTPUT_FILE = (
    VALUE_DIR
    / "football_value_bets.xlsx"
)

OUTPUT_CSV = (
    VALUE_DIR
    / "football_value_bets.csv"
)


# =========================================================
# CONFIG
# =========================================================

VALUE_MARKETS = [
    {
        "Market": "Home Win",
        "ModelProbabilityColumn": "HomeWinProbability",
        "OddsColumn": "AverageHomeOdds",
    },
    {
        "Market": "Draw",
        "ModelProbabilityColumn": "DrawProbability",
        "OddsColumn": "AverageDrawOdds",
    },
    {
        "Market": "Away Win",
        "ModelProbabilityColumn": "AwayWinProbability",
        "OddsColumn": "AverageAwayOdds",
    },
    {
        "Market": "Over 2.5 Goals",
        "ModelProbabilityColumn": "Over25Probability",
        "OddsColumn": "AverageOver25Odds",
    },
    {
        "Market": "Under 2.5 Goals",
        "ModelProbabilityColumn": "Under25Probability",
        "OddsColumn": "AverageUnder25Odds",
    },
]


CORE_COLUMNS = [
    "FixtureKey",
    "FixtureDate",
    "KickoffTime",
    "Tier",
    "Country",
    "League",
    "HomeTeam",
    "AwayTeam",
    "PredictedResult",
    "BestGoalsPick",
    "BestCornersPick",
    "BettingGrade",
    "EnsembleConfidenceScore",
    "ElitePrediction",
    "SignalCount",
]


# =========================================================
# HELPERS
# =========================================================

def ensure_directories():
    VALUE_DIR.mkdir(
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


def odds_to_implied_probability(odds):
    if pd.isna(odds):
        return None

    try:
        odds = float(odds)

    except Exception:
        return None

    if odds <= 1:
        return None

    return round(
        1 / odds,
        4
    )


def value_rating(edge):
    if pd.isna(edge):
        return "No Odds"

    try:
        edge = float(edge)

    except Exception:
        return "No Odds"

    if edge >= 0.12:
        return "Strong Value"

    if edge >= 0.07:
        return "Medium Value"

    if edge >= 0.03:
        return "Small Value"

    if edge >= 0:
        return "Fair Price"

    if edge <= -0.08:
        return "Trap Bet"

    return "No Value"


def value_score(edge, model_probability, ensemble_confidence):
    if pd.isna(edge):
        return 0

    edge = float(edge)

    model_probability = 0 if pd.isna(model_probability) else float(model_probability)
    ensemble_confidence = 0 if pd.isna(ensemble_confidence) else float(ensemble_confidence)

    score = (
        (edge * 100 * 0.50)
        + (model_probability * 100 * 0.30)
        + (ensemble_confidence * 100 * 0.20)
    )

    return round(score, 2)


# =========================================================
# VALUE ENGINE
# =========================================================

def build_market_rows(predictions_df):
    rows = []

    df = predictions_df.copy()

    for col in [
        "HomeWinProbability",
        "DrawProbability",
        "AwayWinProbability",
        "Over25Probability",
        "AverageHomeOdds",
        "AverageDrawOdds",
        "AverageAwayOdds",
        "AverageOver25Odds",
        "AverageUnder25Odds",
        "EnsembleConfidenceScore",
    ]:
        df = safe_numeric(
            df,
            col
        )

    if "Under25Probability" not in df.columns:
        if "Over25Probability" in df.columns:
            df["Under25Probability"] = 1 - df["Over25Probability"]
        else:
            df["Under25Probability"] = None

    for _, row in df.iterrows():

        base_row = {
            col: row.get(col)
            for col in CORE_COLUMNS
            if col in df.columns
        }

        for market_config in VALUE_MARKETS:

            market = market_config["Market"]
            model_probability_col = market_config["ModelProbabilityColumn"]
            odds_col = market_config["OddsColumn"]

            model_probability = row.get(
                model_probability_col
            )

            odds = row.get(
                odds_col
            )

            implied_probability = odds_to_implied_probability(
                odds
            )

            if pd.isna(model_probability) or implied_probability is None:
                edge = None
            else:
                edge = round(
                    float(model_probability) - float(implied_probability),
                    4
                )

            rating = value_rating(
                edge
            )

            score = value_score(
                edge=edge,
                model_probability=model_probability,
                ensemble_confidence=row.get("EnsembleConfidenceScore")
            )

            output_row = base_row.copy()

            output_row.update(
                {
                    "Market": market,
                    "ModelProbability": round(float(model_probability), 4)
                    if not pd.isna(model_probability)
                    else None,
                    "BookmakerOdds": odds,
                    "BookmakerImpliedProbability": implied_probability,
                    "ValueEdge": edge,
                    "ValueEdgePercent": round(edge * 100, 2)
                    if edge is not None
                    else None,
                    "ValueRating": rating,
                    "ValueScore": score,
                    "GeneratedAt": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }
            )

            rows.append(
                output_row
            )

    return pd.DataFrame(rows)


def build_value_bets(value_df):
    if value_df.empty:
        return pd.DataFrame()

    keep_ratings = [
        "Strong Value",
        "Medium Value",
        "Small Value",
    ]

    value_bets = value_df[
        value_df["ValueRating"].isin(keep_ratings)
    ].copy()

    return value_bets.sort_values(
        by=[
            "ValueScore",
            "ValueEdge",
            "ModelProbability",
        ],
        ascending=[
            False,
            False,
            False,
        ]
    ).reset_index(drop=True)


def build_summary(value_df, value_bets_df):
    return pd.DataFrame(
        [
            {
                "Metric": "Total Market Rows",
                "Value": len(value_df),
            },
            {
                "Metric": "Value Bets",
                "Value": len(value_bets_df),
            },
            {
                "Metric": "Strong Value Bets",
                "Value": int(
                    (
                        value_bets_df["ValueRating"] == "Strong Value"
                    ).sum()
                )
                if not value_bets_df.empty
                else 0,
            },
            {
                "Metric": "Medium Value Bets",
                "Value": int(
                    (
                        value_bets_df["ValueRating"] == "Medium Value"
                    ).sum()
                )
                if not value_bets_df.empty
                else 0,
            },
            {
                "Metric": "Generated At",
                "Value": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            },
        ]
    )


def build_rating_summary(value_df):
    if value_df.empty:
        return pd.DataFrame()

    return (
        value_df
        .groupby("ValueRating", dropna=False)
        .agg(
            Markets=("ValueRating", "count"),
            AvgEdge=("ValueEdge", "mean"),
            AvgScore=("ValueScore", "mean"),
        )
        .reset_index()
        .round(4)
    )


def build_league_summary(value_bets_df):
    if value_bets_df.empty:
        return pd.DataFrame()

    return (
        value_bets_df
        .groupby(
            [
                "Tier",
                "Country",
                "League",
            ],
            dropna=False
        )
        .agg(
            ValueBets=("League", "count"),
            AvgEdge=("ValueEdge", "mean"),
            AvgScore=("ValueScore", "mean"),
            StrongValueBets=(
                "ValueRating",
                lambda x: (x == "Strong Value").sum()
            ),
        )
        .reset_index()
        .round(4)
    )


# =========================================================
# EXPORT
# =========================================================

def export_value_bets():
    ensure_directories()

    predictions_df = safe_read_excel(
        FIXTURE_PREDICTIONS_FILE,
        "Fixture_Predictions"
    )

    if predictions_df.empty:
        print("No fixture predictions found.")
        return pd.DataFrame()

    value_df = build_market_rows(
        predictions_df
    )

    value_bets_df = build_value_bets(
        value_df
    )

    summary_df = build_summary(
        value_df,
        value_bets_df
    )

    rating_summary_df = build_rating_summary(
        value_df
    )

    league_summary_df = build_league_summary(
        value_bets_df
    )

    value_bets_df.to_csv(
        OUTPUT_CSV,
        index=False
    )

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:

        value_bets_df.to_excel(
            writer,
            sheet_name="Value_Bets",
            index=False
        )

        value_df.to_excel(
            writer,
            sheet_name="All_Market_Edges",
            index=False
        )

        summary_df.to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

        rating_summary_df.to_excel(
            writer,
            sheet_name="Rating_Summary",
            index=False
        )

        league_summary_df.to_excel(
            writer,
            sheet_name="League_Summary",
            index=False
        )

    print("\n======================================")
    print("FOOTBALL VALUE BETS EXPORTED")
    print("======================================")
    print(f"Market rows: {len(value_df)}")
    print(f"Value bets : {len(value_bets_df)}")
    print(f"Excel      : {OUTPUT_FILE}")
    print(f"CSV        : {OUTPUT_CSV}")
    print("======================================\n")

    return value_bets_df


def main():
    export_value_bets()


if __name__ == "__main__":
    main()