from pathlib import Path
import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[1]

NAV_ITEMS = [
    ("pages/1_Home.py", "Home", "🏠"),
    ("pages/2_Lottery.py", "Lottery Picks", "🎲"),
    ("pages/3_Football.py", "Football Picks", "⚽"),
    ("pages/3_Results.py", "Results", "📋"),
    ("pages/4_Responsible_Play.py", "Play Smart", "🛡️"),
]

def load_css() -> None:
    css_path = APP_ROOT / "styles" / "main.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )

def _safe_page_link(page: str, label: str, icon: str | None = None) -> None:
    try:
        st.page_link(page, label=label, icon=icon)
    except Exception:
        if st.button(f"{icon or ''} {label}", key=f"nav_{label}"):
            st.switch_page(page)

def render_sidebar() -> None:
    with st.sidebar:
        logo = APP_ROOT / "assets" / "hexagrandhouse_logo.png"
        if logo.exists():
            st.image(str(logo), width=82)

        st.markdown(
            """
            <div class="hh-side-brand">
                <div class="hh-side-title">HEXAGRANDHOUSE</div>
                <div class="hh-side-sub">Simple picks. Clear results.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="hh-side-rule"></div>', unsafe_allow_html=True)

        for page, label, icon in NAV_ITEMS:
            _safe_page_link(page, label, icon)

        st.markdown('<div class="hh-side-rule"></div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="hh-side-note">
                <b>Entertainment only.</b><br/>
                Signals are not guarantees. Keep play optional and controlled.
            </div>
            """,
            unsafe_allow_html=True,
        )

def refresh_chip(label: str = "Updated", value: str | None = None) -> None:
    st.markdown(
        f"""
        <div class="hh-refresh-chip">
            <span>{label}</span>
            <b>{value or "Live"}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

def configure_page(title: str = "HexagrandHouse", icon: str = "🏠") -> None:
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    load_css()
    render_sidebar()
