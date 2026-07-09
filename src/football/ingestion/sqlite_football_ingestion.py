from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.core.paths import FOOTBALL_RAW_FIXTURES_DIR
from src.data.sqlite_store import create_indexes, replace_sqlite_table


# =========================================================
# FOOTBALL FIXTURE INGESTION - SQLITE RUNTIME
# =========================================================

FIXTURES_URL = "https://www.football-data.co.uk/fixtures.csv"
FIXTURES_TABLE = "football_fixtures"
STATUS_TABLE = "football_fixture_ingestion_status"

LOOKAHEAD_DAYS = 60

RAW_FIXTURES_DIR = FOOTBALL_RAW_FIXTURES_DIR
RAW_CACHE_FILE = RAW_FIXTURES_DIR / "football_fixtures_raw.csv"
MANUAL_CSV_FILE = RAW_FIXTURES_DIR / "new_league_fixtures.csv"
MANUAL_XLSX_FILE = RAW_FIXTURES_DIR / "new_league_fixtures.xlsx"

LEAGUE_MAP = {
    "E0": ("Premier League", "England", "Tier 1 - Elite Europe"),
    "SP1": ("La Liga", "Spain", "Tier 1 - Elite Europe"),
    "D1": ("Bundesliga", "Germany", "Tier 1 - Elite Europe"),
    "I1": ("Serie A", "Italy", "Tier 1 - Elite Europe"),
    "F1": ("Ligue 1", "France", "Tier 1 - Elite Europe"),
    "P1": ("Primeira Liga", "Portugal", "Tier 1 - Elite Europe"),
    "N1": ("Eredivisie", "Netherlands", "Tier 1 - Elite Europe"),
    "B1": ("Belgian Pro League", "Belgium", "Tier 1 - Elite Europe"),
    "E1": ("Championship", "England", "Tier 2 - Europe Depth"),
    "E2": ("League One", "England", "Tier 2 - Europe Depth"),
    "E3": ("League Two", "England", "Tier 2 - Europe Depth"),
    "EC": ("National League", "England", "Tier 2 - Europe Depth"),
    "SC0": ("Scottish Premiership", "Scotland", "Tier 2 - Europe Depth"),
    "SC1": ("Scottish Championship", "Scotland", "Tier 2 - Europe Depth"),
    "D2": ("2. Bundesliga", "Germany", "Tier 2 - Europe Depth"),
    "I2": ("Serie B", "Italy", "Tier 2 - Europe Depth"),
    "SP2": ("La Liga 2", "Spain", "Tier 2 - Europe Depth"),
    "F2": ("Ligue 2", "France", "Tier 2 - Europe Depth"),
    "T1": ("Turkish Super Lig", "Turkey", "Tier 2 - Europe Depth"),
    "G1": ("Greek Super League", "Greece", "Tier 2 - Europe Depth"),
}

COLUMN_MAP = {
    "Div": "LeagueCode",
    "LeagueCode": "LeagueCode",
    "Date": "FixtureDate",
    "FixtureDate": "FixtureDate",
    "Time": "KickoffTime",
    "KickoffTime": "KickoffTime",
    "HomeTeam": "HomeTeam",
    "AwayTeam": "AwayTeam",
    "Home": "HomeTeam",
    "Away": "AwayTeam",
    "Home_Team": "HomeTeam",
    "Away_Team": "AwayTeam",
    "League": "League",
    "Country": "Country",
    "Tier": "Tier",
    "B365H": "Bet365HomeOdds",
    "B365D": "Bet365DrawOdds",
    "B365A": "Bet365AwayOdds",
    "AvgH": "AverageHomeOdds",
    "AvgD": "AverageDrawOdds",
    "AvgA": "AverageAwayOdds",
    "MaxH": "MaxHomeOdds",
    "MaxD": "MaxDrawOdds",
    "MaxA": "MaxAwayOdds",
    "B365>2.5": "Bet365Over25Odds",
    "B365<2.5": "Bet365Under25Odds",
    "Avg>2.5": "AverageOver25Odds",
    "Avg<2.5": "AverageUnder25Odds",
    "Max>2.5": "MaxOver25Odds",
    "Max<2.5": "MaxUnder25Odds",
    "SourceName": "SourceName",
    "SourceUrl": "SourceUrl",
}

OUTPUT_COLUMNS = [
    "FixtureKey",
    "LeagueCode",
    "League",
    "Country",
    "Tier",
    "FixtureDate",
    "KickoffTime",
    "HomeTeam",
    "AwayTeam",
    "Bet365HomeOdds",
    "Bet365DrawOdds",
    "Bet365AwayOdds",
    "AverageHomeOdds",
    "AverageDrawOdds",
    "AverageAwayOdds",
    "MaxHomeOdds",
    "MaxDrawOdds",
    "MaxAwayOdds",
    "Bet365Over25Odds",
    "Bet365Under25Odds",
    "AverageOver25Odds",
    "AverageUnder25Odds",
    "MaxOver25Odds",
    "MaxUnder25Odds",
    "SourceName",
    "SourceUrl",
    "IngestedAt",
]

