from datetime import datetime
from pathlib import Path

import streamlit as st


def kpi_card(
    title,
    value,
    subtitle="",
    icon="📊"
):
    st.markdown(
        f"""
<div class="hgh-kpi-card">
    <div class="hgh-kpi-icon">{icon}</div>
    <div class="hgh-kpi-label">{title}</div>
    <div class="hgh-kpi-value">{value}</div>
    <div class="hgh-kpi-subtitle">{subtitle}</div>
</div>
""",
        unsafe_allow_html=True
    )


def section_card(
    title,
    body,
    icon="📌"
):
    st.markdown(
        f"""
<div class="hgh-card">
    <div class="hgh-card-title">{icon} {title}</div>
    <div class="hgh-card-body">{body}</div>
</div>
""",
        unsafe_allow_html=True
    )


def status_card(
    title,
    status="Operational",
    icon="✅"
):
    status_class = "hgh-status-operational"

    if str(status).lower() in [
        "warning",
        "pending",
        "limited"
    ]:
        status_class = "hgh-status-warning"

    if str(status).lower() in [
        "failed",
        "error",
        "offline"
    ]:
        status_class = "hgh-status-error"

    st.markdown(
        f"""
<div class="hgh-card">
    <div class="hgh-card-title">{icon} {title}</div>
    <div class="{status_class}">{status}</div>
</div>
""",
        unsafe_allow_html=True
    )


def hero_banner(
    title,
    subtitle,
    icon="🎯"
):
    st.markdown(
        f"""
<div class="hgh-hero">
    <div class="hgh-hero-title">{icon} {title}</div>
    <div class="hgh-hero-subtitle">{subtitle}</div>
</div>
""",
        unsafe_allow_html=True
    )


def render_sidebar_branding():
    st.sidebar.markdown(
        """
<div class="hgh-sidebar-brand">
    <div class="hgh-sidebar-logo">H</div>
    <div>
        <div class="hgh-sidebar-title">HEXAGRANDBET</div>
        <div class="hgh-sidebar-subtitle">DATA. INSIGHT. PLAY SMART.</div>
    </div>
</div>
""",
        unsafe_allow_html=True
    )

    st.sidebar.markdown("---")


def last_refresh_card(
    label="Last Refresh",
    value=None
):
    if value is None:
        value = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    st.markdown(
        f"""
<div class="hgh-refresh-card">
    <span>{label}</span>
    <strong>{value}</strong>
</div>
""",
        unsafe_allow_html=True
    )


def page_section_title(
    title,
    subtitle="",
    icon="📌"
):
    st.markdown(
        f"""
<div class="hgh-section-heading">
    <div class="hgh-section-heading-title">{icon} {title}</div>
    <div class="hgh-section-heading-subtitle">{subtitle}</div>
</div>
""",
        unsafe_allow_html=True
    )