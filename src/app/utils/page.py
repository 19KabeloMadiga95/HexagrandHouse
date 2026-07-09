from pathlib import Path
import base64
import html
import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[1]
BRAND_NAME = "HexaGrandBet"
BRAND_TAGLINE = "Lottery & football intelligence"

NAV_ITEMS = [
    ("pages/1_Home.py", "Home", "⌂"),
    ("pages/2_Lottery.py", "Lottery Picks", "✤"),
    ("pages/3_Football.py", "Football Picks", "⚽"),
    ("pages/3_Results.py", "Results Archive", "▣"),
    ("pages/4_Insights.py", "Insights", "▥"),
    ("pages/5_Settings.py", "Settings", "⚙"),
]


def load_css() -> None:
    css_path = APP_ROOT / "styles" / "main.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )


def _nav_button(page: str, label: str, icon: str | None = None, active_label: str | None = None) -> None:
    """Render one consistent sidebar navigation button.

    Streamlit's native page_link renders the active page differently from
    normal links in some versions, which caused mixed button sizes/styles.
    Using buttons + st.switch_page keeps every nav row visually identical
    and gives us a reliable active-page highlight.
    """
    active = (label == active_label) or (active_label == BRAND_NAME and label == "Home")
    display_label = f"{icon or ''} {label}".strip()
    clicked = st.button(
        display_label,
        key=f"hgb_nav_{label.replace(' ', '_').lower()}",
        type="primary" if active else "secondary",
        use_container_width=True,
    )

    if clicked and not active:
        st.switch_page(page)


def _asset_data_uri(path: Path) -> str | None:
    if not path.exists():
        return None
    suffix = path.suffix.lower().replace(".", "") or "png"
    mime = "jpeg" if suffix in {"jpg", "jpeg"} else "png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/{mime};base64,{encoded}"


def render_sidebar(active_label: str | None = None) -> None:
    with st.sidebar:
        logo_icon = _asset_data_uri(APP_ROOT / "assets" / "hexagrandbet_icon.png")

        if logo_icon:
            st.markdown(
                f"""
                <div class="hgb-sidebar-logo-wrap">
                    <img src="{logo_icon}" class="hgb-sidebar-logo" alt="HexaGrandBet logo" />
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="hgb-fallback-logo">HGB</div>', unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="hgb-side-brand">
                <div class="hgb-side-title"><span>Hexa</span>GrandBet</div>
                <div class="hgb-side-sub">{html.escape(BRAND_TAGLINE)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="hgb-side-rule"></div>', unsafe_allow_html=True)

        st.markdown('<div class="hgb-nav-stack">', unsafe_allow_html=True)
        for page, label, icon in NAV_ITEMS:
            _nav_button(page, label, icon, active_label)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="hgb-side-rule"></div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div class="hgb-premium-card">
                <div class="hgb-premium-icon">◇</div>
                <b>Premium Insights</b>
                <span>Advanced analytics, historical trends, and smarter review tools.</span>
                <small>Coming soon</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="hgb-profile-card">
                <div class="hgb-avatar">HGB</div>
                <div><b>HexaGrandBet</b><span>Public analytics</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def refresh_chip(label: str = "Updated", value: str | None = None) -> None:
    st.markdown(
        f"""
        <div class="hgb-topline">
            <div class="hgb-refresh-chip"><i></i><span>{html.escape(label)}</span><b>{html.escape(value or 'Live')}</b></div>
            <div class="hgb-topline-note">18+ • Statistical insights only • No guarantees</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def configure_page(title: str = BRAND_NAME, icon: str = "◆") -> None:
    st.set_page_config(
        page_title=f"{title} | {BRAND_NAME}" if title != BRAND_NAME else BRAND_NAME,
        page_icon=icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    load_css()
    render_sidebar(title)
