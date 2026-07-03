from __future__ import annotations

from pathlib import Path
from datetime import datetime
import math

import pandas as pd

from src.lottery.config.lottery_game_rules import (
    LotteryGameRule,
    get_current_rule,
    get_regular_range,
    get_bonus_range,
)


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

PREDICTIONS_DIR = BASE_DIR / "data" / "exports" / "predictions"
OPTIMIZATION_DIR = BASE_DIR / "data" / "exports" / "optimization"
BACKTEST_DIR = BASE_DIR / "data" / "exports" / "backtesting"
FINAL_PREDICTIONS_DIR = BASE_DIR / "data" / "exports" / "final_predictions"

UNIFIED_DASHBOARD_FILE = (
    BACKTEST_DIR
    / "unified_model_performance_dashboard.xlsx"
)

COMBINED_OUTPUT_FILE = (
    FINAL_PREDICTIONS_DIR
    / "all_games_ensemble_predictions.xlsx"
)


# =========================================================
# GAME CONFIG
# =========================================================

GAME_CONFIGS = {
    "PowerBall": {
        "game_name": "PowerBall",
        "game_family": "PowerBall",
        "draw_type": None,
        "prediction_file": PREDICTIONS_DIR / "powerball_predictions.xlsx",
        "prediction_sheets": ["PowerBall_Predictions", "Predictions", "Sheet1"],
        "optimizer_file": OPTIMIZATION_DIR / "powerball_genetic_optimizer_results.xlsx",
        "optimizer_sheets": ["POWERBALL_Optimized_Numbers", "Optimized_Numbers", "Sheet1"],
        "output_file": FINAL_PREDICTIONS_DIR / "powerball_ensemble_predictions.xlsx",
    },
    "Lotto": {
        "game_name": "Lotto",
        "game_family": "Lotto",
        "draw_type": None,
        "prediction_file": PREDICTIONS_DIR / "lotto_predictions.xlsx",
        "prediction_sheets": ["Lotto_Predictions", "Predictions", "Sheet1"],
        "optimizer_file": OPTIMIZATION_DIR / "lotto_genetic_optimizer_results.xlsx",
        "optimizer_sheets": ["Optimized_Numbers", "LOTTO_Optimized_Numbers", "Sheet1"],
        "output_file": FINAL_PREDICTIONS_DIR / "lotto_ensemble_predictions.xlsx",
    },
    "Daily Lotto": {
        "game_name": "Daily Lotto",
        "game_family": "Daily Lotto",
        "draw_type": None,
        "prediction_file": PREDICTIONS_DIR / "daily_lotto_predictions.xlsx",
        "prediction_sheets": ["Daily_Lotto_Predictions", "Predictions", "Sheet1"],
        "optimizer_file": OPTIMIZATION_DIR / "daily_lotto_genetic_optimizer_results.xlsx",
        "optimizer_sheets": ["Optimized_Numbers", "DAILY_LOTTO_Optimized_Numbers", "Sheet1"],
        "output_file": FINAL_PREDICTIONS_DIR / "daily_lotto_ensemble_predictions.xlsx",
    },
    "UK49s Lunchtime": {
        "game_name": "UK49s Lunchtime",
        "game_family": "UK49s",
        "draw_type": "Lunchtime",
        "prediction_file": PREDICTIONS_DIR / "uk49s_predictions.xlsx",
        "prediction_sheets": ["UK49s_Predictions", "Predictions", "Sheet1"],
        "optimizer_file": OPTIMIZATION_DIR / "uk49s_genetic_optimizer_results.xlsx",
        "optimizer_sheets": ["Optimized_Numbers", "UK49S_Optimized_Numbers", "Sheet1"],
        "output_file": FINAL_PREDICTIONS_DIR / "uk49s_lunchtime_ensemble_predictions.xlsx",
    },
    "UK49s Teatime": {
        "game_name": "UK49s Teatime",
        "game_family": "UK49s",
        "draw_type": "Teatime",
        "prediction_file": PREDICTIONS_DIR / "uk49s_predictions.xlsx",
        "prediction_sheets": ["UK49s_Predictions", "Predictions", "Sheet1"],
        "optimizer_file": OPTIMIZATION_DIR / "uk49s_genetic_optimizer_results.xlsx",
        "optimizer_sheets": ["Optimized_Numbers", "UK49S_Optimized_Numbers", "Sheet1"],
        "output_file": FINAL_PREDICTIONS_DIR / "uk49s_teatime_ensemble_predictions.xlsx",
    },
}

SOURCE_WEIGHTS = {
    "PredictionModel": 0.45,
    "GeneticOptimizer": 0.55,
}

FINAL_ROWS_PER_GAME = 20


# =========================================================
# BASIC HELPERS
# =========================================================

