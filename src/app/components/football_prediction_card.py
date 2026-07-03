import html

import pandas as pd
import streamlit as st


# =========================================================
# CSS
# =========================================================

def inject_football_card_css():
    st.markdown(
        """
<style>

.hgh-football-card {
    background: linear-gradient(145deg, #0d131c, #060a10);
    border: 1px solid rgba(255, 199, 44, 0.35);
    border-radius: 18px;
    padding: 18px 20px;
    margin-bottom: 18px;
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.35);
}

.hgh-card-topline {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;
}

.hgh-card-league {
    color: #facc15;
    font-size: 0.82rem;
    font-weight: 800;
    text-transform: uppercase;
    margin-right: 10px;
}

.hgh-card-date {
    color: #9ca3af;
    font-size: 0.78rem;
}

.hgh-card-badge {
    display: inline-flex;
    align-items: center;
    border: 1px solid rgba(255, 199, 44, 0.45);
    border-radius: 999px;
    padding: 4px 10px;
    font-size: 0.68rem;
    font-weight: 800;
    margin-left: 6px;
}

.hgh-card-badge-elite {
    color: #f87171;
    border-color: #f87171;
    background: rgba(248, 113, 113, 0.08);
}

.hgh-card-match {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 14px;
    margin: 16px 0;
}

.hgh-card-team {
    color: white;
    font-size: 1.25rem;
    font-weight: 900;
    line-height: 1.2;
}

.hgh-card-team:last-child {
    text-align: right;
}

.hgh-card-vs {
    color: #facc15;
    border: 1px solid rgba(255, 199, 44, 0.25);
    border-radius: 999px;
    padding: 5px 10px;
    font-size: 0.7rem;
    font-weight: 900;
}

.hgh-card-mainpick {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(255, 199, 44, 0.08);
    border: 1px solid rgba(255, 199, 44, 0.14);
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 14px;
}

.hgh-card-label {
    color: #9ca3af;
    font-size: 0.68rem;
    text-transform: uppercase;
    margin-bottom: 4px;
}

.hgh-card-pick {
    color: white;
    font-size: 1rem;
    font-weight: 900;
}

.hgh-card-confidence {
    font-size: 1.45rem;
    font-weight: 950;
}

.hgh-card-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
}

.hgh-card-mini {
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 13px;
    padding: 11px;
}

.hgh-card-mini-value {
    color: white;
    font-weight: 800;
    font-size: 0.86rem;
    line-height: 1.2;
    min-height: 34px;
}

.hgh-card-mini-prob {
    font-weight: 950;
    font-size: 1rem;
    margin-top: 5px;
}

.hgh-progress-wrap {
    margin-top: 8px;
}

.hgh-progress-track {
    width: 100%;
    height: 8px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.06);
    overflow: hidden;
}

.hgh-progress-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.4s ease;
}

.hgh-card-warning {
    margin-top: 10px;
    color: #facc15;
    font-size: 0.75rem;
    font-weight: 700;
}

@media (max-width: 900px) {
    .hgh-card-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .hgh-card-match {
        grid-template-columns: 1fr;
    }

    .hgh-card-team:last-child {
        text-align: left;
    }
}

</style>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# HELPERS
# =========================================================

def safe_text(value, default="-"):
    if value is None:
        return default

    if pd.isna(value):
        return default

    value = str(value).strip()

    if value == "" or value.lower() == "nan":
        return default

    return html.escape(value)


def safe_probability(value, default="-"):
    if value is None:
        return default

    if pd.isna(value):
        return default

    try:
        value = float(value)

        if value <= 1:
            value = value * 100

        return f"{round(value, 1)}%"

    except Exception:
        return default


def safe_probability_value(value):
    try:
        value = float(value)

        if value <= 1:
            value = value * 100

        if value < 0:
            return 0

        if value > 100:
            return 100

        return round(value, 1)

    except Exception:
        return 0


def confidence_color(value):
    try:
        value = float(value)

        if value <= 1:
            value = value * 100

    except Exception:
        return "#8b949e"

    if value >= 85:
        return "#22c55e"

    if value >= 75:
        return "#84cc16"

    if value >= 65:
        return "#facc15"

    if value >= 55:
        return "#f97316"

    return "#8b949e"


def confidence_band(value):
    try:
        value = float(value)

        if value <= 1:
            value = value * 100

    except Exception:
        return "No Data"

    if value >= 85:
        return "Elite"

    if value >= 75:
        return "Strong"

    if value >= 65:
        return "Medium"

    if value >= 55:
        return "Small"

    return "Weak"


def progress_bar_html(value, color):
    return f"""
<div class="hgh-progress-wrap">
<div class="hgh-progress-track">
<div class="hgh-progress-fill" style="width:{value}%; background:{color};"></div>
</div>
</div>
"""


def format_fixture_datetime(fixture_date, kickoff_time):
    try:
        date_value = pd.to_datetime(
            fixture_date,
            errors="coerce"
        )

        if pd.isna(date_value):
            return f"{safe_text(fixture_date)} {safe_text(kickoff_time)}"

        date_text = date_value.strftime("%d %b %Y")

        kickoff_text = safe_text(
            kickoff_time,
            ""
        )

        if kickoff_text in ["-", ""]:
            return date_text

        return f"{date_text} • {kickoff_text}"

    except Exception:
        return f"{safe_text(fixture_date)} {safe_text(kickoff_time)}"


def choose_primary_market(
    predicted_result,
    predicted_result_probability,
    best_goals_pick,
    best_goals_probability,
    best_corners_pick,
    best_corners_probability,
):
    result_probability = safe_probability_value(
        predicted_result_probability
    )

    goals_probability = safe_probability_value(
        best_goals_probability
    )

    corners_probability = safe_probability_value(
        best_corners_probability
    )

    candidates = []

    if safe_text(predicted_result) != "-":
        candidates.append(
            {
                "market": "Result",
                "signal": safe_text(predicted_result),
                "probability": result_probability,
            }
        )

    if safe_text(best_goals_pick) != "-":
        candidates.append(
            {
                "market": "Goals",
                "signal": safe_text(best_goals_pick),
                "probability": goals_probability,
            }
        )

    if safe_text(best_corners_pick, "No corners data") != "No corners data":
        candidates.append(
            {
                "market": "Corners",
                "signal": safe_text(best_corners_pick),
                "probability": corners_probability,
            }
        )

    if not candidates:
        return {
            "market": "Unknown",
            "signal": "-",
            "probability": 0,
        }

    return max(
        candidates,
        key=lambda item: item["probability"]
    )


def clean_elite_badge(
    elite_prediction,
    primary_probability,
    signal_count,
):
    try:
        elite_value = int(elite_prediction)
    except Exception:
        elite_value = 0

    try:
        signal_count_value = int(signal_count)
    except Exception:
        signal_count_value = 0

    if (
        elite_value == 1
        and primary_probability >= 80
        and signal_count_value >= 3
    ):
        return (
            '<span class="hgh-card-badge hgh-card-badge-elite">'
            '🔥 ELITE PICK'
            '</span>'
        )

    return ""


# =========================================================
# SINGLE CARD
# =========================================================

def football_prediction_card(
    fixture_date,
    kickoff_time,
    league,
    home_team,
    away_team,
    predicted_result,
    predicted_result_probability,
    best_goals_pick,
    best_goals_probability,
    best_corners_pick=None,
    best_corners_probability=None,
    ensemble_confidence_score=None,
    signal_count=None,
    elite_prediction=0,
    betting_grade=None,
):
    league = safe_text(league)
    home_team = safe_text(home_team)
    away_team = safe_text(away_team)

    predicted_result = safe_text(predicted_result)
    best_goals_pick = safe_text(best_goals_pick)

    best_corners_pick = safe_text(
        best_corners_pick,
        "No corners data"
    )

    betting_grade = safe_text(
        betting_grade,
        "No Grade"
    )

    display_datetime = format_fixture_datetime(
        fixture_date,
        kickoff_time
    )

    primary_market = choose_primary_market(
        predicted_result,
        predicted_result_probability,
        best_goals_pick,
        best_goals_probability,
        best_corners_pick,
        best_corners_probability,
    )

    primary_market_name = primary_market["market"]
    primary_signal = primary_market["signal"]
    primary_probability_value = primary_market["probability"]
    primary_probability_text = f"{primary_probability_value}%"

    result_probability_text = safe_probability(
        predicted_result_probability
    )

    goals_probability_text = safe_probability(
        best_goals_probability
    )

    corners_probability_text = safe_probability(
        best_corners_probability
    )

    result_probability_value = safe_probability_value(
        predicted_result_probability
    )

    goals_probability_value = safe_probability_value(
        best_goals_probability
    )

    corners_probability_value = safe_probability_value(
        best_corners_probability
    )

    primary_color = confidence_color(
        primary_probability_value
    )

    result_color = confidence_color(
        result_probability_value
    )

    goals_color = confidence_color(
        goals_probability_value
    )

    corners_color = confidence_color(
        corners_probability_value
    )

    primary_band = confidence_band(
        primary_probability_value
    )

    grade_badge = ""

    if betting_grade != "No Grade":
        grade_badge = (
            f'<span class="hgh-card-badge">'
            f'{betting_grade}'
            f'</span>'
        )

    elite_badge = clean_elite_badge(
        elite_prediction,
        primary_probability_value,
        signal_count,
    )

    signal_text = "-"

    if signal_count is not None and not pd.isna(signal_count):
        try:
            signal_text = str(int(signal_count))
        except Exception:
            signal_text = str(signal_count)

    result_bar = progress_bar_html(
        result_probability_value,
        result_color
    )

    goals_bar = progress_bar_html(
        goals_probability_value,
        goals_color
    )

    corners_bar = progress_bar_html(
        corners_probability_value,
        corners_color
    )

    primary_bar = progress_bar_html(
        primary_probability_value,
        primary_color
    )

    caution_note = ""

    if (
        primary_market_name != "Result"
        and result_probability_value < 50
    ):
        caution_note = (
            '<div class="hgh-card-warning">'
            '⚠️ Result market is low confidence. Best edge is market-specific.'
            '</div>'
        )

    html_card = f"""
<div class="hgh-football-card">

<div class="hgh-card-topline">
<div>
<span class="hgh-card-league">{league}</span>
<span class="hgh-card-date">{display_datetime}</span>
</div>
<div>
{elite_badge}
{grade_badge}
<span class="hgh-card-badge" style="border-color:{primary_color}; color:{primary_color};">
{primary_band}
</span>
</div>
</div>

<div class="hgh-card-match">
<div class="hgh-card-team">{home_team}</div>
<div class="hgh-card-vs">VS</div>
<div class="hgh-card-team">{away_team}</div>
</div>

<div class="hgh-card-mainpick">
<div>
<div class="hgh-card-label">Primary Market Signal</div>
<div class="hgh-card-pick">{primary_market_name}: {primary_signal}</div>
</div>
<div class="hgh-card-confidence" style="color:{primary_color};">
{primary_probability_text}
</div>
</div>

{primary_bar}
{caution_note}

<div class="hgh-card-grid">

<div class="hgh-card-mini">
<div class="hgh-card-label">Result</div>
<div class="hgh-card-mini-value">{predicted_result}</div>
<div class="hgh-card-mini-prob" style="color:{result_color};">{result_probability_text}</div>
{result_bar}
</div>

<div class="hgh-card-mini">
<div class="hgh-card-label">Goals</div>
<div class="hgh-card-mini-value">{best_goals_pick}</div>
<div class="hgh-card-mini-prob" style="color:{goals_color};">{goals_probability_text}</div>
{goals_bar}
</div>

<div class="hgh-card-mini">
<div class="hgh-card-label">Corners</div>
<div class="hgh-card-mini-value">{best_corners_pick}</div>
<div class="hgh-card-mini-prob" style="color:{corners_color};">{corners_probability_text}</div>
{corners_bar}
</div>

<div class="hgh-card-mini">
<div class="hgh-card-label">Signals</div>
<div class="hgh-card-mini-value">{signal_text}/3</div>
<div class="hgh-card-mini-prob" style="color:{primary_color};">{primary_band}</div>
{primary_bar}
</div>

</div>

</div>
"""

    st.markdown(
        html_card,
        unsafe_allow_html=True
    )


# =========================================================
# MULTI CARD RENDERER
# =========================================================

def render_football_prediction_cards(
    df,
    max_cards=10,
):
    inject_football_card_css()

    if df.empty:
        st.warning(
            "No prediction cards available."
        )

        return

    display_df = df.copy()

    if "PrimaryMarketProbability" in display_df.columns:
        display_df = display_df.sort_values(
            by="PrimaryMarketProbability",
            ascending=False
        )

    elif "EnsembleConfidenceScore" in display_df.columns:
        display_df = display_df.sort_values(
            by="EnsembleConfidenceScore",
            ascending=False
        )

    display_df = display_df.head(max_cards)

    for _, row in display_df.iterrows():
        football_prediction_card(
            fixture_date=row.get("FixtureDate"),
            kickoff_time=row.get("KickoffTime"),
            league=row.get("League"),
            home_team=row.get("HomeTeam"),
            away_team=row.get("AwayTeam"),
            predicted_result=row.get("PredictedResult"),
            predicted_result_probability=row.get("PredictedResultProbability"),
            best_goals_pick=row.get("BestGoalsPick"),
            best_goals_probability=row.get("BestGoalsProbability"),
            best_corners_pick=row.get("BestCornersPick"),
            best_corners_probability=row.get("BestCornersProbability"),
            ensemble_confidence_score=row.get("EnsembleConfidenceScore"),
            signal_count=row.get("SignalCount"),
            elite_prediction=row.get("ElitePrediction", 0),
            betting_grade=row.get("BettingGrade"),
        )