NUMERIC_COLUMNS = [
    "Bet365HomeOdds",
    "Bet365DrawOdds",
    "Bet365AwayOdds",
    "AverageHomeOdds",
    "AverageDrawOdds",
    "AverageAwayOdds",
    "MaxHomeOdds",
    "MaxDrawOdds",
    "MaxAwayOdds",
    "Bet365Over25Odds",
    "Bet365Under25Odds",
    "AverageOver25Odds",
    "AverageUnder25Odds",
    "MaxOver25Odds",
    "MaxUnder25Odds",
]


def now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _empty_fixtures() -> pd.DataFrame:
    return pd.DataFrame(columns=OUTPUT_COLUMNS)


def _add_missing_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            out[col] = None
    return out


def _clean_team(value: Any) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _parse_fixture_date(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, dayfirst=True, errors="coerce")
    if parsed.notna().sum() == 0:
        parsed = pd.to_datetime(series, errors="coerce")
    return parsed


def _create_league_code_from_name(row: pd.Series) -> str:
    country = str(row.get("Country") or "Unknown").strip()
    league = str(row.get("League") or "Unknown League").strip()
    return f"{country.upper().replace(' ', '_')}_{league.upper().replace(' ', '_')}"


def _enrich_leagues(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if "LeagueCode" not in out.columns:
        out["LeagueCode"] = None

    if "League" not in out.columns:
        out["League"] = None

    if "Country" not in out.columns:
        out["Country"] = None

    if "Tier" not in out.columns:
        out["Tier"] = None

    mapped_league = out["LeagueCode"].map(
        lambda x: LEAGUE_MAP.get(str(x), (None, None, None))[0]
    )
    mapped_country = out["LeagueCode"].map(
        lambda x: LEAGUE_MAP.get(str(x), (None, None, None))[1]
    )
    mapped_tier = out["LeagueCode"].map(
        lambda x: LEAGUE_MAP.get(str(x), (None, None, None))[2]
    )

    out["League"] = out["League"].where(out["League"].notna(), mapped_league)
    out["Country"] = out["Country"].where(out["Country"].notna(), mapped_country)
    out["Tier"] = out["Tier"].where(out["Tier"].notna(), mapped_tier)

    missing_code = out["LeagueCode"].isna() | out["LeagueCode"].astype(str).str.strip().isin(["", "nan", "None"])
    if missing_code.any():
        out.loc[missing_code, "LeagueCode"] = out.loc[missing_code].apply(_create_league_code_from_name, axis=1)

    out["League"] = out["League"].fillna("Unknown League")
    out["Country"] = out["Country"].fillna("Unknown")
    out["Tier"] = out["Tier"].fillna("Unknown")

    return out


def _build_fixture_key(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    date_key = pd.to_datetime(out["FixtureDate"], errors="coerce").dt.strftime("%Y-%m-%d")
    out["FixtureKey"] = (
        out["LeagueCode"].astype(str).str.strip()
        + "_"
        + date_key.astype(str)
        + "_"
        + out["HomeTeam"].astype(str).str.strip()
        + "_"
        + out["AwayTeam"].astype(str).str.strip()
    )
    return out


def _read_csv_file(path: Path, source_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, low_memory=False)
        df["SourceName"] = source_name
        df["SourceUrl"] = str(path)
        print(f"Loaded fixture file: {path}")
        return df
    except Exception as exc:
        print(f"Could not read fixture file {path}: {exc}")
        return pd.DataFrame()


def _read_excel_file(path: Path, source_name: str) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_excel(path, engine="openpyxl")
        df["SourceName"] = source_name
        df["SourceUrl"] = str(path)
        print(f"Loaded fixture file: {path}")
        return df
    except Exception as exc:
        print(f"Could not read fixture file {path}: {exc}")
        return pd.DataFrame()


def _download_fixture_feed() -> pd.DataFrame:
    print(f"Downloading football fixtures: {FIXTURES_URL}")
    df = pd.read_csv(FIXTURES_URL, low_memory=False)
    df["SourceName"] = "football-data.co.uk fixtures"
    df["SourceUrl"] = FIXTURES_URL

    RAW_FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_CACHE_FILE, index=False)
    print(f"Cached raw fixture feed: {RAW_CACHE_FILE}")

    return df


def _load_raw_fixture_frames() -> tuple[list[pd.DataFrame], list[str]]:
    frames: list[pd.DataFrame] = []
    messages: list[str] = []

    try:
        online_df = _download_fixture_feed()
        if not online_df.empty:
            frames.append(online_df)
            messages.append(f"online={len(online_df)}")
    except Exception as exc:
        messages.append(f"online_failed={exc}")
        cached_df = _read_csv_file(RAW_CACHE_FILE, "cached football-data.co.uk fixtures")
        if not cached_df.empty:
            frames.append(cached_df)
            messages.append(f"cache={len(cached_df)}")

    manual_csv = _read_csv_file(MANUAL_CSV_FILE, "manual CSV fixture file")
    if not manual_csv.empty:
        frames.append(manual_csv)
        messages.append(f"manual_csv={len(manual_csv)}")

    manual_xlsx = _read_excel_file(MANUAL_XLSX_FILE, "manual Excel fixture file")
    if not manual_xlsx.empty:
        frames.append(manual_xlsx)
        messages.append(f"manual_xlsx={len(manual_xlsx)}")

    return frames, messages


def transform_fixture_feed(raw_df: pd.DataFrame, lookahead_days: int = LOOKAHEAD_DAYS) -> pd.DataFrame:
    if raw_df is None or raw_df.empty:
        return _empty_fixtures()

    available_cols = [col for col in COLUMN_MAP if col in raw_df.columns]
    if not available_cols:
        return _empty_fixtures()

    df = raw_df[available_cols].rename(columns=COLUMN_MAP).copy()
    df = _add_missing_columns(df, list(set(COLUMN_MAP.values())))

    df["FixtureDate"] = _parse_fixture_date(df["FixtureDate"])
    df["HomeTeam"] = df["HomeTeam"].apply(_clean_team)
    df["AwayTeam"] = df["AwayTeam"].apply(_clean_team)

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    today = pd.Timestamp(datetime.now().date())
    max_day = today + pd.Timedelta(days=int(lookahead_days))

    df = df[
        df["FixtureDate"].notna()
        & (df["FixtureDate"] >= today)
        & (df["FixtureDate"] <= max_day)
        & df["HomeTeam"].notna()
        & df["AwayTeam"].notna()
    ].copy()

    if df.empty:
        return _empty_fixtures()

    df = _enrich_leagues(df)
    df["SourceName"] = df["SourceName"].fillna("football fixtures")
    df["SourceUrl"] = df["SourceUrl"].fillna(FIXTURES_URL)
    df["IngestedAt"] = now_string()
    df = _build_fixture_key(df)
    df = _add_missing_columns(df, OUTPUT_COLUMNS)

    df = df[OUTPUT_COLUMNS].drop_duplicates(subset=["FixtureKey"]).sort_values(
        ["FixtureDate", "League", "HomeTeam", "AwayTeam"]
    )

    return df.reset_index(drop=True)


def _status_df(fixtures_df: pd.DataFrame, status: str, message: str) -> pd.DataFrame:
    if fixtures_df.empty:
        earliest = None
        latest = None
        leagues = 0
    else:
        earliest = pd.to_datetime(fixtures_df["FixtureDate"], errors="coerce").min()
        latest = pd.to_datetime(fixtures_df["FixtureDate"], errors="coerce").max()
        leagues = int(fixtures_df["League"].nunique()) if "League" in fixtures_df.columns else 0

    return pd.DataFrame(
        [
            {
                "Status": status,
                "Message": message,
                "Rows": int(len(fixtures_df)),
                "Leagues": leagues,
                "EarliestFixture": None if pd.isna(earliest) else earliest.strftime("%Y-%m-%d"),
                "LatestFixture": None if pd.isna(latest) else latest.strftime("%Y-%m-%d"),
                "SourceUrl": FIXTURES_URL,
                "UpdatedAt": now_string(),
            }
        ]
    )


def update_football_fixtures_sqlite(lookahead_days: int = LOOKAHEAD_DAYS) -> pd.DataFrame:
    """
    Refresh current/future football fixtures in SQLite.

    The public website must not show old football cards. This loader therefore
    keeps only today/future fixtures. It can combine the online feed, a cached
    copy, and optional manual CSV/XLSX files under data/football/raw/fixtures.
    """

    frames, messages = _load_raw_fixture_frames()

    if frames:
        raw_df = pd.concat(frames, ignore_index=True, sort=False)
        fixtures_df = transform_fixture_feed(raw_df, lookahead_days=lookahead_days)
        status = "Success" if not fixtures_df.empty else "No Upcoming Fixtures"
        message = "; ".join(messages) or "Raw fixtures loaded."
        if fixtures_df.empty:
            message += "; no fixtures survived the upcoming-date filter."
    else:
        fixtures_df = _empty_fixtures()
        status = "Failed"
        message = "; ".join(messages) if messages else "No online, cached, or manual fixture source available."

    rows = replace_sqlite_table(FIXTURES_TABLE, fixtures_df)
    replace_sqlite_table(STATUS_TABLE, _status_df(fixtures_df, status, message))

    create_indexes(
        FIXTURES_TABLE,
        ["FixtureKey", "FixtureDate", "LeagueCode", "League", "HomeTeam", "AwayTeam"],
    )
    create_indexes(STATUS_TABLE, ["Status", "UpdatedAt"])

    print("\nSQLite football fixtures refreshed.")
    print(f"Table : {FIXTURES_TABLE}")
    print(f"Status: {status}")
    print(f"Rows  : {rows}")
    print(f"Note  : {message}")
    if not fixtures_df.empty:
        print(f"Next  : {fixtures_df['FixtureDate'].min()}")
        print(f"Last  : {fixtures_df['FixtureDate'].max()}")
    print("=" * 38)

    return fixtures_df


def main() -> pd.DataFrame:
    return update_football_fixtures_sqlite()


if __name__ == "__main__":
    main()