def clean_text(value) -> str:
    if value is None or pd.isna(value):
        return ""

    value = str(value).strip()

    if value.lower() in {"nan", "none", "nat"}:
        return ""

    return value


def safe_read_excel(path: Path, preferred_sheets: list[str]) -> pd.DataFrame:
    if not path.exists():
        print(f"Missing optional source: {path}")
        return pd.DataFrame()

    try:
        workbook = pd.ExcelFile(path, engine="openpyxl")

        for sheet in preferred_sheets:
            if sheet in workbook.sheet_names:
                return pd.read_excel(workbook, sheet_name=sheet)

        return pd.read_excel(workbook, sheet_name=workbook.sheet_names[0])

    except Exception as exc:
        print(f"Could not read: {path}")
        print(f"Error: {exc}")
        return pd.DataFrame()


def normalise_01(series) -> pd.Series:
    series = pd.to_numeric(pd.Series(series), errors="coerce").fillna(0)

    if series.empty:
        return pd.Series(dtype=float)

    min_value = series.min()
    max_value = series.max()

    if max_value <= min_value:
        return pd.Series(0.5, index=series.index)

    return (series - min_value) / (max_value - min_value)


def build_game_display(game_family: str, draw_type: str | None = None) -> str:
    game_family = clean_text(game_family)
    draw_type = clean_text(draw_type)

    if game_family == "UK49s" and draw_type:
        return f"UK49s {draw_type}"

    return game_family


def get_rule(game_name: str) -> LotteryGameRule:
    rule = get_current_rule(game_name)

    if rule is None:
        raise ValueError(f"No lottery rules found for: {game_name}")

    return rule


def get_regular_cols(rule: LotteryGameRule) -> list[str]:
    return [f"N{i}" for i in range(1, rule.regular_pick_count + 1)]


def has_bonus(rule: LotteryGameRule) -> bool:
    return get_bonus_range(rule) is not None and rule.bonus_pick_count > 0


def filter_by_draw_type(df: pd.DataFrame, draw_type: str | None) -> pd.DataFrame:
    if df.empty or not draw_type:
        return df

    if "DrawType" not in df.columns:
        return df

    filtered = df[
        df["DrawType"].astype(str).str.strip().str.lower()
        == draw_type.lower()
    ].copy()

    return filtered if not filtered.empty else df


def apply_game_metadata(
    df: pd.DataFrame,
    game_name: str,
    game_family: str,
    draw_type: str | None,
) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    df["GameName"] = game_name
    df["GameFamily"] = game_family
    df["DrawType"] = draw_type
    df["GameDisplay"] = build_game_display(game_family, draw_type)

    return df


def coerce_number_columns(df: pd.DataFrame, regular_cols: list[str], bonus_col: str | None) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    columns = regular_cols[:]

    if bonus_col and bonus_col in df.columns:
        columns.append(bonus_col)

    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def build_combo_key(row, regular_cols: list[str], bonus_col: str | None) -> str:
    regulars = []

    for col in regular_cols:
        if col in row and pd.notna(row[col]):
            regulars.append(int(row[col]))

    regulars = sorted(regulars)

    if bonus_col and bonus_col in row and pd.notna(row[bonus_col]):
        return "|".join(map(str, regulars + [int(row[bonus_col])]))

    return "|".join(map(str, regulars))


def count_overlap(key_a: str, key_b: str, includes_bonus: bool) -> int:
    values_a = [int(x) for x in str(key_a).split("|") if clean_text(x)]
    values_b = [int(x) for x in str(key_b).split("|") if clean_text(x)]

    if includes_bonus:
        values_a = values_a[:-1]
        values_b = values_b[:-1]

    return len(set(values_a).intersection(set(values_b)))


def rank_score_from_column(df: pd.DataFrame) -> pd.Series:
    rank_col = None

    for col in ["EnsembleRank", "PredictionRank", "Rank", "SourceRank"]:
        if col in df.columns:
            rank_col = col
            break

    if rank_col is None:
        return pd.Series(0.5, index=df.index)

    ranks = pd.to_numeric(df[rank_col], errors="coerce").fillna(len(df) + 1)

    return normalise_01(1 / (ranks + 1))


def score_column(df: pd.DataFrame) -> pd.Series:
    score_cols = [
        "EnsembleScore",
        "Confidence",
        "ConfidenceScore",
        "RawScore",
        "ModelRawScore",
        "FitnessScore",
        "GeneticFitnessScore",
        "PredictionScore",
    ]

    available = [col for col in score_cols if col in df.columns]

    if not available:
        return pd.Series(0.5, index=df.index)

    combined = pd.Series(0.0, index=df.index)

    for col in available:
        combined += normalise_01(df[col])

    return normalise_01(combined)


# =========================================================
# LOAD SOURCES
# =========================================================

