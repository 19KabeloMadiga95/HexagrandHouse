from pathlib import Path
import sys
import html

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pandas as pd
import streamlit as st

from lottery.frontend.components.kpi_cards import (
    kpi_card,
    section_card,
    last_refresh_card,
)

from lottery.frontend.components.charts import (
    plot_bar_chart,
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Results Intelligence",
    page_icon="📊",
    layout="wide",
)


# =========================================================
# CSS
# =========================================================

def load_main_css():
    css_path = (
        Path(__file__).resolve().parents[1]
        / "styles"
        / "main.css"
    )

    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )


def inject_results_css():
    st.markdown(
        """
<style>

.hgh-results-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 18px;
}

.hgh-result-card {
    background:
        radial-gradient(circle at top left, rgba(255,191,0,0.10), transparent 36%),
        linear-gradient(145deg, rgba(13,19,28,0.98), rgba(6,10,16,0.98));
    border: 1px solid rgba(255,191,0,0.28);
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 18px;
    box-shadow: 0 18px 45px rgba(0,0,0,0.28);
}

.hgh-result-topline {
    display: flex;
    justify-content: space-between;
    gap: 14px;
    align-items: flex-start;
    margin-bottom: 16px;
}

.hgh-result-kicker {
    color: #ffbf00;
    font-size: 0.72rem;
    font-weight: 900;
    letter-spacing: 0.10em;
    text-transform: uppercase;
}

.hgh-result-date {
    color: #9db0ca;
    font-size: 0.76rem;
    margin-top: 4px;
}

.hgh-result-badge {
    border: 1px solid rgba(255,191,0,0.36);
    color: #ffbf00;
    border-radius: 999px;
    padding: 5px 10px;
    font-size: 0.68rem;
    font-weight: 900;
    white-space: nowrap;
}

.hgh-lottery-balls {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 18px 0;
}

.hgh-lottery-ball {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    display: inline-flex;
    justify-content: center;
    align-items: center;
    color: #111827;
    font-weight: 950;
    background:
        radial-gradient(circle at 30% 25%, #ffffff, #d8dee8 45%, #8b96a8);
    box-shadow:
        inset 0 2px 4px rgba(255,255,255,0.7),
        0 8px 18px rgba(0,0,0,0.35);
}

.hgh-lottery-ball-bonus {
    background:
        radial-gradient(circle at 30% 25%, #ffd966, #ffbf00 48%, #a66a00);
    color: black;
}

.hgh-result-meta-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-top: 14px;
}

.hgh-result-meta {
    background: rgba(15,23,42,0.72);
    border: 1px solid rgba(148,163,184,0.14);
    border-radius: 14px;
    padding: 11px;
}

.hgh-result-meta-label {
    color: #9db0ca;
    font-size: 0.66rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 5px;
}

.hgh-result-meta-value {
    color: white;
    font-weight: 900;
    font-size: 0.9rem;
}

.hgh-football-scoreline {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 18px;
    align-items: center;
    margin: 18px 0;
}

.hgh-football-team {
    color: white;
    font-size: 1.15rem;
    font-weight: 950;
    line-height: 1.2;
}

.hgh-football-team-away {
    text-align: right;
}

.hgh-football-score {
    color: #ffbf00;
    font-size: 1.7rem;
    font-weight: 950;
    padding: 8px 15px;
    border-radius: 14px;
    background: rgba(255,191,0,0.10);
    border: 1px solid rgba(255,191,0,0.25);
}

.hgh-hit-good {
    color: #00e676;
    font-weight: 900;
}

.hgh-hit-bad {
    color: #ff5c5c;
    font-weight: 900;
}

.hgh-pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 12px 0 22px 0;
}

.hgh-pill {
    border: 1px solid rgba(255,191,0,0.22);
    background: rgba(255,191,0,0.06);
    color: #ffbf00;
    border-radius: 999px;
    padding: 7px 12px;
    font-size: 0.76rem;
    font-weight: 900;
}

@media (max-width: 900px) {
    .hgh-results-grid {
        grid-template-columns: 1fr;
    }

    .hgh-result-meta-grid {
        grid-template-columns: 1fr;
    }

    .hgh-football-scoreline {
        grid-template-columns: 1fr;
    }

    .hgh-football-team-away {
        text-align: left;
    }
}

</style>
        """,
        unsafe_allow_html=True
    )


load_main_css()
inject_results_css()
last_refresh_card()


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[4]

LOTTERY_MASTER_FILE = (
    BASE_DIR
    / "data"
    / "master"
    / "lottery_historical_master.xlsx"
)

