from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import pandas as pd


@dataclass(frozen=True)
class LotteryGameRule:
    game_key: str
    game_family: str
    game_name: str
    regular_min: int
    regular_max: int
    regular_pick_count: int
    bonus_min: int | None = None
    bonus_max: int | None = None
    bonus_pick_count: int = 0
    effective_from: date = date(1900, 1, 1)
    effective_to: date | None = None
    rule_version: str = "v1"


LOTTO_RULE_HISTORY = [
    LotteryGameRule(
        game_key="lotto",
        game_family="Lotto",
        game_name="Lotto",
        regular_min=1,
        regular_max=52,
        regular_pick_count=6,
        effective_from=date(1900, 1, 1),
        effective_to=date(2025, 9, 20),
        rule_version="Lotto_52_Pre_Expansion",
    ),
    LotteryGameRule(
        game_key="lotto",
        game_family="Lotto",
        game_name="Lotto",
        regular_min=1,
        regular_max=58,
        regular_pick_count=6,
        effective_from=date(2025, 9, 21),
        effective_to=date(2026, 6, 2),
        rule_version="Lotto_58_Expansion",
    ),
    LotteryGameRule(
        game_key="lotto",
        game_family="Lotto",
        game_name="Lotto",
        regular_min=1,
        regular_max=52,
        regular_pick_count=6,
        effective_from=date(2026, 6, 3),
        effective_to=None,
        rule_version="Lotto_52_Sizekhaya",
    ),
]


LOTTO_PLUS_1_RULE_HISTORY = [
    LotteryGameRule(
        game_key="lotto_plus_1",
        game_family="Lotto",
        game_name="Lotto Plus 1",
        regular_min=1,
        regular_max=52,
        regular_pick_count=6,
        effective_from=date(1900, 1, 1),
        effective_to=date(2025, 9, 20),
        rule_version="LottoPlus1_52_Pre_Expansion",
    ),
    LotteryGameRule(
        game_key="lotto_plus_1",
        game_family="Lotto",
        game_name="Lotto Plus 1",
        regular_min=1,
        regular_max=58,
        regular_pick_count=6,
        effective_from=date(2025, 9, 21),
        effective_to=date(2026, 6, 2),
        rule_version="LottoPlus1_58_Expansion",
    ),
    LotteryGameRule(
        game_key="lotto_plus_1",
        game_family="Lotto",
        game_name="Lotto Plus 1",
        regular_min=1,
        regular_max=52,
        regular_pick_count=6,
        effective_from=date(2026, 6, 3),
        effective_to=None,
        rule_version="LottoPlus1_52_Sizekhaya",
    ),
]


LOTTO_PLUS_2_RULE_HISTORY = [
    LotteryGameRule(
        game_key="lotto_plus_2",
        game_family="Lotto",
        game_name="Lotto Plus 2",
        regular_min=1,
        regular_max=52,
        regular_pick_count=6,
        effective_from=date(1900, 1, 1),
        effective_to=date(2025, 9, 20),
        rule_version="LottoPlus2_52_Pre_Expansion",
    ),
    LotteryGameRule(
        game_key="lotto_plus_2",
        game_family="Lotto",
        game_name="Lotto Plus 2",
        regular_min=1,
        regular_max=58,
        regular_pick_count=6,
        effective_from=date(2025, 9, 21),
        effective_to=date(2026, 6, 2),
        rule_version="LottoPlus2_58_Expansion",
    ),
    LotteryGameRule(
        game_key="lotto_plus_2",
        game_family="Lotto",
        game_name="Lotto Plus 2",
        regular_min=1,
        regular_max=52,
        regular_pick_count=6,
        effective_from=date(2026, 6, 3),
        effective_to=None,
        rule_version="LottoPlus2_52_Sizekhaya",
    ),
]


POWERBALL_RULE_HISTORY = [
    LotteryGameRule(
        game_key="powerball",
        game_family="PowerBall",
        game_name="PowerBall",
        regular_min=1,
        regular_max=50,
        regular_pick_count=5,
        bonus_min=1,
        bonus_max=20,
        bonus_pick_count=1,
        effective_from=date(1900, 1, 1),
        effective_to=date(2026, 6, 2),
        rule_version="PowerBall_20_Pre_Sizekhaya",
    ),
    LotteryGameRule(
        game_key="powerball",
        game_family="PowerBall",
        game_name="PowerBall",
        regular_min=1,
        regular_max=50,
        regular_pick_count=5,
        bonus_min=1,
        bonus_max=16,
        bonus_pick_count=1,
        effective_from=date(2026, 6, 3),
        effective_to=None,
        rule_version="PowerBall_16_Sizekhaya",
    ),
]


