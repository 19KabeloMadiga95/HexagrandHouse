from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

PREDICTIONS_DIR = (
    BASE_DIR
    / "data"
    / "exports"
    / "predictions"
)

OPTIMIZATION_DIR = (
    BASE_DIR
    / "data"
    / "exports"
    / "optimization"
)

BACKTEST_DIR = (
    BASE_DIR
    / "data"
    / "exports"
    / "backtesting"
)

EXPORT_DIR = (
    BASE_DIR
    / "data"
    / "exports"
    / "final_predictions"
)

UNIFIED_DASHBOARD_FILE = (
    BACKTEST_DIR
    / "unified_model_performance_dashboard.xlsx"
)


# =========================================================
# GAME CONFIGS
# =========================================================

GAME_CONFIGS = {
    "PowerBall": {
        "game_family": "PowerBall",
        "draw_type": None,
        "prediction_file": PREDICTIONS_DIR / "powerball_predictions.xlsx",
        "prediction_sheet": "PowerBall_Predictions",
        "optimizer_file": OPTIMIZATION_DIR / "powerball_genetic_optimizer_results.xlsx",
        "regular_cols": ["N1", "N2", "N3", "N4", "N5"],
        "bonus_col": "Bonus",
        "output_file": EXPORT_DIR / "powerball_ensemble_predictions.xlsx",
    },

    "Lotto": {
        "game_family": "Lotto",
        "draw_type": None,
        "prediction_file": PREDICTIONS_DIR / "lotto_predictions.xlsx",
        "prediction_sheet": "Lotto_Predictions",
        "optimizer_file": OPTIMIZATION_DIR / "lotto_genetic_optimizer_results.xlsx",
        "regular_cols": ["N1", "N2", "N3", "N4", "N5", "N6"],
        "bonus_col": "Bonus",
        "output_file": EXPORT_DIR / "lotto_ensemble_predictions.xlsx",
    },

    "Daily Lotto": {
        "game_family": "Daily Lotto",
        "draw_type": None,
        "prediction_file": PREDICTIONS_DIR / "daily_lotto_predictions.xlsx",
        "prediction_sheet": "Daily_Lotto_Predictions",
        "optimizer_file": OPTIMIZATION_DIR / "daily_lotto_genetic_optimizer_results.xlsx",
        "regular_cols": ["N1", "N2", "N3", "N4", "N5"],
        "bonus_col": None,
        "output_file": EXPORT_DIR / "daily_lotto_ensemble_predictions.xlsx",
    },

    "UK49s Lunchtime": {
        "game_family": "UK49s",
        "draw_type": "Lunchtime",
        "prediction_file": PREDICTIONS_DIR / "uk49s_predictions.xlsx",
        "prediction_sheet": "UK49s_Predictions",
        "optimizer_file": OPTIMIZATION_DIR / "uk49s_genetic_optimizer_results.xlsx",
        "regular_cols": ["N1", "N2", "N3", "N4", "N5", "N6"],
        "bonus_col": "Bonus",
        "output_file": EXPORT_DIR / "uk49s_lunchtime_ensemble_predictions.xlsx",
    },

    "UK49s Teatime": {
        "game_family": "UK49s",
        "draw_type": "Teatime",
        "prediction_file": PREDICTIONS_DIR / "uk49s_predictions.xlsx",
        "prediction_sheet": "UK49s_Predictions",
        "optimizer_file": OPTIMIZATION_DIR / "uk49s_genetic_optimizer_results.xlsx",
        "regular_cols": ["N1", "N2", "N3", "N4", "N5", "N6"],
        "bonus_col": "Bonus",
        "output_file": EXPORT_DIR / "uk49s_teatime_ensemble_predictions.xlsx",
    },
}


# =========================================================
# HELPERS
# =========================================================

def safe_read_excel(path, sheet_name=0):
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


def clean_text(value):
    if value is None or pd.isna(value):
        return ""

    value = str(value).strip()

    if value.lower() in [
        "nan",
        "none",
        "nat",
    ]:
        return ""

    return value


def normalise_01(series):
    series = pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0)

    min_value = series.min()
    max_value = series.max()

    if max_value <= min_value:
        return pd.Series(
            0.5,
            index=series.index
        )

    return (
        series - min_value
    ) / (
        max_value - min_value
    )


def build_game_display(game_family, draw_type=None):
    game_family = clean_text(game_family)
    draw_type = clean_text(draw_type)

    if game_family == "UK49s" and draw_type:
        return f"UK49s {draw_type}"

    return game_family


