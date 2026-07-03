from __future__ import annotations

import streamlit as st


def hero_banner(
    kicker: str,
    title: str,
    subtitle: str,
    small: bool = True,
):
    if small:
        st.markdown(
            f"""
<div class="hgh-premium-hero-small">
    <div class="hgh-hero-kicker">{kicker}</div>
    <h1 class="hgh-hero-title-small">{title}</h1>
    <p class="hgh-hero-subtitle-small">{subtitle}</p>
</div>
""",
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
<div class="hgh-premium-hero">
    <div class="hgh-hero-left">
        <div class="hgh-hero-kicker">{kicker}</div>
        <h1 class="hgh-hero-title">{title}</h1>
        <p class="hgh-hero-subtitle">{subtitle}</p>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )