from __future__ import annotations
import html
import pandas as pd
import streamlit as st


def _safe(value, default="-"):
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat", ""}:
        return default
    return html.escape(text)


def _num(value):
    try:
        return int(float(value))
    except Exception:
        return value


def compact_header(eyebrow, title, subtitle="", tags=None, metrics=None):
    tags = tags or []
    metrics = metrics or []
    tag_html = "".join(f'<span class="hgh-chip">{_safe(t)}</span>' for t in tags)
    metric_html = "".join(
        '<div class="hgh-stat-mini">'
        f'<div class="hgh-stat-label">{_safe(m.get("label"))}</div>'
        f'<div class="hgh-stat-value">{_safe(m.get("value"))}</div>'
        f'<div class="hgh-stat-note">{_safe(m.get("note", ""))}</div>'
        '</div>'
        for m in metrics[:4]
    )
    st.markdown(
        '<section class="hgh-command">'
        '<div class="hgh-command-copy">'
        f'<div class="hgh-eyebrow">{_safe(eyebrow)}</div>'
        f'<h1>{_safe(title)}</h1>'
        f'<p>{_safe(subtitle)}</p>'
        f'<div class="hgh-chip-row">{tag_html}</div>'
        '</div>'
        f'<div class="hgh-stat-stack">{metric_html}</div>'
        '</section>',
        unsafe_allow_html=True,
    )


def kpi_grid(items):
    html_items = []
    for item in items:
        html_items.append(
            '<div class="hgh-kpi">'
            f'<div class="hgh-kpi-head"><span>{_safe(item.get("icon", "⬢"))}</span><b>{_safe(item.get("title"))}</b></div>'
            f'<div class="hgh-kpi-value">{_safe(item.get("value"))}</div>'
            f'<div class="hgh-kpi-sub">{_safe(item.get("sub", ""))}</div>'
            '</div>'
        )
    st.markdown('<div class="hgh-kpi-grid">' + ''.join(html_items) + '</div>', unsafe_allow_html=True)


def section_title(text, icon=""):
    st.markdown(f'<div class="hgh-section-title"><span>{_safe(icon)}</span>{_safe(text)}</div>', unsafe_allow_html=True)


def empty_state(title="No data available", detail="This area will populate when the source provides data.", icon="◎"):
    st.markdown(
        f'<div class="hgh-empty"><div class="hgh-empty-icon">{_safe(icon)}</div><div><b>{_safe(title)}</b><p>{_safe(detail)}</p></div></div>',
        unsafe_allow_html=True,
    )


def number_balls(row, regular_cols=None, bonus_col="Bonus"):
    regular_cols = regular_cols or [c for c in ["N1", "N2", "N3", "N4", "N5", "N6"] if c in row.index]
    balls = []
    for col in regular_cols:
        val = row.get(col)
        if pd.notna(val):
            val = _num(val)
            balls.append(f'<span class="hgh-ball">{_safe(f"{val:02}" if isinstance(val, int) else val)}</span>')
    if bonus_col in row.index and pd.notna(row.get(bonus_col)):
        val = _num(row.get(bonus_col))
        balls.append(f'<span class="hgh-ball hgh-ball-bonus">{_safe(f"{val:02}" if isinstance(val, int) else val)}</span>')
    return '<div class="hgh-balls">' + ''.join(balls) + '</div>'


def lottery_ticket(row, rank=1, dense=False):
    game = row.get("GameDisplay", row.get("GameName", row.get("GameFamily", "Lottery")))
    model = row.get("SourceType", row.get("ModelVersion", row.get("ModelName", "Model")))
    score = row.get("EnsembleScore", row.get("Confidence", row.get("PredictionScore", row.get("RawScore", "-"))))
    generated = row.get("GeneratedAt", "-")
    reg_sum = row.get("RegularSum", "-")
    odd = row.get("OddCount", "-")
    even = row.get("EvenCount", "-")
    high = row.get("HighCount", "-")
    low = row.get("LowCount", "-")
    st.markdown(
        '<article class="hgh-ticket">'
        '<div class="hgh-ticket-top">'
        f'<div><div class="hgh-card-kicker">{_safe(game)}</div><h3>Prediction ticket</h3></div>'
        f'<div class="hgh-score-pill">#{rank}</div>'
        '</div>'
        '<div class="hgh-ticket-main">'
        f'{number_balls(row)}'
        '<div class="hgh-ticket-score">'
        '<span>Score</span>'
        f'<b>{_safe(score)}</b>'
        '</div>'
        '</div>'
        '<div class="hgh-ticket-meta">'
        f'<span>Sum <b>{_safe(reg_sum)}</b></span>'
        f'<span>Odd/Even <b>{_safe(odd)}/{_safe(even)}</b></span>'
        f'<span>High/Low <b>{_safe(high)}/{_safe(low)}</b></span>'
        f'<span>Model <b>{_safe(model)}</b></span>'
        f'<span>Generated <b>{_safe(generated)}</b></span>'
        '</div>'
        '</article>',
        unsafe_allow_html=True,
    )


def lottery_card(row, rank=1):
    lottery_ticket(row, rank)