POWERBALL_PLUS_RULE_HISTORY = [
    LotteryGameRule(
        game_key="powerball_plus",
        game_family="PowerBall",
        game_name="PowerBall Plus",
        regular_min=1,
        regular_max=50,
        regular_pick_count=5,
        bonus_min=1,
        bonus_max=20,
        bonus_pick_count=1,
        effective_from=date(1900, 1, 1),
        effective_to=date(2026, 6, 2),
        rule_version="PowerBallPlus_20_Pre_Sizekhaya",
    ),
    LotteryGameRule(
        game_key="powerball_plus",
        game_family="PowerBall",
        game_name="PowerBall Plus",
        regular_min=1,
        regular_max=50,
        regular_pick_count=5,
        bonus_min=1,
        bonus_max=16,
        bonus_pick_count=1,
        effective_from=date(2026, 6, 3),
        effective_to=None,
        rule_version="PowerBallPlus_16_Sizekhaya",
    ),
]


DAILY_LOTTO_RULE_HISTORY = [
    LotteryGameRule(
        game_key="daily_lotto",
        game_family="Daily Lotto",
        game_name="Daily Lotto",
        regular_min=1,
        regular_max=36,
        regular_pick_count=5,
        effective_from=date(1900, 1, 1),
        effective_to=None,
        rule_version="DailyLotto_36_Current",
    ),
]


UK49S_LUNCHTIME_RULE_HISTORY = [
    LotteryGameRule(
        game_key="uk49s_lunchtime",
        game_family="UK49s",
        game_name="UK49s Lunchtime",
        regular_min=1,
        regular_max=49,
        regular_pick_count=6,
        bonus_min=1,
        bonus_max=49,
        bonus_pick_count=1,
        effective_from=date(1900, 1, 1),
        effective_to=None,
        rule_version="UK49sLunchtime_49_Current",
    ),
]


UK49S_TEATIME_RULE_HISTORY = [
    LotteryGameRule(
        game_key="uk49s_teatime",
        game_family="UK49s",
        game_name="UK49s Teatime",
        regular_min=1,
        regular_max=49,
        regular_pick_count=6,
        bonus_min=1,
        bonus_max=49,
        bonus_pick_count=1,
        effective_from=date(1900, 1, 1),
        effective_to=None,
        rule_version="UK49sTeatime_49_Current",
    ),
]


LOTTERY_RULE_HISTORY = {
    "lotto": LOTTO_RULE_HISTORY,
    "lotto plus 1": LOTTO_PLUS_1_RULE_HISTORY,
    "lotto plus 2": LOTTO_PLUS_2_RULE_HISTORY,
    "powerball": POWERBALL_RULE_HISTORY,
    "powerball plus": POWERBALL_PLUS_RULE_HISTORY,
    "daily lotto": DAILY_LOTTO_RULE_HISTORY,
    "uk49s lunchtime": UK49S_LUNCHTIME_RULE_HISTORY,
    "uk49s teatime": UK49S_TEATIME_RULE_HISTORY,
}


def normalise_game_name(game_name: str) -> str:
    return str(game_name or "").strip().lower()


def coerce_date(value) -> date:
    if value is None or value == "":
        return date.today()

    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        return date.today()

    return parsed.date()


def get_rule_history(game_name: str) -> list[LotteryGameRule]:
    return LOTTERY_RULE_HISTORY.get(normalise_game_name(game_name), [])


def get_lottery_rule(game_name: str) -> LotteryGameRule | None:
    """
    Backward-compatible helper.

    Returns the current active rule.
    """

    return get_current_rule(game_name)


def get_current_rule(game_name: str) -> LotteryGameRule | None:
    rules = get_rule_history(game_name)

    if not rules:
        return None

    return sorted(
        rules,
        key=lambda rule: rule.effective_from,
        reverse=True,
    )[0]


def get_rule_for_draw(
    game_name: str,
    draw_date=None,
) -> LotteryGameRule | None:
    rules = get_rule_history(game_name)

    if not rules:
        return None

    check_date = coerce_date(draw_date)

    for rule in sorted(
        rules,
        key=lambda item: item.effective_from,
        reverse=True,
    ):
        starts_ok = check_date >= rule.effective_from
        ends_ok = rule.effective_to is None or check_date <= rule.effective_to

        if starts_ok and ends_ok:
            return rule

    return sorted(
        rules,
        key=lambda item: item.effective_from,
    )[0]


