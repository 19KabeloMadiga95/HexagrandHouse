import pandas as pd
import plotly.express as px
import streamlit as st


def plot_bar_chart(
    df,
    x_col,
    y_col,
    title="",
    height=420
):
    if df.empty:
        st.warning("No chart data available.")
        return

    chart_df = df.copy()

    chart_df[y_col] = pd.to_numeric(
        chart_df[y_col],
        errors="coerce"
    )

    chart_df = chart_df.dropna(
        subset=[x_col, y_col]
    )

    if chart_df.empty:
        st.warning("No valid chart data available.")
        return

    fig = px.bar(
        chart_df,
        x=x_col,
        y=y_col,
        title=title,
        text=y_col,
    )

    fig.update_layout(
        height=height,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#F5F7FA"
        ),
        title=dict(
            font=dict(
                color="#F2CF63",
                size=18
            )
        ),
        xaxis=dict(
            tickangle=0,
            gridcolor="rgba(255,255,255,0.08)",
            showticklabels=False
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.08)"
        ),
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=90
        ),
    )

    fig.update_traces(
        marker_line_width=0,
        texttemplate="%{text:.2f}",
        textposition="outside",
        textfont=dict(size=10),
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )


def plot_horizontal_bar_chart(
    df,
    x_col,
    y_col,
    title="",
    height=420
):
    if df.empty:
        st.warning("No chart data available.")
        return

    chart_df = df.copy()

    chart_df[x_col] = pd.to_numeric(
        chart_df[x_col],
        errors="coerce"
    )

    chart_df = chart_df.dropna(
        subset=[x_col, y_col]
    )

    if chart_df.empty:
        st.warning("No valid chart data available.")
        return

    fig = px.bar(
        chart_df,
        x=x_col,
        y=y_col,
        orientation="h",
        title=title,
        text=x_col,
    )

    fig.update_layout(
        height=height,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#F5F7FA"
        ),
        title=dict(
            font=dict(
                color="#F2CF63",
                size=18
            )
        ),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.08)"
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.08)"
        ),
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=30
        ),
    )

    fig.update_traces(
        marker_line_width=0,
        texttemplate="%{text:.2f}",
        textposition="outside",
        textfont=dict(size=10),
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )


def plot_line_chart(
    df,
    x_col,
    y_col,
    title="",
    height=420
):
    if df.empty:
        st.warning("No chart data available.")
        return

    chart_df = df.copy()

    chart_df[y_col] = pd.to_numeric(
        chart_df[y_col],
        errors="coerce"
    )

    chart_df = chart_df.dropna(
        subset=[x_col, y_col]
    )

    if chart_df.empty:
        st.warning("No valid chart data available.")
        return

    fig = px.line(
        chart_df,
        x=x_col,
        y=y_col,
        title=title,
        markers=True,
    )

    fig.update_layout(
        height=height,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="#F5F7FA"
        ),
        title=dict(
            font=dict(
                color="#F2CF63",
                size=18
            )
        ),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.08)"
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.08)"
        ),
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=60
        ),
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )