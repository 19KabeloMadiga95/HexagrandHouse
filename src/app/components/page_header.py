from __future__ import annotations

import streamlit as st

from src.app.components.hero_banner import hero_banner


def page_header(
    kicker: str,
    title: str,
    subtitle: str,
):
    hero_banner(
        kicker=kicker,
        title=title,
        subtitle=subtitle,
    )

    st.divider()