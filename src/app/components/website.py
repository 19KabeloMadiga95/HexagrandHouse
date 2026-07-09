from __future__ import annotations

import html
import pandas as pd
import streamlit as st


def safe(value, default="-"):
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "nat"}:
        return default
    return html.escape(text)


def _html(markup: str) -> None:
    # Keep markup as one compact line so Streamlit never treats indented HTML as code.
    compact = " ".join(str(markup).split())
    st.markdown(compact, unsafe_allow_html=True)


def num_label(value):
    try:
        return f"{int(float(value)):02}"
    except Exception:
        return safe(value, "")


def date_label(value, default="-"):
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.notna(parsed):
            return parsed.strftime("%d %b %Y")
    except Exception:
        pass
    return safe(value, default)


def section_label(title: str, subtitle: str = ""):
    sub = f'<p>{safe(subtitle)}</p>' if subtitle else ""
    _html(f'<div class="hh-section-head"><h2>{safe(title)}</h2>{sub}</div>')


def hero(title: str, subtitle: str, eyebrow: str = "HEXAGRANDHOUSE", chips: list[str] | None = None, metrics: list[dict] | None = None):
    chips = chips or []
    metrics = metrics or []
    chip_html = "".join(f'<span>{safe(c)}</span>' for c in chips if safe(c, ""))
    metric_html = "".join(
        f'<div class="hh-hero-stat"><b>{safe(m.get("value"))}</b><span>{safe(m.get("label"))}</span></div>'
        for m in metrics[:4]
    )
    _html(
        f'<section class="hh-hero"><div class="hh-hero-copy"><div class="hh-eyebrow">{safe(eyebrow)}</div>'
        f'<h1>{safe(title)}</h1><p>{safe(subtitle)}</p><div class="hh-chip-row">{chip_html}</div></div>'
        f'<div class="hh-hero-stats">{metric_html}</div></section>'
    )


def mini_cards(items: list[dict]):
    html_items = []
    for item in items:
        html_items.append(
            f'<div class="hh-mini-card"><div class="hh-mini-icon">{safe(item.get("icon", "•"))}</div>'
            f'<div><span>{safe(item.get("label", ""))}</span><b>{safe(item.get("value", "-"))}</b>'
            f'<small>{safe(item.get("note", ""))}</small></div></div>'
        )
    _html(f'<div class="hh-mini-grid">{"".join(html_items)}</div>')


def number_balls(row, bonus_col="Bonus"):
    cols = [c for c in ["N1", "N2", "N3", "N4", "N5", "N6"] if c in row.index]
    balls = []
    for c in cols:
        val = row.get(c)
        if pd.notna(val):
            balls.append(f'<span class="hh-ball">{num_label(val)}</span>')
    if bonus_col in row.index and pd.notna(row.get(bonus_col)):
        balls.append(f'<span class="hh-ball hh-ball-bonus">{num_label(row.get(bonus_col))}</span>')
    if not balls:
        return '<div class="hh-no-balls">Numbers not available yet</div>'
    return '<div class="hh-balls">' + ''.join(balls) + '</div>'


def _valid_meta(value) -> bool:
    text = str(value).strip()
    return text not in ["", "-", "nan", "None", "NaT"]


def lottery_ticket(row, rank: int = 1, compact: bool = False):
    game = row.get("GameName", row.get("GameFamily", "Lottery"))
    draw = row.get("DrawType", "Pick")
    generated = row.get("GeneratedAt", row.get("EnsembleGeneratedAt", ""))
    score = row.get("ConfidenceScore", row.get("EnsembleConfidenceScore", row.get("RawScore", "")))
    reg_sum = row.get("RegularSum", "")
    odd = row.get("OddCount", "")
    even = row.get("EvenCount", "")
    high = row.get("HighCount", "")
    low = row.get("LowCount", "")
    model = row.get("ModelName", row.get("Model", ""))

    meta_items = []
    if _valid_meta(reg_sum):
        meta_items.append(f'<span>Total <b>{safe(reg_sum)}</b></span>')
    if _valid_meta(odd) or _valid_meta(even):
        meta_items.append(f'<span>Odd/Even <b>{safe(odd)}/{safe(even)}</b></span>')
    if _valid_meta(high) or _valid_meta(low):
        meta_items.append(f'<span>High/Low <b>{safe(high)}/{safe(low)}</b></span>')
    if _valid_meta(score):
        meta_items.append(f'<span>Score <b>{safe(score)}</b></span>')
    if _valid_meta(model):
        meta_items.append(f'<span>Source <b>{safe(model)}</b></span>')

    meta_html = ''.join(meta_items[:5])
    _html(
        f'<article class="hh-ticket"><div class="hh-ticket-top"><div><div class="hh-card-kicker">{safe(game)}</div>'
        f'<h3>{safe(draw)} pick</h3></div><div class="hh-rank">#{rank}</div></div>{number_balls(row)}'
        f'<div class="hh-ticket-meta">{meta_html}</div><div class="hh-muted-line">Updated {safe(date_label(generated), "recently")}</div></article>'
    )