def apply_game_metadata(df, game_name, config):
    if df.empty:
        return df

    df = df.copy()

    game_family = config.get(
        "game_family",
        game_name
    )

    draw_type = config.get(
        "draw_type"
    )

    df["GameFamily"] = game_family

    if draw_type:
        df["DrawType"] = draw_type
    elif "DrawType" not in df.columns:
        df["DrawType"] = None

    df["GameDisplay"] = df.apply(
        lambda row: build_game_display(
            row.get("GameFamily"),
            row.get("DrawType")
        ),
        axis=1
    )

    return df


def filter_source_by_draw_type(df, config):
    if df.empty:
        return df

    draw_type = config.get(
        "draw_type"
    )

    if not draw_type:
        return df

    df = df.copy()

    if "DrawType" in df.columns:
        filtered = df[
            df["DrawType"].astype(str).str.strip().str.lower()
            == draw_type.lower()
        ].copy()

        if not filtered.empty:
            return filtered

    return df


def build_combo_key(row, regular_cols, bonus_col=None):
    regulars = []

    for col in regular_cols:
        if col in row and pd.notna(row[col]):
            regulars.append(
                int(row[col])
            )

    regulars = sorted(
        regulars
    )

    if bonus_col and bonus_col in row and pd.notna(row[bonus_col]):
        bonus = int(
            row[bonus_col]
        )

        return "|".join(
            map(str, regulars + [bonus])
        )

    return "|".join(
        map(str, regulars)
    )


def count_overlap(key_a, key_b, has_bonus=True):
    a = [
        int(x)
        for x in str(key_a).split("|")
        if str(x).strip() != ""
    ]

    b = [
        int(x)
        for x in str(key_b).split("|")
        if str(x).strip() != ""
    ]

    if has_bonus:
        a_regulars = set(a[:-1])
        b_regulars = set(b[:-1])
    else:
        a_regulars = set(a)
        b_regulars = set(b)

    return len(
        a_regulars.intersection(
            b_regulars
        )
    )


def add_common_features(df, regular_cols):
    df = df.copy()

    for col in regular_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    available_regular_cols = [
        col for col in regular_cols
        if col in df.columns
    ]

    df["RegularSum"] = df[
        available_regular_cols
    ].sum(
        axis=1
    )

    df["OddCount"] = df[
        available_regular_cols
    ].apply(
        lambda row: sum(
            1 for x in row
            if pd.notna(x) and int(x) % 2 != 0
        ),
        axis=1
    )

    df["EvenCount"] = len(
        available_regular_cols
    ) - df["OddCount"]

    df["NumberSpread"] = (
        df[available_regular_cols].max(axis=1)
        - df[available_regular_cols].min(axis=1)
    )

    return df


# =========================================================
# MODEL LEADERBOARD WEIGHTS
# =========================================================

def load_game_model_weight(game_name, config):
    leaderboard = safe_read_excel(
        UNIFIED_DASHBOARD_FILE,
        "Unified_Leaderboard"
    )

    if leaderboard.empty:
        return 1.0

    leaderboard = leaderboard.copy()

    game_family = config.get(
        "game_family",
        game_name
    )

    draw_type = config.get(
        "draw_type"
    )

    if "GameFamily" in leaderboard.columns:
        leaderboard = leaderboard[
            leaderboard["GameFamily"].astype(str) == game_family
        ].copy()

    if draw_type and "DrawType" in leaderboard.columns:
        filtered = leaderboard[
            leaderboard["DrawType"].astype(str).str.strip().str.lower()
            == draw_type.lower()
        ].copy()

        if not filtered.empty:
            leaderboard = filtered

    if leaderboard.empty:
        return 1.0

    if "AverageBestRegularMatch_PerDraw" not in leaderboard.columns:
        return 1.0

    leaderboard[
        "AverageBestRegularMatch_PerDraw"
    ] = pd.to_numeric(
        leaderboard[
            "AverageBestRegularMatch_PerDraw"
        ],
        errors="coerce"
    )

    best_score = leaderboard[
        "AverageBestRegularMatch_PerDraw"
    ].max()

    if pd.isna(best_score):
        return 1.0

    return float(
        best_score
    )


# =========================================================
# LOAD SOURCES
# =========================================================

