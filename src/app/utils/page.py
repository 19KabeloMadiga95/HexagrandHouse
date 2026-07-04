from pathlib import Path
import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[1]

def load_css() -> None:
    css_path = APP_ROOT / "styles" / "main.css"

    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


NAV_ITEMS = [
    ("pages/1_Home.py", "Command Centre", "🏠"),
    ("pages/2_Lottery.py", "Lottery Intelligence", "🎲"),
    ("pages/3_Football.py", "Football Intelligence", "⚽"),
    ("pages/3_Results.py", "Analytics", "📈"),
    ("pages/7_Model_Accuracy.py", "Accuracy", "🎯"),
    ("pages/4_Responsible_Play.py", "Responsible Play", "🛡️"),
    ("pages/99_Admin.py", "Administration", "⚙️"),
]


def _safe_page_link(page: str, label: str, icon: str | None = None) -> None:
    try:
        if icon:
            st.page_link(page, label=label, icon=icon)
        else:
            st.page_link(page, label=label)
    except Exception:
        if st.button(f"{icon or ''} {label}", key=f"nav_{label}"):
            st.switch_page(page)


def render_sidebar() -> None:
    with st.sidebar:
        st.image(str(APP_ROOT / "assets" / "hexagrandhouse_logo.png"), width=64)
        st.markdown("### HEXAGRANDHOUSE")
        st.caption("Prediction Intelligence")
        st.divider()

        for page, label, icon in NAV_ITEMS:
            _safe_page_link(page, label, icon)

        st.divider()
        st.success("Database online")
        st.caption("HexagrandHouse v4 workspace")

def refresh_chip(label: str = "Last Refresh", value: str | None = None) -> None:
    if value is None:
        value = "-"

    st.markdown(
        f"""
        <div class="hgh-refresh-chip">
            <span>{label}</span>
            <strong>{value}</strong>
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