FOOTBALL_MASTER_FILE = (
    BASE_DIR
    / "data"
    / "football"
    / "master"
    / "football_master_all_leagues.xlsx"
)

FOOTBALL_BACKTEST_FILE = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "backtesting"
    / "football_fixture_backtest_history.xlsx"
)


# =========================================================
# DATA LOADING
# =========================================================

@st.cache_data
def safe_read_excel(path, sheet_name=0):
    try:
        return pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine="openpyxl"
        )
    except Exception:
        return pd.DataFrame()


def safe_text(value, default="-"):
    if value is None:
        return default

    if pd.isna(value):
        return default

    value = str(value).strip()

    if value == "" or value.lower() == "nan":
        return default

    return html.escape(value)


def safe_number(value, default="-"):
    if value is None:
        return default

    if pd.isna(value):
        return default

    try:
        return int(float(value))
    except Exception:
        return default


def format_date(value):
    try:
        value = pd.to_datetime(
            value,
            errors="coerce"
        )

        if pd.isna(value):
            return "-"

        return value.strftime("%A • %d %b %Y")

    except Exception:
        return "-"


def format_short_date(value):
    try:
        value = pd.to_datetime(
            value,
            errors="coerce"
        )

        if pd.isna(value):
            return "-"

        return value.strftime("%Y-%m-%d")

    except Exception:
        return "-"


def format_currency(value):
    if value is None or pd.isna(value):
        return "-"

    try:
        value = float(value)

        if value >= 1_000_000:
            return f"R{round(value / 1_000_000, 1)}M"

        if value >= 1_000:
            return f"R{round(value / 1_000, 1)}K"

        return f"R{round(value, 2)}"

    except Exception:
        return safe_text(value)


# =========================================================
# LOAD DATA
# =========================================================

lottery_df = safe_read_excel(
    LOTTERY_MASTER_FILE
)

football_df = safe_read_excel(
    FOOTBALL_MASTER_FILE,
    "Football_Master"
)

football_backtest_df = safe_read_excel(
    FOOTBALL_BACKTEST_FILE,
    "Backtest_History"
)

if not lottery_df.empty and "DrawDate" in lottery_df.columns:
    lottery_df["DrawDate"] = pd.to_datetime(
        lottery_df["DrawDate"],
        errors="coerce"
    )

if not football_df.empty and "MatchDate" in football_df.columns:
    football_df["MatchDate"] = pd.to_datetime(
        football_df["MatchDate"],
        errors="coerce"
    )

if not football_backtest_df.empty and "FixtureDate" in football_backtest_df.columns:
    football_backtest_df["FixtureDate"] = pd.to_datetime(
        football_backtest_df["FixtureDate"],
        errors="coerce"
    )


# =========================================================
# FILTER RECENT DATA
# =========================================================

today = pd.Timestamp.today().normalize()
seven_days_ago = today - pd.Timedelta(days=7)

recent_lottery_df = lottery_df.copy()

if not recent_lottery_df.empty and "DrawDate" in recent_lottery_df.columns:
    recent_lottery_df = recent_lottery_df[
        recent_lottery_df["DrawDate"] >= seven_days_ago
    ].copy()

recent_football_df = football_df.copy()

if not recent_football_df.empty and "MatchDate" in recent_football_df.columns:
    recent_football_df = recent_football_df[
        recent_football_df["MatchDate"] >= seven_days_ago
    ].copy()

    recent_football_df = recent_football_df[
        recent_football_df["HomeGoals"].notna()
        & recent_football_df["AwayGoals"].notna()
    ].copy()


# =========================================================
# HERO
# =========================================================

st.markdown(
    """<div class="hgh-premium-hero-small"><div class="hgh-hero-kicker">RESULTS INTELLIGENCE</div><h1 class="hgh-hero-title-small">Recent Outcomes & Performance Feed</h1><p class="hgh-hero-subtitle-small">A cleaner view of recent lottery draws, completed football matches and model scoring activity from the last 7 days.</p></div>""",
    unsafe_allow_html=True
)

st.divider()


# =========================================================
# KPI SUMMARY
# =========================================================

latest_lottery_date = "-"

if not recent_lottery_df.empty and "DrawDate" in recent_lottery_df.columns:
    latest_lottery_date = format_short_date(
        recent_lottery_df["DrawDate"].max()
    )

latest_football_date = "-"

if not recent_football_df.empty and "MatchDate" in recent_football_df.columns:
    latest_football_date = format_short_date(
        recent_football_df["MatchDate"].max()
    )