def load_prediction_source(game_name, config):
    df = safe_read_excel(
        config["prediction_file"],
        config["prediction_sheet"]
    )

    if df.empty:
        return pd.DataFrame()

    df = filter_source_by_draw_type(
        df,
        config
    )

    df = apply_game_metadata(
        df,
        game_name,
        config
    )

    df["SourceType"] = "PredictionModel"

    df["SourceRank"] = (
        df.index + 1
    )

    return df


def load_optimizer_source(game_name, config):
    df = safe_read_excel(
        config["optimizer_file"],
        "Optimized_Numbers"
    )

    if df.empty:
        return pd.DataFrame()

    df = filter_source_by_draw_type(
        df,
        config
    )

    df = apply_game_metadata(
        df,
        game_name,
        config
    )

    df["SourceType"] = "GeneticOptimizer"

    if "Rank" in df.columns:
        df["SourceRank"] = pd.to_numeric(
            df["Rank"],
            errors="coerce"
        )

        df["SourceRank"] = df["SourceRank"].where(
            df["SourceRank"].notna(),
            pd.Series(
                df.index + 1,
                index=df.index
            )
        )

    else:
        df["SourceRank"] = (
            df.index + 1
        )

    return df


def combine_sources(game_name, config):
    prediction_df = load_prediction_source(
        game_name,
        config
    )

    optimizer_df = load_optimizer_source(
        game_name,
        config
    )

    frames = [
        df for df in [
            prediction_df,
            optimizer_df
        ]
        if not df.empty
    ]

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(
        frames,
        ignore_index=True
    )

    regular_cols = config["regular_cols"]
    bonus_col = config["bonus_col"]

    combined = add_common_features(
        combined,
        regular_cols
    )

    combined["ComboKey"] = combined.apply(
        lambda row: build_combo_key(
            row,
            regular_cols,
            bonus_col
        ),
        axis=1
    )

    combined = apply_game_metadata(
        combined,
        game_name,
        config
    )

    return combined


# =========================================================
# ENSEMBLE SCORING
# =========================================================

