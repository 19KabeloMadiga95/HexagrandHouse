from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from itertools import combinations
from typing import Iterable

import numpy as np
import pandas as pd

from src.data.sqlite_store import (
    create_indexes,
    read_sqlite_table,
    replace_sqlite_table,
)
from src.lottery.config.lottery_game_rules import (
    LotteryGameRule,
    get_current_rule,
    get_low_high_split,
)


# =========================================================
# SQLITE-FIRST LOTTERY PREDICTION ENGINE
# =========================================================

MODEL_NAME = "SQLite Weighted Ensemble"
MODEL_VERSION = "SQLiteRuntime_v1"
DEFAULT_SIMULATION_COUNT = 6500
DEFAULT_TOP_N = 10
RECENCY_DECAY = 0.985

REGULAR_COLUMNS = ["N1", "N2", "N3", "N4", "N5", "N6"]
BONUS_COLUMN = "Bonus"


@dataclass(frozen=True)
class GamePredictionConfig:
    game_name: str
    feature_table: str
    output_table: str
    top_n: int = DEFAULT_TOP_N
    simulation_count: int = DEFAULT_SIMULATION_COUNT


GAME_CONFIGS: dict[str, list[GamePredictionConfig]] = {
    "powerball": [
        GamePredictionConfig(
            game_name="PowerBall",
            feature_table="lottery_powerball_features",
            output_table="lottery_powerball_predictions",
        ),
        GamePredictionConfig(
            game_name="PowerBall Plus",
            feature_table="lottery_powerball_features",
            output_table="lottery_powerball_predictions",
        ),
    ],
    "lotto": [
        GamePredictionConfig(
            game_name="Lotto",
            feature_table="lottery_lotto_features",
            output_table="lottery_lotto_predictions",
        ),
        GamePredictionConfig(
            game_name="Lotto Plus 1",
            feature_table="lottery_lotto_features",
            output_table="lottery_lotto_predictions",
        ),
        GamePredictionConfig(
            game_name="Lotto Plus 2",
            feature_table="lottery_lotto_features",
            output_table="lottery_lotto_predictions",
        ),
    ],
    "daily_lotto": [
        GamePredictionConfig(
            game_name="Daily Lotto",
            feature_table="lottery_daily_lotto_features",
            output_table="lottery_daily_lotto_predictions",
        ),
    ],
    "uk49s": [
        GamePredictionConfig(
            game_name="UK49s Lunchtime",
            feature_table="lottery_uk49s_features",
            output_table="lottery_uk49s_predictions",
        ),
        GamePredictionConfig(
            game_name="UK49s Teatime",
            feature_table="lottery_uk49s_features",
            output_table="lottery_uk49s_predictions",
        ),
    ],
}


# =========================================================
# LOAD / CLEAN FEATURES
# =========================================================


def _as_int(value) -> int | None:
    if pd.isna(value):
        return None
    try:
        return int(value)
    except Exception:
        return None