def result_row(row):
    game = row.get("GameName", row.get("GameFamily", "Lottery"))
    date = row.get("DrawDate", row.get("Date", ""))
    draw = row.get("DrawType", "")
    draw_html = f' • {safe(draw)}' if safe(draw, "") else ""
    _html(
        f'<div class="hh-result-row"><div><b>{safe(game)}</b><span>{safe(date_label(date))}{draw_html}</span></div>{number_balls(row)}</div>'
    )


def lottery_result_group_card(group: pd.DataFrame):
    if group is None or group.empty:
        return

    group = group.copy()
    if "DrawDate" in group.columns:
        group["_card_draw_date"] = pd.to_datetime(group["DrawDate"], errors="coerce")
        group["_card_draw_day"] = group["_card_draw_date"].dt.date
        latest_date = group["_card_draw_date"].max()
    else:
        latest_date = None

    dedupe_subset = [
        col
        for col in [
            "_card_draw_day",
            "GameGroup",
            "SubGameDisplay",
            "GameName",
            "DrawType",
            "N1",
            "N2",
            "N3",
            "N4",
            "N5",
            "N6",
            "Bonus",
        ]
        if col in group.columns
    ]
    if dedupe_subset:
        group = group.drop_duplicates(subset=dedupe_subset, keep="first")

    first = group.iloc[0]
    game_group = first.get("GameGroup", first.get("GameName", first.get("GameFamily", "Lottery")))
    count_label = f"{len(group)} draw" if len(group) == 1 else f"{len(group)} draws"

    row_html = []
    for _, row in group.iterrows():
        subgame = row.get("SubGameDisplay", row.get("GameName", row.get("GameFamily", "Lottery")))
        draw_type = row.get("DrawType", "")
        draw_type_html = f'<small>{safe(draw_type)}</small>' if _valid_meta(draw_type) else ""
        row_html.append(
            f'<div class="hh-result-group-row"><div><b>{safe(subgame)}</b>{draw_type_html}</div>{number_balls(row)}</div>'
        )

    _html(
        f'<article class="hh-result-group"><div class="hh-result-group-head"><div>'
        f'<div class="hh-card-kicker">Lottery result</div><h3>{safe(game_group)}</h3>'
        f'<span>{safe(date_label(latest_date))}</span></div><div class="hh-result-count">{safe(count_label)}</div></div>'
        f'<div class="hh-result-group-stack">{"".join(row_html)}</div></article>'
    )


def football_pick(row, rank: int = 1):
    home = row.get("HomeTeam", row.get("Home", "Home"))
    away = row.get("AwayTeam", row.get("Away", "Away"))
    league = row.get("League", row.get("Competition", "Football"))
    pick = row.get("PrimaryMarketSignal", row.get("BestResultPick", row.get("PredictedResult", row.get("ModelPick", row.get("Pick", "Pick")))))
    strength = row.get("ConfidenceScore", row.get("EnsembleConfidenceScore", row.get("Confidence", row.get("Strength", ""))))
    date = row.get("MatchDate", row.get("FixtureDate", row.get("Date", "")))

    try:
        strength_float = float(str(strength).replace("%", ""))
        if strength_float <= 1:
            strength_display = f"{strength_float * 100:.0f}%"
            width = max(0, min(100, strength_float * 100))
        else:
            strength_display = f"{strength_float:.0f}%"
            width = max(0, min(100, strength_float))
    except Exception:
        strength_display = safe(strength, "-")
        width = 65

    _html(
        f'<article class="hh-football-card"><div class="hh-ticket-top"><div><div class="hh-card-kicker">{safe(league)}</div>'
        f'<div class="hh-muted-line">{safe(date_label(date), "Latest")}</div></div><div class="hh-rank">#{rank}</div></div>'
        f'<div class="hh-match"><b>{safe(home)}</b><span>vs</span><b>{safe(away)}</b></div>'
        f'<div class="hh-pick-strip"><span>Pick</span><b>{safe(pick)}</b></div>'
        f'<div class="hh-strength"><div><span>Strength</span><b>{strength_display}</b></div><div class="hh-strength-track"><i style="width:{width}%"></i></div></div></article>'
    )


def empty_message(title: str, detail: str):
    _html(f'<div class="hh-empty"><b>{safe(title)}</b><p>{safe(detail)}</p></div>')


def friendly_table(df: pd.DataFrame, columns: list[str], height: int = 300, limit: int = 80):
    if df is None or df.empty:
        empty_message("Nothing to show yet", "This section will populate once data is available.")
        return
    cols = [c for c in columns if c in df.columns]
    if not cols:
        cols = list(df.columns[:6])
    display = df[cols].head(limit).copy()
    for col in display.columns:
        if "Date" in col or col.endswith("At"):
            try:
                display[col] = pd.to_datetime(display[col], errors="coerce").dt.strftime("%d %b %Y")
            except Exception:
                pass
    st.dataframe(display, use_container_width=True, height=height, hide_index=True)


def page_footer():
    _html('<div class="hh-footer"><b>HexagrandHouse</b><span>For entertainment and review only. No outcome is guaranteed.</span></div>')
