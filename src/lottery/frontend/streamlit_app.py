from pathlib import Path

import streamlit as st


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="HexagrandHouse",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# LOAD CSS
# =========================================================

def load_main_css():

    css_path = (
        Path(__file__).resolve().parent
        / "styles"
        / "main.css"
    )

    with open(css_path, "r", encoding="utf-8") as f:

        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )


load_main_css()


# =========================================================
# SIDEBAR BRANDING
# =========================================================

st.logo(
    "https://img.icons8.com/fluency/96/trophy.png"
)

st.sidebar.markdown(
    """
<div style="padding-top:10px;"></div>

<h1 style="
    color:white;
    font-size:28px;
    font-weight:900;
    margin-bottom:0;
">
HexagrandHouse
</h1>

<p style="
    color:#9db0ca;
    margin-top:4px;
    font-size:13px;
">
Premium Analytics Platform
</p>
""",
    unsafe_allow_html=True
)

st.sidebar.divider()

st.switch_page("pages/1_Home.py")