scored_predictions = len(football_backtest_df)

result_accuracy = "-"

if (
    not football_backtest_df.empty
    and "ResultHit" in football_backtest_df.columns
):
    result_accuracy = f"{round(pd.to_numeric(football_backtest_df['ResultHit'], errors='coerce').mean() * 100, 1)}%"

k1, k2, k3, k4 = st.columns(4)

with k1:
    kpi_card(
        "Lottery Results",
        len(recent_lottery_df),
        "Draws in last 7 days",
        "🎲"
    )

with k2:
    kpi_card(
        "Football Results",
        len(recent_football_df),
        "Completed matches",
        "⚽"
    )

with k3:
    kpi_card(
        "Latest Football",
        latest_football_date,
        "Newest completed match",
        "📅"
    )

with k4:
    kpi_card(
        "Model Accuracy",
        result_accuracy,
        f"{scored_predictions} scored fixtures",
        "🎯"
    )


st.divider()


# =========================================================
# CONTROLS
# =========================================================

control_col1, control_col2, control_col3 = st.columns(3)

with control_col1:
    result_view = st.selectbox(
        "Result View",
        [
            "All Results",
            "Lottery Only",
            "Football Only",
            "Model Scored Only",
        ]
    )

with control_col2:
    lottery_game_filter = "All"

    if not recent_lottery_df.empty and "GameName" in recent_lottery_df.columns:
        lottery_game_filter = st.selectbox(
            "Lottery Game",
            ["All"] + sorted(
                recent_lottery_df["GameName"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        )
    else:
        st.selectbox(
            "Lottery Game",
            ["All"]
        )

with control_col3:
    football_league_filter = "All"

    if not recent_football_df.empty and "League" in recent_football_df.columns:
        football_league_filter = st.selectbox(
            "Football League",
            ["All"] + sorted(
                recent_football_df["League"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        )
    else:
        st.selectbox(
            "Football League",
            ["All"]
        )


filtered_lottery_df = recent_lottery_df.copy()

if (
    lottery_game_filter != "All"
    and not filtered_lottery_df.empty
    and "GameName" in filtered_lottery_df.columns
):
    filtered_lottery_df = filtered_lottery_df[
        filtered_lottery_df["GameName"].astype(str) == lottery_game_filter
    ].copy()


filtered_football_df = recent_football_df.copy()

if (
    football_league_filter != "All"
    and not filtered_football_df.empty
    and "League" in filtered_football_df.columns
):
    filtered_football_df = filtered_football_df[
        filtered_football_df["League"].astype(str) == football_league_filter
    ].copy()


st.markdown(
    """<div class="hgh-pill-row"><span class="hgh-pill">Last 7 Days</span><span class="hgh-pill">Lottery Draws</span><span class="hgh-pill">Football Outcomes</span><span class="hgh-pill">Model Tracking</span></div>""",
    unsafe_allow_html=True
)

st.divider()


# =========================================================
# CARD RENDERERS
# =========================================================

def render_lottery_result_card(row):
    game_name = safe_text(
        row.get("GameName", row.get("GameFamily", "Lottery"))
    )

    draw_type = safe_text(
        row.get("DrawType", "")
    )

    draw_date = format_date(
        row.get("DrawDate")
    )

    jackpot = format_currency(
        row.get("Jackpot")
    )

    outcome = safe_text(
        row.get("Outcome", "-")
    )

    numbers = []

    for col in [
        "N1",
        "N2",
        "N3",
        "N4",
        "N5",
        "N6",
    ]:
        if col in row.index:
            number = safe_number(
                row.get(col)
            )

            if number != "-":
                numbers.append(number)

    bonus = safe_number(
        row.get("Bonus")
    )

    ball_html = ""

    for number in numbers:
        ball_html += (
            f'<span class="hgh-lottery-ball">'
            f'{str(number).zfill(2)}'
            f'</span>'
        )

    if bonus != "-":
        ball_html += (
            f'<span class="hgh-lottery-ball hgh-lottery-ball-bonus">'
            f'{str(bonus).zfill(2)}'
            f'</span>'
        )

    html_card = f"""
<div class="hgh-result-card">
<div class="hgh-result-topline">
<div>
<div class="hgh-result-kicker">{game_name}</div>
<div class="hgh-result-date">{draw_date}</div>
</div>
<div class="hgh-result-badge">{draw_type}</div>
</div>

<div class="hgh-lottery-balls">
{ball_html}
</div>

<div class="hgh-result-meta-grid">
<div class="hgh-result-meta">
<div class="hgh-result-meta-label">Jackpot</div>
<div class="hgh-result-meta-value">{jackpot}</div>
</div>
<div class="hgh-result-meta">
<div class="hgh-result-meta-label">Outcome</div>
<div class="hgh-result-meta-value">{outcome}</div>
</div>
<div class="hgh-result-meta">
<div class="hgh-result-meta-label">Source</div>
<div class="hgh-result-meta-value">Official</div>
</div>
</div>
</div>
"""

    st.markdown(
        html_card,
        unsafe_allow_html=True
    )


def render_football_result_card(row):
    league = safe_text(
        row.get("League", "Football")
    )

    country = safe_text(
        row.get("Country", "-")
    )

    match_date = format_date(
        row.get("MatchDate")
    )

    home_team = safe_text(
        row.get("HomeTeam")
    )

    away_team = safe_text(
        row.get("AwayTeam")
    )

    home_goals = safe_number(
        row.get("HomeGoals")
    )

    away_goals = safe_number(
        row.get("AwayGoals")
    )

    result_label = safe_text(
        row.get("ResultLabel", "-")
    )

    total_goals = safe_number(
        row.get("TotalGoals")
    )

    total_corners = safe_number(
        row.get("TotalCorners")
    )

    btts = "Yes" if safe_number(row.get("BTTS"), 0) == 1 else "No"

    html_card = f"""
<div class="hgh-result-card">
<div class="hgh-result-topline">
<div>
<div class="hgh-result-kicker">{league}</div>
<div class="hgh-result-date">{country} • {match_date}</div>
</div>
<div class="hgh-result-badge">{result_label}</div>
</div>

<div class="hgh-football-scoreline">
<div class="hgh-football-team">{home_team}</div>
<div class="hgh-football-score">{home_goals} - {away_goals}</div>
<div class="hgh-football-team hgh-football-team-away">{away_team}</div>
</div>

<div class="hgh-result-meta-grid">
<div class="hgh-result-meta">
<div class="hgh-result-meta-label">Total Goals</div>
<div class="hgh-result-meta-value">{total_goals}</div>
</div>
<div class="hgh-result-meta">
<div class="hgh-result-meta-label">Corners</div>
<div class="hgh-result-meta-value">{total_corners}</div>
</div>
<div class="hgh-result-meta">
<div class="hgh-result-meta-label">BTTS</div>
<div class="hgh-result-meta-value">{btts}</div>
</div>
</div>
</div>
"""

    st.markdown(
        html_card,
        unsafe_allow_html=True
    )


def render_scored_prediction_card(row):
    league = safe_text(
        row.get("League", "Football")
    )

    fixture_date = format_date(
        row.get("FixtureDate")
    )

    home_team = safe_text(
        row.get("HomeTeam")
    )

    away_team = safe_text(
        row.get("AwayTeam")
    )

    predicted_result = safe_text(
        row.get("PredictedResult")
    )

    actual_result = safe_text(
        row.get("ActualResult")
    )

    result_hit = safe_number(
        row.get("ResultHit"),
        0
    )

    goals_hit = safe_number(
        row.get("GoalsHit"),
        0
    )

    corners_hit = safe_number(
        row.get("CornersHit"),
        0
    )

    result_status = (
        '<span class="hgh-hit-good">✔ Hit</span>'
        if result_hit == 1
        else '<span class="hgh-hit-bad">✖ Miss</span>'
    )

    goals_status = (
        '<span class="hgh-hit-good">✔ Goals</span>'
        if goals_hit == 1
        else '<span class="hgh-hit-bad">✖ Goals</span>'
    )

    corners_status = (
        '<span class="hgh-hit-good">✔ Corners</span>'
        if corners_hit == 1
        else '<span class="hgh-hit-bad">✖ Corners</span>'
    )

    html_card = f"""
<div class="hgh-result-card">
<div class="hgh-result-topline">
<div>
<div class="hgh-result-kicker">{league}</div>
<div class="hgh-result-date">{fixture_date}</div>
</div>
<div class="hgh-result-badge">Model Scored</div>
</div>

<div class="hgh-football-scoreline">
<div class="hgh-football-team">{home_team}</div>
<div class="hgh-football-score">VS</div>
<div class="hgh-football-team hgh-football-team-away">{away_team}</div>
</div>

<div class="hgh-result-meta-grid">
<div class="hgh-result-meta">
<div class="hgh-result-meta-label">Prediction</div>
<div class="hgh-result-meta-value">{predicted_result}</div>
</div>
<div class="hgh-result-meta">
<div class="hgh-result-meta-label">Actual</div>
<div class="hgh-result-meta-value">{actual_result}</div>
</div>
<div class="hgh-result-meta">
<div class="hgh-result-meta-label">Outcome</div>
<div class="hgh-result-meta-value">{result_status}</div>
</div>
</div>

<div class="hgh-pill-row">
<span class="hgh-pill">{goals_status}</span>
<span class="hgh-pill">{corners_status}</span>
</div>

</div>
"""

    st.markdown(
        html_card,
        unsafe_allow_html=True
    )


# =========================================================
# MAIN TABS
# =========================================================

overview_tab, lottery_tab, football_tab, scored_tab, charts_tab = st.tabs(
    [
        "🔥 Overview",
        "🎲 Lottery",
        "⚽ Football",
        "🎯 Model Scored",
        "📈 Analytics",
    ]
)


with overview_tab:
    st.markdown("## 🔥 Recent Results Feed")

    feed_col1, feed_col2 = st.columns(2)

    with feed_col1:
        st.markdown("### 🎲 Latest Lottery Draws")

        if filtered_lottery_df.empty:
            st.warning("No lottery results found for the last 7 days.")
        else:
            lottery_feed = filtered_lottery_df.sort_values(
                by="DrawDate",
                ascending=False
            ).head(6)

            for _, row in lottery_feed.iterrows():
                render_lottery_result_card(row)

    with feed_col2:
        st.markdown("### ⚽ Latest Football Results")

        if filtered_football_df.empty:
            st.warning("No football results found for the last 7 days.")
        else:
            football_feed = filtered_football_df.sort_values(
                by="MatchDate",
                ascending=False
            ).head(6)

            for _, row in football_feed.iterrows():
                render_football_result_card(row)


with lottery_tab:
    st.markdown("## 🎲 Lottery Results")

    if filtered_lottery_df.empty:
        st.warning("No lottery results found.")
    else:
        filtered_lottery_df = filtered_lottery_df.sort_values(
            by="DrawDate",
            ascending=False
        )

        for _, row in filtered_lottery_df.head(30).iterrows():
            render_lottery_result_card(row)


with football_tab:
    st.markdown("## ⚽ Football Results")

    if filtered_football_df.empty:
        st.warning("No football results found.")
    else:
        filtered_football_df = filtered_football_df.sort_values(
            by="MatchDate",
            ascending=False
        )

        for _, row in filtered_football_df.head(30).iterrows():
            render_football_result_card(row)


with scored_tab:
    st.markdown("## 🎯 Model Scored Results")

    if football_backtest_df.empty:
        st.warning(
            "No scored football predictions yet. This will populate once archived predictions have completed results."
        )
    else:
        scored_df = football_backtest_df.copy()

        if "FixtureDate" in scored_df.columns:
            scored_df = scored_df.sort_values(
                by="FixtureDate",
                ascending=False
            )

        for _, row in scored_df.head(30).iterrows():
            render_scored_prediction_card(row)


with charts_tab:
    st.markdown("## 📈 Results Analytics")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        if not filtered_lottery_df.empty and "GameName" in filtered_lottery_df.columns:
            lottery_volume = (
                filtered_lottery_df
                .groupby("GameName")
                .size()
                .reset_index(name="Draws")
                .sort_values("Draws", ascending=False)
            )

            plot_bar_chart(
                lottery_volume,
                x_col="GameName",
                y_col="Draws",
                title="Lottery Draws by Game",
                height=420
            )
        else:
            section_card(
                "Lottery Analytics",
                "No lottery analytics available for the selected filter.",
                "🎲"
            )

    with chart_col2:
        if not filtered_football_df.empty and "ResultLabel" in filtered_football_df.columns:
            result_distribution = (
                filtered_football_df
                .groupby("ResultLabel")
                .size()
                .reset_index(name="Matches")
                .sort_values("Matches", ascending=False)
            )

            plot_bar_chart(
                result_distribution,
                x_col="ResultLabel",
                y_col="Matches",
                title="Football Result Distribution",
                height=420
            )
        else:
            section_card(
                "Football Analytics",
                "No football analytics available for the selected filter.",
                "⚽"
            )


st.divider()

section_card(
    "Results Page Direction",
    (
        "This page now behaves like a premium results feed instead of a raw table. "
        "The detailed datasets still exist in the backend, but the user experience focuses "
        "on readable recent outcomes and model performance."
    ),
    "🚀"
)