def load_prediction_source(game_name: str, config: dict, rule: LotteryGameRule) -> pd.DataFrame:
    df = safe_read_excel(
        config["prediction_file"],
        config["prediction_sheets"],
    )

    if df.empty:
        return df

    df = filter_by_draw_type(df, config.get("draw_type"))
    df = apply_game_metadata(
        df,
        game_name=config["game_name"],
        game_family=config["game_family"],
        draw_type=config.get("draw_type"),
    )

    df["SourceType"] = "PredictionModel"
    df["SourceWeight"] = SOURCE_WEIGHTS["PredictionModel"]

    if "SourceRank" not in df.columns:
        if "PredictionRank" in df.columns:
            df["SourceRank"] = df["PredictionRank"]
        else:
            df["SourceRank"] = df.index + 1

    regular_cols = get_regular_cols(rule)
    bonus_col = "Bonus" if has_bonus(rule) else None

    return coerce_number_columns(df, regular_cols, bonus_col)


def load_optimizer_source(game_name: str, config: dict, rule: LotteryGameRule) -> pd.DataFrame:
    df = safe_read_excel(
        config["optimizer_file"],
        config["optimizer_sheets"],
    )

    if df.empty:
        return df

    df = filter_by_draw_type(df, config.get("draw_type"))
    df = apply_game_metadata(
        df,
        game_name=config["game_name"],
        game_family=config["game_family"],
        draw_type=config.get("draw_type"),
    )

    df["SourceType"] = "GeneticOptimizer"
    df["SourceWeight"] = SOURCE_WEIGHTS["GeneticOptimizer"]

    if "SourceRank" not in df.columns:
        if "Rank" in df.columns:
            df["SourceRank"] = df["Rank"]
        else:
            df["SourceRank"] = df.index + 1

    regular_cols = get_regular_cols(rule)
    bonus_col = "Bonus" if has_bonus(rule) else None

    return coerce_number_columns(df, regular_cols, bonus_col)


def combine_sources(game_name: str, config: dict, rule: LotteryGameRule) -> pd.DataFrame:
    prediction_df = load_prediction_source(game_name, config, rule)
    optimizer_df = load_optimizer_source(game_name, config, rule)

    frames = [df for df in [prediction_df, optimizer_df] if not df.empty]

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True, sort=False)

    regular_cols = get_regular_cols(rule)
    bonus_col = "Bonus" if has_bonus(rule) else None

    existing_regular_cols = [col for col in regular_cols if col in df.columns]

    if len(existing_regular_cols) < rule.regular_pick_count:
        return pd.DataFrame()

    df = df.dropna(subset=existing_regular_cols)

    # Keep final predictions legal under the current rule.
    for col in existing_regular_cols:
        df = df[
            (pd.to_numeric(df[col], errors="coerce") >= rule.regular_min)
            & (pd.to_numeric(df[col], errors="coerce") <= rule.regular_max)
        ].copy()

    if bonus_col:
        if bonus_col not in df.columns:
            return pd.DataFrame()

        bonus_range = get_bonus_range(rule)
        bonus_min = min(bonus_range)
        bonus_max = max(bonus_range)

        df = df[
            (pd.to_numeric(df[bonus_col], errors="coerce") >= bonus_min)
            & (pd.to_numeric(df[bonus_col], errors="coerce") <= bonus_max)
        ].copy()

    if df.empty:
        return df

    df["ComboKey"] = df.apply(
        lambda row: build_combo_key(row, regular_cols, bonus_col),
        axis=1,
    )

    return df


# =========================================================
# SCORING
# =========================================================

def score_ensemble(game_name: str, config: dict) -> pd.DataFrame:
    rule = get_rule(config["game_name"])
    df = combine_sources(game_name, config, rule)

    if df.empty:
        return pd.DataFrame()

    df = df.copy()

    df["RankScore"] = rank_score_from_column(df)
    df["SignalScore"] = score_column(df)
    df["SourceWeight"] = pd.to_numeric(df["SourceWeight"], errors="coerce").fillna(0.4)

    agreement = (
        df
        .groupby("ComboKey", dropna=False)
        .agg(
            SourceCount=("SourceType", "nunique"),
            DuplicateCount=("ComboKey", "count"),
        )
        .reset_index()
    )

    df = df.merge(agreement, on="ComboKey", how="left")

    df["AgreementScore"] = normalise_01(
        pd.to_numeric(df["SourceCount"], errors="coerce").fillna(0)
        + pd.to_numeric(df["DuplicateCount"], errors="coerce").fillna(0)
    )

    df["EnsembleScore"] = (
        df["SourceWeight"] * 35
        + df["RankScore"] * 25
        + df["SignalScore"] * 25
        + df["AgreementScore"] * 15
    ).round(4)

    df = (
        df
        .sort_values(
            by=["ComboKey", "EnsembleScore"],
            ascending=[True, False],
        )
        .groupby("ComboKey", as_index=False)
        .head(1)
        .reset_index(drop=True)
    )

    df = df.sort_values(
        by="EnsembleScore",
        ascending=False,
    ).reset_index(drop=True)

    return apply_diversity_filter(df, rule)


