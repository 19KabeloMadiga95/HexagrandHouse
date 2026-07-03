from __future__ import annotations

import streamlit as st


def select_filter(
    label: str,
    options: list,
    key: str | None = None,
    default_index: int = 0,
):
    """
    Standard single select filter.
    """

    if not options:
        options = ["All"]

    return st.selectbox(
        label,
        options,
        index=min(default_index, len(options) - 1),
        key=key,
    )


def multi_filter(
    label: str,
    options: list,
    default=None,
    key: str | None = None,
):
    """
    Standard multiselect.
    """

    return st.multiselect(
        label,
        options,
        default=default,
        key=key,
    )


def filter_columns(count: int):
    """
    Create evenly spaced filter columns.
    """

    return st.columns(count)