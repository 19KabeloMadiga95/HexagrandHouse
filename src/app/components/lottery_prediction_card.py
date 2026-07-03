import html

import pandas as pd
import streamlit as st


def safe_text(value, default="-"):
    if value is None or pd.isna(value):
        return default

    value = str(value).strip()

    if value == "" or value.lower() == "nan":
        return default

    return html.escape(value)


def safe_number(value):
    if value is None or pd.isna(value):
        return None

    try:
        return str(int(float(value))).zfill(2)
    except Exception:
        return safe_text(value)


def get_numbers(row):
    numbers = []

    for col in ["N1", "N2", "N3", "N4", "N5", "N6"]:
        if col in row.index:
            value = safe_number(row.get(col))

            if value is not None:
                numbers.append(value)

    return numbers


def lottery_prediction_card(row):
    game = safe_text(
        row.get(
            "GameFamily",
            row.get("GameName", "Lottery")
        )
    )

    subtitle = safe_text(
        row.get(
            "GameName",
            row.get("ModelName", "Ensemble Pick")
        )
    )

    rank = safe_text(
        row.get(
            "PredictionRank",
            row.get("Rank", "-")
        )
    )

    bonus = None

    if "Bonus" in row.index:
        bonus = safe_number(row.get("Bonus"))

    regular_sum = safe_text(row.get("RegularSum", "-"))
    high_count = safe_text(row.get("HighCount", "-"))
    low_count = safe_text(row.get("LowCount", "-"))
    odd_count = safe_text(row.get("OddCount", "-"))
    even_count = safe_text(row.get("EvenCount", "-"))

    confidence = safe_text(
        row.get(
            "ConfidenceScore",
            row.get("Score", "-")
        )
    )

    numbers = get_numbers(row)

    number_html = "".join(
        [
            f'<span class="hgh-lotto-ball">{number}</span>'
            for number in numbers
        ]
    )

    bonus_html = ""

    if bonus is not None:
        bonus_html = (
            f'<span class="hgh-lotto-bonus-label">Bonus</span>'
            f'<span class="hgh-lotto-ball hgh-lotto-ball-bonus">{bonus}</span>'
        )

    html_card = (
        f'<div class="hgh-lotto-card">'
        f'<div class="hgh-lotto-topline">'
        f'<div>'
        f'<div class="hgh-lotto-game">{game}</div>'
        f'<div class="hgh-lotto-subtitle">{subtitle}</div>'
        f'</div>'
        f'<div class="hgh-lotto-rank">#{rank}</div>'
        f'</div>'
        f'<div class="hgh-lotto-numbers">{number_html}{bonus_html}</div>'
        f'<div class="hgh-lotto-metrics">'
        f'<div class="hgh-lotto-metric"><span>Sum</span><strong>{regular_sum}</strong></div>'
        f'<div class="hgh-lotto-metric"><span>High / Low</span><strong>{high_count}H / {low_count}L</strong></div>'
        f'<div class="hgh-lotto-metric"><span>Odd / Even</span><strong>{odd_count}O / {even_count}E</strong></div>'
        f'<div class="hgh-lotto-metric"><span>Confidence</span><strong>{confidence}</strong></div>'
        f'</div>'
        f'</div>'
    )

    st.markdown(
        html_card,
        unsafe_allow_html=True
    )


def render_lottery_prediction_cards(df, max_cards=12):
    if df.empty:
        st.warning("No lottery prediction cards available.")
        return

    display_df = df.copy()

    sort_col = None

    for col in ["PredictionRank", "Rank", "ConfidenceScore", "Score"]:
        if col in display_df.columns:
            sort_col = col
            break

    if sort_col is not None:
        display_df[sort_col] = pd.to_numeric(
            display_df[sort_col],
            errors="coerce"
        )

        ascending = sort_col not in ["ConfidenceScore", "Score"]

        display_df = display_df.sort_values(
            by=sort_col,
            ascending=ascending
        )

    display_df = display_df.head(max_cards)

    for _, row in display_df.iterrows():
        lottery_prediction_card(row)