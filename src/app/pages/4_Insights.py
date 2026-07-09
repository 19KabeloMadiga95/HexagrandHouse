from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from src.app.utils.page import configure_page, refresh_chip
from src.app.utils.sqlite_runtime import cached_table, count_rows, sort_by_date
from src.app.components.website import hero, mini_cards, section_label, friendly_table, empty_message, page_footer

configure_page("Insights", "▥")
refresh_chip()


@st.cache_data(ttl=300, show_spinner=False)
def load_insights():
    lottery_leaderboard = cached_table("lottery_model_leaderboard", limit=100)
    lottery_summary = cached_table("lottery_model_dashboard_summary", limit=100)
    football_kpis = cached_table("football_performance_kpis", limit=100)
    football_summary = cached_table("football_performance_dashboard_summary", limit=100)
    football_notes = sort_by_date(cached_table("football_performance_notes", limit=50))
    platform_log = sort_by_date(cached_table("platform_run_log", limit=100))
    return lottery_leaderboard, lottery_summary, football_kpis, football_summary, football_notes, platform_log


lottery_leaderboard, lottery_summary, football_kpis, football_summary, football_notes, platform_log = load_insights()

lottery_rows = count_rows("lottery_predictions")
football_rows = count_rows("football_fixture_predictions") or count_rows("football_ensemble_predictions")
model_rows = len(lottery_leaderboard) + len(football_kpis)
run_rows = count_rows("platform_run_log")

hero(
    "Insights",
    "Model accuracy, performance trends, platform status, and operational intelligence for the public dashboard.",
    eyebrow="Platform intelligence",
    chips=["Accuracy", "Coverage", "Model notes", "Runtime health"],
    metrics=[
        {"value": f"{lottery_rows:,}", "label": "Lottery outputs"},
        {"value": f"{football_rows:,}", "label": "Football outputs"},
        {"value": f"{model_rows:,}", "label": "Model insight rows"},
        {"value": f"{run_rows:,}", "label": "Refresh logs"},
    ],
)

mini_cards([
    {"icon": "◎", "label": "Overall", "value": "Live", "note": "runtime data"},
    {"icon": "✤", "label": "Lottery", "value": f"{lottery_rows:,}", "note": "prediction rows"},
    {"icon": "⚽", "label": "Football", "value": f"{football_rows:,}", "note": "current or model rows"},
    {"icon": "✓", "label": "Best practice", "value": "Current only", "note": "no stale public football"},
])

section_label("Prediction Performance", "High-level performance and operational summaries.")
left, right = st.columns([1.15, .85], gap="large")

with left:
    st.markdown(
        """
        <div class="hgb-card">
            <div class="hgb-progress-row"><div><b>Overall Accuracy View</b><br/><span>Use this area to review latest model dashboard rows and model leaderboard output.</span></div><span class="hgb-pill">Model layer</span></div>
            <div class="hgb-progress-row"><div><b>Lottery Performance</b><br/><span>Lottery predictions are refreshed daily and displayed as grouped tickets/results.</span></div><span class="hgb-pill">Active</span></div>
            <div class="hgb-progress-row"><div><b>Football Guardrail</b><br/><span>Public football cards only use current/future fixture predictions.</span></div><span class="hgb-pill">Protected</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    if not platform_log.empty:
        section_label("Latest Runs", "Most recent automation log rows.")
        friendly_table(platform_log, ["RunID", "StepName", "Status", "StartedAt", "FinishedAt", "RowsAffected"], height=265, limit=8)
    else:
        empty_message("No run log available", "Platform run log will show after refresh cycles.")

cols = st.columns([1, 1, 1], gap="medium")
with cols[0]:
    section_label("Model Leaderboard", "Lottery model leaderboard table.")
    friendly_table(lottery_leaderboard, list(lottery_leaderboard.columns[:6]) if not lottery_leaderboard.empty else [], height=330, limit=12)
with cols[1]:
    section_label("Game Coverage", "Dashboard summary rows.")
    friendly_table(lottery_summary, list(lottery_summary.columns[:6]) if not lottery_summary.empty else [], height=330, limit=12)
with cols[2]:
    section_label("Football KPIs", "Football performance KPI rows.")
    friendly_table(football_kpis if not football_kpis.empty else football_summary, list((football_kpis if not football_kpis.empty else football_summary).columns[:6]) if not (football_kpis if not football_kpis.empty else football_summary).empty else [], height=330, limit=12)

section_label("Platform Notes", "Operational notes and model updates.")
if football_notes.empty:
    empty_message("No notes yet", "Platform notes will populate as report tables are refreshed.")
else:
    friendly_table(football_notes, list(football_notes.columns[:6]), height=260, limit=20)

page_footer()