def _safe_numeric(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce")
    return out


def load_feature_table(table_name: str, game_name: str | None = None) -> pd.DataFrame:
    df = read_sqlite_table(table_name)

    if df.empty:
        raise RuntimeError(
            f"SQLite feature table '{table_name}' is empty or missing.\n"
            "Run this first:\n"
            "python -m src.lottery.features.export_lottery_features"
        )

    df = df.copy()

    if "DrawDate" in df.columns:
        df["DrawDate"] = pd.to_datetime(df["DrawDate"], errors="coerce")

    df = _safe_numeric(df, REGULAR_COLUMNS + [BONUS_COLUMN])

    if game_name and "GameName" in df.columns:
        filtered = df[df["GameName"].astype(str).str.strip().str.lower() == game_name.lower()].copy()
        if not filtered.empty:
            df = filtered

    df = df.dropna(subset=["DrawDate"] if "DrawDate" in df.columns else [])

    if "DrawDate" in df.columns:
        df = df.sort_values("DrawDate", ascending=False)

    return df.reset_index(drop=True)


# =========================================================
# NUMBER / PATTERN HELPERS
# =========================================================


def regular_columns_for_rule(rule: LotteryGameRule) -> list[str]:
    return [f"N{i}" for i in range(1, rule.regular_pick_count + 1)]


def get_regular_numbers(row: pd.Series, rule: LotteryGameRule) -> list[int]:
    numbers: list[int] = []

    for column in regular_columns_for_rule(rule):
        number = _as_int(row.get(column))
        if number is not None and rule.regular_min <= number <= rule.regular_max:
            numbers.append(number)

    return sorted(set(numbers))


def get_bonus_number(row: pd.Series, rule: LotteryGameRule) -> int | None:
    if rule.bonus_pick_count <= 0 or rule.bonus_min is None or rule.bonus_max is None:
        return None

    number = _as_int(row.get(BONUS_COLUMN))
    if number is None:
        return None

    if rule.bonus_min <= number <= rule.bonus_max:
        return number

    return None


def count_high_low(numbers: list[int], rule: LotteryGameRule) -> tuple[int, int]:
    lows, highs = get_low_high_split(rule)
    low_count = sum(1 for number in numbers if number in lows)
    high_count = sum(1 for number in numbers if number in highs)
    return high_count, low_count


def count_odd_even(numbers: list[int]) -> tuple[int, int]:
    odd_count = sum(1 for number in numbers if number % 2 != 0)
    even_count = len(numbers) - odd_count
    return odd_count, even_count


def consecutive_pairs(numbers: list[int]) -> int:
    ordered = sorted(numbers)
    return sum(1 for idx in range(len(ordered) - 1) if ordered[idx + 1] - ordered[idx] == 1)


def number_signature(numbers: list[int], bonus: int | None = None) -> str:
    base = "-".join(f"{number:02d}" for number in sorted(numbers))
    if bonus is not None:
        return f"{base}|B{bonus:02d}"
    return base


def _daily_seed(game_name: str) -> int:
    today_seed = int(pd.Timestamp.today().strftime("%Y%m%d"))
    name_seed = sum((idx + 1) * ord(char) for idx, char in enumerate(game_name))
    return today_seed + name_seed


# =========================================================
# SCORING MODEL
# =========================================================


def _build_history(df: pd.DataFrame, rule: LotteryGameRule) -> tuple[list[list[int]], list[int]]:
    historical_sets: list[list[int]] = []
    bonus_numbers: list[int] = []

    for _, row in df.iterrows():
        regulars = get_regular_numbers(row, rule)
        if len(regulars) == rule.regular_pick_count:
            historical_sets.append(regulars)

        bonus = get_bonus_number(row, rule)
        if bonus is not None:
            bonus_numbers.append(bonus)

    return historical_sets, bonus_numbers


def _normalised_counter(counter: Counter, universe: list[int]) -> dict[int, float]:
    if not universe:
        return {}

    values = np.array([counter.get(number, 0) for number in universe], dtype=float)
    lo = float(values.min()) if len(values) else 0.0
    hi = float(values.max()) if len(values) else 0.0

    if hi <= lo:
        return {number: 0.5 for number in universe}

    return {
        number: float((counter.get(number, 0) - lo) / (hi - lo))
        for number in universe
    }


def _recency_scores(history: list[list[int]], universe: list[int]) -> dict[int, float]:
    scores = Counter()

    for age, numbers in enumerate(history):
        weight = RECENCY_DECAY ** age
        for number in numbers:
            scores[number] += weight

    return _normalised_counter(scores, universe)


def _overdue_scores(history: list[list[int]], universe: list[int]) -> dict[int, float]:
    last_seen = {number: len(history) + 1 for number in universe}

    for age, numbers in enumerate(history):
        for number in numbers:
            if last_seen.get(number, len(history) + 1) == len(history) + 1:
                last_seen[number] = age

    values = pd.Series(last_seen, dtype=float)
    lo = float(values.min()) if not values.empty else 0.0
    hi = float(values.max()) if not values.empty else 0.0

    if hi <= lo:
        return {number: 0.5 for number in universe}

    return {number: float((age - lo) / (hi - lo)) for number, age in last_seen.items()}


def _pair_scores(history: list[list[int]]) -> Counter:
    pairs = Counter()
    for numbers in history:
        for pair in combinations(sorted(numbers), 2):
            pairs[pair] += 1
    return pairs


def _number_weights(history: list[list[int]], rule: LotteryGameRule) -> dict[int, float]:
    universe = list(range(rule.regular_min, rule.regular_max + 1))
    freq = Counter(number for numbers in history for number in numbers)
    freq_score = _normalised_counter(freq, universe)
    recency_score = _recency_scores(history, universe)
    overdue_score = _overdue_scores(history, universe)

    recent_numbers = set(number for numbers in history[:8] for number in numbers)

    weights: dict[int, float] = {}
    for number in universe:
        weight = (
            1.00
            + 2.20 * freq_score.get(number, 0.0)
            + 1.35 * recency_score.get(number, 0.0)
            + 1.15 * overdue_score.get(number, 0.0)
        )

        if number in recent_numbers:
            weight *= 0.92

        weights[number] = max(float(weight), 0.05)

    return weights


def _bonus_weights(bonus_numbers: list[int], rule: LotteryGameRule, exclude: set[int] | None = None) -> dict[int, float]:
    if rule.bonus_pick_count <= 0 or rule.bonus_min is None or rule.bonus_max is None:
        return {}

    universe = list(range(rule.bonus_min, rule.bonus_max + 1))
    counter = Counter(bonus_numbers)
    freq_score = _normalised_counter(counter, universe)
    recent_bonus = set(bonus_numbers[:8])
    exclude = exclude or set()

    weights: dict[int, float] = {}
    for number in universe:
        weight = 1.0 + 2.0 * freq_score.get(number, 0.0)
        if number in recent_bonus:
            weight *= 0.94
        if number in exclude and len(universe) > len(exclude):
            weight *= 0.25
        weights[number] = max(float(weight), 0.05)

    return weights


def _weighted_sample(weights: dict[int, float], count: int, rng: np.random.Generator) -> list[int]:
    numbers = np.array(list(weights.keys()), dtype=int)
    raw_weights = np.array([weights[int(number)] for number in numbers], dtype=float)

    if len(numbers) == 0:
        return []

    probabilities = raw_weights / raw_weights.sum() if raw_weights.sum() > 0 else np.ones(len(numbers)) / len(numbers)
    sample = rng.choice(numbers, size=min(count, len(numbers)), replace=False, p=probabilities)
    return sorted(int(number) for number in sample.tolist())


def _target_patterns(history: list[list[int]], rule: LotteryGameRule) -> dict[str, float]:
    if not history:
        return {
            "median_sum": (rule.regular_max * rule.regular_pick_count) / 2,
            "iqr_sum": max(rule.regular_max, 1),
            "median_high": rule.regular_pick_count / 2,
            "median_odd": rule.regular_pick_count / 2,
            "median_spread": rule.regular_max * 0.65,
        }

    sums = []
    highs = []
    odds = []
    spreads = []

    for numbers in history:
        high_count, _ = count_high_low(numbers, rule)
        odd_count, _ = count_odd_even(numbers)
        sums.append(sum(numbers))
        highs.append(high_count)
        odds.append(odd_count)
        spreads.append(max(numbers) - min(numbers))

    sum_series = pd.Series(sums, dtype=float)
    return {
        "median_sum": float(sum_series.median()),
        "iqr_sum": max(float(sum_series.quantile(0.75) - sum_series.quantile(0.25)), 1.0),
        "median_high": float(pd.Series(highs, dtype=float).median()),
        "median_odd": float(pd.Series(odds, dtype=float).median()),
        "median_spread": float(pd.Series(spreads, dtype=float).median()),
    }


def _candidate_score(
    numbers: list[int],
    rule: LotteryGameRule,
    number_weights: dict[int, float],
    pair_counter: Counter,
    targets: dict[str, float],
    historical_exact_sets: set[tuple[int, ...]],
) -> float:
    base_score = float(sum(number_weights.get(number, 1.0) for number in numbers))

    pair_values = [pair_counter.get(pair, 0) for pair in combinations(sorted(numbers), 2)]
    pair_score = float(np.mean(pair_values)) if pair_values else 0.0

    high_count, _ = count_high_low(numbers, rule)
    odd_count, _ = count_odd_even(numbers)
    spread = max(numbers) - min(numbers)
    regular_sum = sum(numbers)

    sum_penalty = abs(regular_sum - targets["median_sum"]) / targets["iqr_sum"]
    high_penalty = abs(high_count - targets["median_high"]) * 0.85
    odd_penalty = abs(odd_count - targets["median_odd"]) * 0.65
    spread_penalty = abs(spread - targets["median_spread"]) / max(rule.regular_max * 0.30, 1)
    consecutive_penalty = consecutive_pairs(numbers) * 0.45

    exact_history_penalty = 7.5 if tuple(sorted(numbers)) in historical_exact_sets else 0.0

    return round(
        base_score
        + 0.20 * pair_score
        - sum_penalty
        - high_penalty
        - odd_penalty
        - spread_penalty
        - consecutive_penalty
        - exact_history_penalty,
        6,
    )


def _diversity_filter(
    candidate_df: pd.DataFrame,
    rule: LotteryGameRule,
    top_n: int,
) -> pd.DataFrame:
    if candidate_df.empty:
        return candidate_df

    max_overlap = max(rule.regular_pick_count - 2, 2)
    selected_rows: list[pd.Series] = []
    selected_sets: list[set[int]] = []

    for _, row in candidate_df.sort_values("RawScore", ascending=False).iterrows():
        numbers = {int(row[col]) for col in regular_columns_for_rule(rule) if pd.notna(row.get(col))}

        if all(len(numbers & existing) <= max_overlap for existing in selected_sets):
            selected_rows.append(row)
            selected_sets.append(numbers)

        if len(selected_rows) >= top_n:
            break

    if len(selected_rows) < top_n:
        for _, row in candidate_df.sort_values("RawScore", ascending=False).iterrows():
            signature = row.get("NumberSet")
            if any(existing.get("NumberSet") == signature for existing in selected_rows):
                continue
            selected_rows.append(row)
            if len(selected_rows) >= top_n:
                break

    return pd.DataFrame(selected_rows).reset_index(drop=True)


# =========================================================
# PUBLIC GENERATION API
# =========================================================


def generate_predictions_for_game(
    game_name: str,
    feature_table: str,
    top_n: int = DEFAULT_TOP_N,
    simulation_count: int = DEFAULT_SIMULATION_COUNT,
) -> pd.DataFrame:
    rule = get_current_rule(game_name)

    if rule is None:
        raise RuntimeError(f"No active lottery rule configured for game: {game_name}")

    features = load_feature_table(feature_table, game_name=game_name)
    history, bonus_history = _build_history(features, rule)

    if not history:
        raise RuntimeError(f"No usable historical feature rows found for game: {game_name}")

    rng = np.random.default_rng(_daily_seed(game_name))
    number_weights = _number_weights(history, rule)
    pair_counter = _pair_scores(history)
    targets = _target_patterns(history, rule)
    historical_exact_sets = {tuple(sorted(numbers)) for numbers in history}

    candidate_rows: list[dict] = []
    seen_signatures: set[str] = set()

    for _ in range(simulation_count):
        numbers = _weighted_sample(number_weights, rule.regular_pick_count, rng)

        if len(numbers) != rule.regular_pick_count:
            continue

        bonus = None
        if rule.bonus_pick_count > 0:
            weights = _bonus_weights(bonus_history, rule, exclude=set(numbers))
            sampled_bonus = _weighted_sample(weights, 1, rng)
            bonus = sampled_bonus[0] if sampled_bonus else None

        signature = number_signature(numbers, bonus)
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)

        high_count, low_count = count_high_low(numbers, rule)
        odd_count, even_count = count_odd_even(numbers)
        raw_score = _candidate_score(
            numbers=numbers,
            rule=rule,
            number_weights=number_weights,
            pair_counter=pair_counter,
            targets=targets,
            historical_exact_sets=historical_exact_sets,
        )

        row = {
            "GameFamily": rule.game_family,
            "GameName": rule.game_name,
            "DrawType": features["DrawType"].dropna().astype(str).mode().iloc[0] if "DrawType" in features.columns and not features["DrawType"].dropna().empty else "",
            "ModelName": MODEL_NAME,
            "ModelVersion": MODEL_VERSION,
            "RuleVersion": rule.rule_version,
            "RegularRange": f"{rule.regular_min}-{rule.regular_max}",
            "BonusRange": f"{rule.bonus_min}-{rule.bonus_max}" if rule.bonus_min is not None and rule.bonus_max is not None else "None",
            "RegularPickCount": rule.regular_pick_count,
            "BonusPickCount": rule.bonus_pick_count,
            "RegularSum": sum(numbers),
            "HighCount": high_count,
            "LowCount": low_count,
            "OddCount": odd_count,
            "EvenCount": even_count,
            "ConsecutivePairs": consecutive_pairs(numbers),
            "NumberSet": signature,
            "RawScore": raw_score,
            "GeneratedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "SourceTable": feature_table,
        }

        for idx in range(1, 7):
            row[f"N{idx}"] = numbers[idx - 1] if idx <= len(numbers) else None

        row[BONUS_COLUMN] = bonus
        candidate_rows.append(row)

    candidates = pd.DataFrame(candidate_rows)

    if candidates.empty:
        return candidates

    candidates = candidates.drop_duplicates(subset=["NumberSet"])
    candidates = candidates.sort_values("RawScore", ascending=False).reset_index(drop=True)

    selected = _diversity_filter(candidates, rule, top_n=top_n)

    if selected.empty:
        return selected

    score_min = float(selected["RawScore"].min())
    score_max = float(selected["RawScore"].max())

    if score_max > score_min:
        selected["ConfidenceScore"] = 72 + ((selected["RawScore"] - score_min) / (score_max - score_min)) * 24
    else:
        selected["ConfidenceScore"] = 82.0

    selected["ConfidenceScore"] = selected["ConfidenceScore"].round(1)
    selected["PredictionRank"] = range(1, len(selected) + 1)
    selected["PredictionKey"] = selected.apply(
        lambda row: f"{row['GameName']}|{row['GeneratedAt']}|{int(row['PredictionRank'])}|{row['NumberSet']}",
        axis=1,
    )

    ordered_columns = [
        "PredictionKey",
        "GameFamily",
        "GameName",
        "DrawType",
        "PredictionRank",
        "N1",
        "N2",
        "N3",
        "N4",
        "N5",
        "N6",
        "Bonus",
        "RegularSum",
        "HighCount",
        "LowCount",
        "OddCount",
        "EvenCount",
        "ConsecutivePairs",
        "ConfidenceScore",
        "RawScore",
        "NumberSet",
        "ModelName",
        "ModelVersion",
        "RuleVersion",
        "RegularRange",
        "BonusRange",
        "RegularPickCount",
        "BonusPickCount",
        "GeneratedAt",
        "SourceTable",
    ]

    return selected[[column for column in ordered_columns if column in selected.columns]].reset_index(drop=True)