def get_regular_range(rule: LotteryGameRule) -> range:
    return range(rule.regular_min, rule.regular_max + 1)


def get_bonus_range(rule: LotteryGameRule) -> range | None:
    if (
        rule.bonus_pick_count <= 0
        or rule.bonus_min is None
        or rule.bonus_max is None
    ):
        return None

    return range(rule.bonus_min, rule.bonus_max + 1)


def get_current_regular_range(game_name: str) -> range:
    rule = get_current_rule(game_name)

    if rule is None:
        return range(0)

    return get_regular_range(rule)


def get_current_bonus_range(game_name: str) -> range | None:
    rule = get_current_rule(game_name)

    if rule is None:
        return None

    return get_bonus_range(rule)


def get_historical_regular_range(
    game_name: str,
    draw_date=None,
) -> range:
    rule = get_rule_for_draw(game_name, draw_date)

    if rule is None:
        return range(0)

    return get_regular_range(rule)


def get_historical_bonus_range(
    game_name: str,
    draw_date=None,
) -> range | None:
    rule = get_rule_for_draw(game_name, draw_date)

    if rule is None:
        return None

    return get_bonus_range(rule)


def get_max_historical_regular_number(game_name: str) -> int:
    rules = get_rule_history(game_name)

    if not rules:
        return 0

    return max(rule.regular_max for rule in rules)


def get_max_historical_bonus_number(game_name: str) -> int | None:
    rules = get_rule_history(game_name)

    bonus_values = [
        rule.bonus_max
        for rule in rules
        if rule.bonus_max is not None
    ]

    if not bonus_values:
        return None

    return max(bonus_values)


def get_prediction_regular_range(game_name: str) -> range:
    return get_current_regular_range(game_name)


def get_prediction_bonus_range(game_name: str) -> range | None:
    return get_current_bonus_range(game_name)


def is_regular_number_valid(
    rule: LotteryGameRule,
    number: int,
) -> bool:
    return rule.regular_min <= int(number) <= rule.regular_max


def is_bonus_number_valid(
    rule: LotteryGameRule,
    number: int,
) -> bool:
    if (
        rule.bonus_pick_count <= 0
        or rule.bonus_min is None
        or rule.bonus_max is None
    ):
        return False

    return rule.bonus_min <= int(number) <= rule.bonus_max


def get_low_high_split(rule: LotteryGameRule) -> tuple[set[int], set[int]]:
    midpoint = rule.regular_max // 2

    low_numbers = set(range(rule.regular_min, midpoint + 1))
    high_numbers = set(range(midpoint + 1, rule.regular_max + 1))

    return low_numbers, high_numbers


def get_upper_start(rule: LotteryGameRule) -> int:
    return int(rule.regular_max * 0.85)


def get_upper_elite(rule: LotteryGameRule) -> int:
    return int(rule.regular_max * 0.92)


def get_dynamic_buckets(rule: LotteryGameRule) -> dict[str, range]:
    max_number = rule.regular_max
    step = max_number // 4

    return {
        "LOW": range(rule.regular_min, step + 1),
        "MID_LOW": range(step + 1, step * 2 + 1),
        "MID_HIGH": range(step * 2 + 1, step * 3 + 1),
        "HIGH": range(step * 3 + 1, max_number + 1),
    }


def get_rule_summary() -> list[dict]:
    rows = []

    for rules in LOTTERY_RULE_HISTORY.values():
        for rule in rules:
            rows.append(
                {
                    "GameKey": rule.game_key,
                    "GameFamily": rule.game_family,
                    "GameName": rule.game_name,
                    "RegularRange": f"{rule.regular_min}-{rule.regular_max}",
                    "RegularPickCount": rule.regular_pick_count,
                    "BonusRange": (
                        f"{rule.bonus_min}-{rule.bonus_max}"
                        if rule.bonus_min is not None
                        else "-"
                    ),
                    "BonusPickCount": rule.bonus_pick_count,
                    "EffectiveFrom": rule.effective_from.isoformat(),
                    "EffectiveTo": (
                        rule.effective_to.isoformat()
                        if rule.effective_to
                        else "Current"
                    ),
                    "RuleVersion": rule.rule_version,
                }
            )

    return rows