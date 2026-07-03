from __future__ import annotations

import streamlit as st


def status_card(
    title: str,
    value: str,
    healthy: bool = True,
):
    colour = "#00d26a" if healthy else "#ff5b5b"

    st.markdown(
        f"""
<div style="
padding:18px;
border-radius:14px;
border:1px solid {colour};
background:#111827;
margin-bottom:10px;
">
<b>{title}</b><br>
<span style="color:{colour};font-size:18px;">
{value}
</span>
</div>
""",
        unsafe_allow_html=True,
    )