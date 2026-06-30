from dataclasses import dataclass


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


LOTTO_RULES = LotteryGameRule(
    game_key="lotto",
    game_family="Lotto",
    game_name="Lotto",
    regular_min=1,
    regular_max=52,
    regular_pick_count=6,
    bonus_min=None,
    bonus_max=None,
    bonus_pick_count=0,
)


LOTTO_PLUS_1_RULES = LotteryGameRule(
    game_key="lotto_plus_1",
    game_family="Lotto",
    game_name="Lotto Plus 1",
    regular_min=1,
    regular_max=52,
    regular_pick_count=6,
)


LOTTO_PLUS_2_RULES = LotteryGameRule(
    game_key="lotto_plus_2",
    game_family="Lotto",
    game_name="Lotto Plus 2",
    regular_min=1,
    regular_max=52,
    regular_pick_count=6,
)


POWERBALL_RULES = LotteryGameRule(
    game_key="powerball",
    game_family="PowerBall",
    game_name="PowerBall",
    regular_min=1,
    regular_max=50,
    regular_pick_count=5,
    bonus_min=1,
    bonus_max=16,
    bonus_pick_count=1,
)


POWERBALL_PLUS_RULES = LotteryGameRule(
    game_key="powerball_plus",
    game_family="PowerBall",
    game_name="PowerBall Plus",
    regular_min=1,
    regular_max=50,
    regular_pick_count=5,
    bonus_min=1,
    bonus_max=16,
    bonus_pick_count=1,
)


DAILY_LOTTO_RULES = LotteryGameRule(
    game_key="daily_lotto",
    game_family="Daily Lotto",
    game_name="Daily Lotto",
    regular_min=1,
    regular_max=36,
    regular_pick_count=5,
)


UK49S_LUNCHTIME_RULES = LotteryGameRule(
    game_key="uk49s_lunchtime",
    game_family="UK49s",
    game_name="UK49s Lunchtime",
    regular_min=1,
    regular_max=49,
    regular_pick_count=6,
    bonus_min=1,
    bonus_max=49,
    bonus_pick_count=1,
)


UK49S_TEATIME_RULES = LotteryGameRule(
    game_key="uk49s_teatime",
    game_family="UK49s",
    game_name="UK49s Teatime",
    regular_min=1,
    regular_max=49,
    regular_pick_count=6,
    bonus_min=1,
    bonus_max=49,
    bonus_pick_count=1,
)


LOTTERY_GAME_RULES = {
    "lotto": LOTTO_RULES,
    "lotto plus 1": LOTTO_PLUS_1_RULES,
    "lotto plus 2": LOTTO_PLUS_2_RULES,
    "powerball": POWERBALL_RULES,
    "powerball plus": POWERBALL_PLUS_RULES,
    "daily lotto": DAILY_LOTTO_RULES,
    "uk49s lunchtime": UK49S_LUNCHTIME_RULES,
    "uk49s teatime": UK49S_TEATIME_RULES,
}


def get_lottery_rule(game_name: str) -> LotteryGameRule | None:
    if not game_name:
        return None

    return LOTTERY_GAME_RULES.get(
        str(game_name).strip().lower()
    )


def get_regular_range(rule: LotteryGameRule) -> range:
    return range(
        rule.regular_min,
        rule.regular_max + 1
    )


def get_bonus_range(rule: LotteryGameRule) -> range | None:
    if rule.bonus_min is None or rule.bonus_max is None:
        return None

    return range(
        rule.bonus_min,
        rule.bonus_max + 1
    )


def is_regular_number_valid(rule: LotteryGameRule, number: int) -> bool:
    return rule.regular_min <= int(number) <= rule.regular_max


def is_bonus_number_valid(rule: LotteryGameRule, number: int) -> bool:
    if rule.bonus_min is None or rule.bonus_max is None:
        return False

    return rule.bonus_min <= int(number) <= rule.bonus_max


def get_low_high_split(rule: LotteryGameRule) -> tuple[set[int], set[int]]:
    midpoint = rule.regular_max // 2

    low_numbers = set(
        range(
            rule.regular_min,
            midpoint + 1
        )
    )

    high_numbers = set(
        range(
            midpoint + 1,
            rule.regular_max + 1
        )
    )

    return low_numbers, high_numbers


def get_rule_summary() -> list[dict]:
    rows = []

    for rule in LOTTERY_GAME_RULES.values():
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
            }
        )

    return rows