def export_prediction_group(
    group_key: str,
    update_combined_table: bool = True,
) -> pd.DataFrame:
    configs = GAME_CONFIGS[group_key]
    frames: list[pd.DataFrame] = []

    for config in configs:
        predictions = generate_predictions_for_game(
            game_name=config.game_name,
            feature_table=config.feature_table,
            top_n=config.top_n,
            simulation_count=config.simulation_count,
        )
        frames.append(predictions)

    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    if combined.empty:
        output_table = configs[0].output_table
        replace_sqlite_table(output_table, combined)
        return combined

    output_table = configs[0].output_table
    rows = replace_sqlite_table(output_table, combined)
    create_indexes(output_table, ["GameFamily", "GameName", "GeneratedAt", "PredictionRank"])

    print(f"\n{group_key.replace('_', ' ').title()} predictions saved to SQLite.")
    print(f"Table: {output_table}")
    print(f"Rows : {rows}")

    if update_combined_table:
        export_all_prediction_groups()

    return combined


def export_all_prediction_groups() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    for group_key, configs in GAME_CONFIGS.items():
        group_frames = []
        for config in configs:
            group_frames.append(
                generate_predictions_for_game(
                    game_name=config.game_name,
                    feature_table=config.feature_table,
                    top_n=config.top_n,
                    simulation_count=config.simulation_count,
                )
            )

        group_df = pd.concat(group_frames, ignore_index=True) if group_frames else pd.DataFrame()
        if not group_df.empty:
            replace_sqlite_table(configs[0].output_table, group_df)
            create_indexes(configs[0].output_table, ["GameFamily", "GameName", "GeneratedAt", "PredictionRank"])
            frames.append(group_df)

    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    if not combined.empty:
        combined = combined.sort_values(
            by=["GeneratedAt", "GameFamily", "GameName", "PredictionRank"],
            ascending=[False, True, True, True],
        ).reset_index(drop=True)

    rows = replace_sqlite_table("lottery_predictions", combined)
    create_indexes("lottery_predictions", ["GameFamily", "GameName", "GeneratedAt", "PredictionRank"])

    print("\nAll lottery predictions saved to SQLite.")
    print("Table: lottery_predictions")
    print(f"Rows : {rows}")

    return combined