def football_card(row, rank=1):
    home = row.get("HomeTeam", row.get("Home", "Home"))
    away = row.get("AwayTeam", row.get("Away", "Away"))
    league = row.get("League", row.get("Competition", "Football"))
    pick = row.get("PrimaryMarketSignal", row.get("PredictedResult", row.get("BestResultPick", row.get("ModelPick", "Signal"))))
    confidence = row.get("EnsembleConfidenceScore", row.get("ConfidenceScore", row.get("Confidence", "-")))
    try:
        c = float(confidence)
        conf_disp = f"{c:.1%}" if c <= 1 else f"{c:.1f}%"
    except Exception:
        conf_disp = confidence
    st.markdown(
        '<article class="hgh-match-card">'
        '<div class="hgh-ticket-top">'
        f'<div><div class="hgh-card-kicker">{_safe(league)}</div></div>'
        f'<div class="hgh-score-pill">#{rank}</div>'
        '</div>'
        '<div class="hgh-match-grid">'
        f'<div class="hgh-team">{_safe(home)}</div>'
        f'<div class="hgh-pick"><span>Primary Signal</span><b>{_safe(pick)}</b></div>'
        f'<div class="hgh-team right">{_safe(away)}</div>'
        '</div>'
        f'<div class="hgh-confidence-bar"><span style="width:min(100%, {_safe(conf_disp).replace("%", "")}%)"></span></div>'
        f'<div class="hgh-match-foot"><span>Confidence</span><b>{_safe(conf_disp)}</b></div>'
        '</article>',
        unsafe_allow_html=True,
    )


def dataframe_card(df, height=260, limit=50, empty_title="No records"):
    if df is None or df.empty:
        empty_state(empty_title)
        return
    st.dataframe(df.head(limit), use_container_width=True, height=height)


def _num_ball_html(value, bonus=False):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    try:
        label = f"{int(float(value)):02}"
    except Exception:
        label = _safe(value)
    klass = "hgh-mini-ball hgh-mini-ball-bonus" if bonus else "hgh-mini-ball"
    return f'<span class="{klass}">{label}</span>'


def _lottery_numbers_html(row):
    balls = []
    for col in ["N1", "N2", "N3", "N4", "N5", "N6"]:
        if col in row.index:
            balls.append(_num_ball_html(row.get(col)))
    if "Bonus" in row.index and pd.notna(row.get("Bonus")):
        balls.append(_num_ball_html(row.get("Bonus"), bonus=True))
    return '<div class="hgh-table-balls">' + ''.join([b for b in balls if b]) + '</div>'


def compact_lottery_table(df, kind="predictions", limit=60):
    if df is None or df.empty:
        empty_state("No rows", "No lottery rows are available for this view.")
        return

    frame = df.head(limit).copy()
    rows = []
    if kind == "results":
        header = "<tr><th>Date</th><th>Game</th><th>Numbers</th><th>Draw</th></tr>"
        for _, row in frame.iterrows():
            rows.append(
                "<tr>"
                f"<td>{_safe(row.get('DrawDate'))}</td>"
                f"<td><b>{_safe(row.get('GameName', row.get('GameDisplay', row.get('GameFamily'))))}</b></td>"
                f"<td>{_lottery_numbers_html(row)}</td>"
                f"<td>{_safe(row.get('DrawType', '-'))}</td>"
                "</tr>"
            )
    else:
        header = "<tr><th>Rank</th><th>Game</th><th>Ticket</th><th>Score</th><th>Signal</th><th>Generated</th></tr>"
        for idx, row in frame.iterrows():
            rank = row.get("PredictionRank", row.get("Rank", idx + 1))
            score = row.get("ConfidenceScore", row.get("EnsembleScore", row.get("Score", row.get("RawScore", "-"))))
            model = row.get("SourceType", row.get("ModelVersion", row.get("ModelName", "Model")))
            rows.append(
                "<tr>"
                f"<td><span class='hgh-rank-badge'>#{_safe(rank)}</span></td>"
                f"<td><b>{_safe(row.get('GameDisplay', row.get('GameName', row.get('GameFamily'))))}</b></td>"
                f"<td>{_lottery_numbers_html(row)}</td>"
                f"<td><b>{_safe(score)}</b></td>"
                f"<td>{_safe(model)}</td>"
                f"<td>{_safe(row.get('GeneratedAt', '-'))}</td>"
                "</tr>"
            )
    st.markdown(
        '<div class="hgh-table-wrap"><table class="hgh-premium-table">'
        f'<thead>{header}</thead><tbody>{"".join(rows)}</tbody></table></div>',
        unsafe_allow_html=True,
    )


def compact_football_table(df, limit=80):
    if df is None or df.empty:
        empty_state("No rows", "No football rows are available for this view.")
        return
    frame = df.head(limit).copy()
    rows = []
    header = "<tr><th>League</th><th>Match</th><th>Pick</th><th>Confidence</th><th>Tier</th></tr>"
    for _, row in frame.iterrows():
        home = row.get("HomeTeam", row.get("Home", "Home"))
        away = row.get("AwayTeam", row.get("Away", "Away"))
        pick = row.get("PrimaryMarketSignal", row.get("PredictedResult", row.get("BestResultPick", row.get("ModelPick", "Signal"))))
        conf = row.get("ConfidenceScore", row.get("EnsembleConfidenceScore", row.get("Confidence", "-")))
        tier = row.get("ConfidenceLabel", row.get("SignalLabel", "-"))
        rows.append(
            "<tr>"
            f"<td>{_safe(row.get('League', '-'))}</td>"
            f"<td><b>{_safe(home)}</b><span class='hgh-vs-inline'>vs</span><b>{_safe(away)}</b></td>"
            f"<td><span class='hgh-pick-badge'>{_safe(pick)}</span></td>"
            f"<td><b>{_safe(conf)}</b></td>"
            f"<td>{_safe(tier)}</td>"
            "</tr>"
        )
    st.markdown(
        '<div class="hgh-table-wrap"><table class="hgh-premium-table">'
        f'<thead>{header}</thead><tbody>{"".join(rows)}</tbody></table></div>',
        unsafe_allow_html=True,
    )
