from __future__ import annotations
from pathlib import Path
import sys
from datetime import datetime
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]
APP_DIR = Path(__file__).resolve().parents[1]
LOGO_PATH = APP_DIR / "assets" / "hexagrandhouse_logo.png"

NAV_ITEMS = [
    ("pages/1_Home.py", "Command Centre", "🏠"),
    ("pages/2_Lottery.py", "Lottery Intelligence", "🎲"),
    ("pages/3_Football.py", "Football Intelligence", "⚽"),
    ("pages/3_Results.py", "Analytics", "📈"),
    ("pages/7_Model_Accuracy.py", "Accuracy", "🎯"),
    ("pages/4_Responsible_Play.py", "Responsible Play", "🛡️"),
    ("pages/99_Admin.py", "Administration", "⚙️"),
]

def ensure_project_root():
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

def load_css():
    css_path = APP_DIR / "styles" / "main.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="hgh-side-shell">', unsafe_allow_html=True)
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=58)
        st.markdown(
            '<div class="hgh-side-title">HEXAGRANDHOUSE</div>'
            '<div class="hgh-side-sub">Prediction Intelligence</div>'
            '<div class="hgh-side-rule"></div>',
            unsafe_allow_html=True,
        )
        valid_icons = {"🏠", "🎲", "⚽", "📈", "🎯", "🛡️", "⚙️"}
        for page, label, icon in NAV_ITEMS:
            if icon in valid_icons:
                st.page_link(page, label=label, icon=icon)
            else:
                st.page_link(page, label=label)
        st.markdown(
            '<div class="hgh-side-rule"></div>'
            '<div class="hgh-side-status"><span class="hgh-online-dot"></span> Database online</div>'
            '<div class="hgh-side-version">HexagrandHouse v4 workspace</div>'
            '</div>',
            unsafe_allow_html=True,
        )

def configure_page(title: str, icon: str = "🏠"):
    ensure_project_root()
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    load_css()
    render_sidebar()

def refresh_chip(label: str = "Last refresh", value: str | None = None):
    if value is None:
        value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(
        f'<div class="hgh-topbar"><div class="hgh-refresh-chip">{label}: <b>{value}</b></div></div>',
        unsafe_allow_html=True,
    )