def apply_diversity_filter(df: pd.DataFrame, rule: LotteryGameRule) -> pd.DataFrame:
    if df.empty:
        return df

    selected_rows = []
    selected_keys = []
    includes_bonus = has_bonus(rule)
    max_overlap = max(rule.regular_pick_count - 2, 2)

    for _, row in df.iterrows():
        key = row["ComboKey"]

        too_similar = False

        for selected_key in selected_keys:
            if count_overlap(key, selected_key, includes_bonus) > max_overlap:
                too_similar = True
                break

        if too_similar:
            continue

        selected_keys.append(key)
        selected_rows.append(row)

        if len(selected_rows) >= FINAL_ROWS_PER_GAME:
            break

    if not selected_rows:
        final_df = df.head(FINAL_ROWS_PER_GAME).copy()
    else:
        final_df = pd.DataFrame(selected_rows).copy()

    final_df = final_df.reset_index(drop=True)
    final_df["EnsembleRank"] = final_df.index + 1
    final_df["PredictionRank"] = final_df["EnsembleRank"]
    final_df["GeneratedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_df["RuleVersion"] = rule.rule_version

    return select_output_columns(final_df, rule)


def select_output_columns(df: pd.DataFrame, rule: LotteryGameRule) -> pd.DataFrame:
    regular_cols = get_regular_cols(rule)
    bonus_col = "Bonus" if has_bonus(rule) else None

    output_cols = [
        "EnsembleRank",
        "PredictionRank",
        "GameDisplay",
        "GameFamily",
        "GameName",
        "DrawType",
    ]

    output_cols.extend([col for col in regular_cols if col in df.columns])

    if bonus_col and bonus_col in df.columns:
        output_cols.append(bonus_col)

    output_cols.extend([
        "SourceType",
        "SourceRank",
        "SourceCount",
        "DuplicateCount",
        "RankScore",
        "SignalScore",
        "AgreementScore",
        "EnsembleScore",
        "ComboKey",
        "RuleVersion",
        "GeneratedAt",
    ])

    output_cols = [col for col in output_cols if col in df.columns]

    return df[output_cols]


# =========================================================
# EXPORT
# =========================================================

def export_game_ensemble(game_name: str, config: dict) -> pd.DataFrame:
    FINAL_PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

    final_df = score_ensemble(game_name, config)
    output_file = config["output_file"]

    with pd.ExcelWriter(output_file, engine="openpyxl", mode="w") as writer:
        final_df.to_excel(
            writer,
            sheet_name="Ensemble_Predictions",
            index=False,
        )

    print(f"\n{game_name.upper()} ENSEMBLE EXPORTED")
    print(f"Rows: {len(final_df)}")
    print(f"File: {output_file}")

    return final_df


def export_ensemble_predictions() -> pd.DataFrame:
    print("\n======================================")
    print("ALL-GAME LOTTERY ENSEMBLE ENGINE")
    print("======================================")

    results = {}
    combined_frames = []

    for game_name, config in GAME_CONFIGS.items():
        try:
            result_df = export_game_ensemble(game_name, config)
            results[game_name] = result_df

            if not result_df.empty:
                combined_frames.append(result_df)

        except Exception as exc:
            print(f"\n{game_name.upper()} ENSEMBLE FAILED")
            print(f"Error: {exc}")
            results[game_name] = pd.DataFrame()

    if combined_frames:
        combined_df = pd.concat(combined_frames, ignore_index=True, sort=False)
    else:
        combined_df = pd.DataFrame()

    FINAL_PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(COMBINED_OUTPUT_FILE, engine="openpyxl", mode="w") as writer:
        combined_df.to_excel(
            writer,
            sheet_name="All_Ensemble_Predictions",
            index=False,
        )

        summary_df = pd.DataFrame(
            [
                {
                    "GameName": game_name,
                    "Rows": len(df),
                    "Status": "Success" if not df.empty else "No Rows",
                }
                for game_name, df in results.items()
            ]
        )

        summary_df.to_excel(
            writer,
            sheet_name="Summary",
            index=False,
        )

    print("\n======================================")
    print("ALL-GAME ENSEMBLE EXPORT COMPLETE")
    print("======================================")
    print(f"Rows: {len(combined_df)}")
    print(f"File: {COMBINED_OUTPUT_FILE}")
    print("======================================\n")

    return combined_df


def export_all_game_ensembles() -> pd.DataFrame:
    """
    Backward-compatible alias for older automation scripts.
    """

    return export_ensemble_predictions()


def main():
    export_ensemble_predictions()


if __name__ == "__main__":
    main()
