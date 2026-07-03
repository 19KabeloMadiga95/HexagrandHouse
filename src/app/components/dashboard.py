from __future__ import annotations

import streamlit as st

from src.app.components.kpi_cards import kpi_card


def render_kpis(kpis: list[dict]):
    """
    Example:

    render_kpis([
        {"title":"Rows","value":100,"subtitle":"Loaded","icon":"📊"},
        ...
    ])
    """

    cols = st.columns(len(kpis))

    for col, item in zip(cols, kpis):
        with col:
            kpi_card(
                item["title"],
                item["value"],
                item.get("subtitle", ""),
                item.get("icon", "📊"),
            )