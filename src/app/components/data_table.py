from __future__ import annotations

import streamlit as st
import pandas as pd


def data_table(
    df: pd.DataFrame,
    height: int = 500,
):
    if df.empty:
        st.info("No records available.")
        return

    st.dataframe(
        df,
        use_container_width=True,
        height=height,
    )