def score_ensemble(game_name, config):
    df = combine_sources(
        game_name,
        config
    )

    if df.empty:
        return pd.DataFrame()

    regular_cols = config["regular_cols"]
    bonus_col = config["bonus_col"]

    model_weight = load_game_model_weight(
        game_name,
        config
    )

    df["SourceRank"] = pd.to_numeric(
        df["SourceRank"],
        errors="coerce"
    ).fillna(
        len(df)
    )

    df["RankScore"] = 1 / (
        df["SourceRank"] + 1
    )

    if "FitnessScore" in df.columns:
        df["FitnessScore_Norm"] = normalise_01(
            df["FitnessScore"]
        )
    else:
        df["FitnessScore_Norm"] = 0.5

    if "PredictionScore" in df.columns:
        df["PredictionScore_Norm"] = normalise_01(
            df["PredictionScore"]
        )

    elif "ModelRawScore" in df.columns:
        df["PredictionScore_Norm"] = normalise_01(
            df["ModelRawScore"]
        )

    else:
        df["PredictionScore_Norm"] = 0.5

    source_weights = {
        "PredictionModel": 0.45,
        "GeneticOptimizer": 0.55,
    }

    df["SourceWeight"] = df[
        "SourceType"
    ].map(
        source_weights
    ).fillna(
        0.40
    )

    agreement = (
        df
        .groupby("ComboKey")
        .agg(
            SourceCount=("SourceType", "nunique"),
            DuplicateCount=("ComboKey", "count"),
        )
        .reset_index()
    )

    df = df.merge(
        agreement,
        on="ComboKey",
        how="left"
    )

    df["AgreementScore"] = normalise_01(
        df["SourceCount"]
        + df["DuplicateCount"]
    )

    df["BaseEnsembleScore"] = (
        df["SourceWeight"] * 30
        + df["RankScore"] * 30
        + df["FitnessScore_Norm"] * 20
        + df["PredictionScore_Norm"] * 15
        + df["AgreementScore"] * 10
        + model_weight
    )

    df["PatternBalanceScore"] = 0

    regular_count = len(
        regular_cols
    )

    if regular_count == 5:
        balanced_odd_even = df["OddCount"].isin(
            [2, 3]
        )
    else:
        balanced_odd_even = df["OddCount"].isin(
            [2, 3, 4]
        )

    df.loc[
        balanced_odd_even,
        "PatternBalanceScore"
    ] += 5

    spread_median = df[
        "NumberSpread"
    ].median()

    df.loc[
        df["NumberSpread"] >= spread_median,
        "PatternBalanceScore"
    ] += 3

    df["EnsembleScore"] = (
        df["BaseEnsembleScore"]
        + df["PatternBalanceScore"]
    )

    grouped = (
        df
        .sort_values(
            by="EnsembleScore",
            ascending=False
        )
        .groupby("ComboKey")
        .head(1)
        .reset_index(drop=True)
    )

    grouped = grouped.sort_values(
        by="EnsembleScore",
        ascending=False
    ).reset_index(drop=True)

    final_rows = []
    selected_keys = []

    has_bonus = bonus_col is not None

    max_overlap_allowed = (
        3 if len(regular_cols) == 5 else 4
    )

    for _, row in grouped.iterrows():
        current_key = row["ComboKey"]

        too_similar = False

        for selected_key in selected_keys:
            overlap = count_overlap(
                current_key,
                selected_key,
                has_bonus=has_bonus
            )

            if overlap > max_overlap_allowed:
                too_similar = True
                break

        if too_similar:
            continue

        selected_keys.append(
            current_key
        )

        final_rows.append(
            row
        )

        if len(final_rows) >= 20:
            break

    if not final_rows:
        final_df = grouped.head(20).copy()
    else:
        final_df = pd.DataFrame(final_rows)

    final_df = final_df.reset_index(
        drop=True
    )

    final_df["EnsembleRank"] = (
        final_df.index + 1
    )

    final_df["PredictionRank"] = final_df["EnsembleRank"]

    final_df["GeneratedAt"] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    final_df = apply_game_metadata(
        final_df,
        game_name,
        config
    )

    output_cols = [
        "EnsembleRank",
        "PredictionRank",
        "GameDisplay",
        "GameFamily",
        "DrawType",
        "SourceType",
        "SourceRank",
    ]

    output_cols += [
        col for col in regular_cols
        if col in final_df.columns
    ]

    if bonus_col and bonus_col in final_df.columns:
        output_cols.append(
            bonus_col
        )

    output_cols += [
        "RegularSum",
        "OddCount",
        "EvenCount",
        "NumberSpread",
        "SourceCount",
        "DuplicateCount",
        "RankScore",
        "FitnessScore_Norm",
        "PredictionScore_Norm",
        "AgreementScore",
        "PatternBalanceScore",
        "EnsembleScore",
        "ComboKey",
        "GeneratedAt",
    ]

    output_cols = [
        col for col in output_cols
        if col in final_df.columns
    ]

    return final_df[
        output_cols
    ]


# =========================================================
# EXPORT
# =========================================================

def export_game_ensemble(game_name, config):
    EXPORT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    final_df = score_ensemble(
        game_name,
        config
    )

    output_file = config[
        "output_file"
    ]

    with pd.ExcelWriter(
        output_file,
        engine="openpyxl",
        mode="w"
    ) as writer:
        final_df.to_excel(
            writer,
            sheet_name="Final_Ensemble",
            index=False
        )

    print("\n======================================")
    print(f"{game_name.upper()} ENSEMBLE EXPORTED")
    print("======================================")
    print(f"Rows: {len(final_df)}")
    print(f"File: {output_file}")
    print("======================================\n")

    return final_df


def export_all_game_ensembles():
    results = {}

    for game_name, config in GAME_CONFIGS.items():
        result = export_game_ensemble(
            game_name,
            config
        )

        results[
            game_name
        ] = result

    combined = []

    for game_name, df in results.items():
        if not df.empty:
            combined.append(df)

    if combined:
        combined_df = pd.concat(
            combined,
            ignore_index=True
        )
    else:
        combined_df = pd.DataFrame()

    combined_file = (
        EXPORT_DIR
        / "all_games_ensemble_predictions.xlsx"
    )

    with pd.ExcelWriter(
        combined_file,
        engine="openpyxl",
        mode="w"
    ) as writer:
        combined_df.to_excel(
            writer,
            sheet_name="All_Ensemble_Predictions",
            index=False
        )

    print("\n======================================")
    print("ALL GAME ENSEMBLES EXPORTED")
    print("======================================")
    print(f"Rows: {len(combined_df)}")
    print(f"File: {combined_file}")
    print("======================================\n")

    return results


# =========================================================
# CLI
# =========================================================

def main():
    export_all_game_ensembles()


if __name__ == "__main__":
    main()