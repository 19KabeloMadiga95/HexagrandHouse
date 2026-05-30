from pathlib import Path
from datetime import datetime
import time

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[3]

RAW_DIR = BASE_DIR / "data" / "football" / "raw" / "fixtures"
MASTER_DIR = BASE_DIR / "data" / "football" / "master"

OUTPUT_FILE = MASTER_DIR / "football_fixtures.xlsx"
OUTPUT_CSV = MASTER_DIR / "football_fixtures.csv"
RAW_CACHE_FILE = RAW_DIR / "football_fixtures_raw.csv"

MANUAL_CSV_FILE = RAW_DIR / "new_league_fixtures.csv"
MANUAL_XLSX_FILE = RAW_DIR / "new_league_fixtures.xlsx"

FIXTURES_URL = "https://www.football-data.co.uk/fixtures.csv"

MAX_RETRIES = 3
RETRY_SLEEP_SECONDS = 3


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
    "Country": "Country",
    "League": "League",
    "Date": "FixtureDate",
    "Time": "KickoffTime",
    "HomeTeam": "HomeTeam",
    "AwayTeam": "AwayTeam",
    "Home": "HomeTeam",
    "Away": "AwayTeam",
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
}

OUTPUT_COLUMNS = [
    "FixtureKey", "LeagueCode", "League", "Country", "Tier",
    "FixtureDate", "KickoffTime", "FixtureDateTime", "IsUpcoming",
    "HomeTeam", "AwayTeam",
    "Bet365HomeOdds", "Bet365DrawOdds", "Bet365AwayOdds",
    "AverageHomeOdds", "AverageDrawOdds", "AverageAwayOdds",
    "MaxHomeOdds", "MaxDrawOdds", "MaxAwayOdds",
    "Bet365Over25Odds", "Bet365Under25Odds",
    "AverageOver25Odds", "AverageUnder25Odds",
    "MaxOver25Odds", "MaxUnder25Odds",
    "SourceName", "SourceUrl", "IngestedAt",
]

NUMERIC_COLUMNS = [
    "Bet365HomeOdds", "Bet365DrawOdds", "Bet365AwayOdds",
    "AverageHomeOdds", "AverageDrawOdds", "AverageAwayOdds",
    "MaxHomeOdds", "MaxDrawOdds", "MaxAwayOdds",
    "Bet365Over25Odds", "Bet365Under25Odds",
    "AverageOver25Odds", "AverageUnder25Odds",
    "MaxOver25Odds", "MaxUnder25Odds",
]


def ensure_directories():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    MASTER_DIR.mkdir(parents=True, exist_ok=True)


def read_fixtures_url():
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Download attempt {attempt}/{MAX_RETRIES}")
            df = pd.read_csv(FIXTURES_URL)
            df["SourceName"] = "football-data.co.uk fixtures.csv"
            df["SourceUrl"] = FIXTURES_URL
            return df
        except Exception as e:
            last_error = e
            print(f"Attempt failed: {e}")

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_SLEEP_SECONDS)

    print(f"Download failed: {last_error}")
    return pd.DataFrame()


def read_manual_fixtures():
    frames = []

    if MANUAL_CSV_FILE.exists():
        try:
            df = pd.read_csv(MANUAL_CSV_FILE)
            df["SourceName"] = "manual CSV fixture file"
            df["SourceUrl"] = str(MANUAL_CSV_FILE)
            frames.append(df)
            print(f"Loaded manual CSV fixtures: {MANUAL_CSV_FILE}")
        except Exception as e:
            print(f"Could not read manual CSV fixtures: {e}")

    if MANUAL_XLSX_FILE.exists():
        try:
            df = pd.read_excel(MANUAL_XLSX_FILE, engine="openpyxl")
            df["SourceName"] = "manual Excel fixture file"
            df["SourceUrl"] = str(MANUAL_XLSX_FILE)
            frames.append(df)
            print(f"Loaded manual Excel fixtures: {MANUAL_XLSX_FILE}")
        except Exception as e:
            print(f"Could not read manual Excel fixtures: {e}")

    if frames:
        return pd.concat(frames, ignore_index=True)

    return pd.DataFrame()


def read_cached_or_download():
    online_df = read_fixtures_url()

    if not online_df.empty:
        RAW_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        online_df.to_csv(RAW_CACHE_FILE, index=False)
        print("Fresh online fixtures downloaded and cached")
    elif RAW_CACHE_FILE.exists():
        print("Using cached online fixtures file")
        online_df = pd.read_csv(RAW_CACHE_FILE, low_memory=False)
        online_df["SourceName"] = "cached football-data.co.uk fixtures"
        online_df["SourceUrl"] = str(RAW_CACHE_FILE)

    manual_df = read_manual_fixtures()

    frames = []

    if not online_df.empty:
        frames.append(online_df)

    if not manual_df.empty:
        frames.append(manual_df)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)


def add_missing_columns(df, columns):
    for col in columns:
        if col not in df.columns:
            df[col] = None

    return df


def clean_team_name(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    if value == "" or value.lower() in ["nan", "none"]:
        return None

    return value


def safe_numeric(df, col):
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def parse_fixture_date(series):
    return pd.to_datetime(series, dayfirst=True, errors="coerce")


def create_league_code_from_name(row):
    league = row.get("League")
    country = row.get("Country")

    if pd.isna(league) or str(league).strip() == "":
        league = "Unknown League"

    if pd.isna(country) or str(country).strip() == "":
        country = "Unknown"

    league_code = (
        str(country).strip().upper().replace(" ", "_")
        + "_"
        + str(league).strip().upper().replace(" ", "_")
    )

    return league_code


def enrich_league_fields(df):
    df = df.copy()

    if "LeagueCode" not in df.columns:
        df["LeagueCode"] = None

    if "League" not in df.columns:
        df["League"] = None

    if "Country" not in df.columns:
        df["Country"] = None

    if "Tier" not in df.columns:
        df["Tier"] = None

    mapped_league = df["LeagueCode"].map(
        lambda x: LEAGUE_MAP.get(str(x), (None, None, None))[0]
    )

    mapped_country = df["LeagueCode"].map(
        lambda x: LEAGUE_MAP.get(str(x), (None, None, None))[1]
    )

    mapped_tier = df["LeagueCode"].map(
        lambda x: LEAGUE_MAP.get(str(x), (None, None, None))[2]
    )

    df["League"] = df["League"].fillna(mapped_league)
    df["Country"] = df["Country"].fillna(mapped_country)
    df["Tier"] = df["Tier"].fillna(mapped_tier)

    df["League"] = df["League"].fillna("Unknown League")
    df["Country"] = df["Country"].fillna("Unknown")
    df["Tier"] = df["Tier"].fillna("External / Manual Source")

    missing_code_mask = (
        df["LeagueCode"].isna()
        | (df["LeagueCode"].astype(str).str.strip() == "")
        | (df["LeagueCode"].astype(str).str.lower() == "nan")
    )

    df.loc[missing_code_mask, "LeagueCode"] = df[missing_code_mask].apply(
        create_league_code_from_name,
        axis=1
    )

    return df


def build_fixture_datetime(df):
    def combine_datetime(row):
        fixture_date = row["FixtureDate"]
        kickoff_time = row["KickoffTime"]

        if pd.isna(fixture_date):
            return pd.NaT

        if pd.isna(kickoff_time) or str(kickoff_time).strip() == "":
            kickoff_time = "12:00"

        try:
            return pd.to_datetime(
                f"{fixture_date.date()} {kickoff_time}",
                errors="coerce"
            )
        except Exception:
            return pd.NaT

    df["FixtureDateTime"] = df.apply(combine_datetime, axis=1)

    return df


def remove_completed_fixtures(df):
    today = pd.Timestamp.today().normalize()

    df["IsUpcoming"] = df["FixtureDate"] >= today

    before_count = len(df)
    df = df[df["IsUpcoming"]].copy()
    after_count = len(df)

    removed = before_count - after_count
    print(f"Removed completed fixtures: {removed}")

    return df


def build_fixture_key(df):
    df["FixtureDateKey"] = df["FixtureDate"].dt.strftime("%Y-%m-%d")

    df["FixtureKey"] = (
        df["LeagueCode"].astype(str)
        + "_"
        + df["FixtureDateKey"].astype(str)
        + "_"
        + df["HomeTeam"].astype(str)
        + "_"
        + df["AwayTeam"].astype(str)
    )

    df = df.drop(columns=["FixtureDateKey"], errors="ignore")

    return df


def transform_fixtures(raw_df):
    if raw_df.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    df = raw_df.copy()

    available_cols = [
        col for col in COLUMN_MAP
        if col in df.columns
    ]

    extra_source_cols = [
        col for col in ["SourceName", "SourceUrl"]
        if col in df.columns
    ]

    df = df[available_cols + extra_source_cols].rename(columns=COLUMN_MAP)

    # Coalesce duplicate columns caused by Home/HomeTeam and Away/AwayTeam formats
    if df.columns.duplicated().any():
        new_df = pd.DataFrame()

        for col in df.columns.unique():
            matching_cols = df.loc[:, df.columns == col]

            if matching_cols.shape[1] == 1:
                new_df[col] = matching_cols.iloc[:, 0]
            else:
                new_df[col] = matching_cols.bfill(axis=1).iloc[:, 0]

        df = new_df.copy()

    df = add_missing_columns(df, list(COLUMN_MAP.values()))
    df = add_missing_columns(df, ["SourceName", "SourceUrl"])

    df["FixtureDate"] = parse_fixture_date(df["FixtureDate"])
    df["HomeTeam"] = df["HomeTeam"].apply(clean_team_name)
    df["AwayTeam"] = df["AwayTeam"].apply(clean_team_name)

    for col in NUMERIC_COLUMNS:
        df = safe_numeric(df, col)

    df = df[
        df["FixtureDate"].notna()
        & df["HomeTeam"].notna()
        & df["AwayTeam"].notna()
    ].copy()

    df = enrich_league_fields(df)
    df = build_fixture_datetime(df)
    df = remove_completed_fixtures(df)

    df["SourceName"] = df["SourceName"].fillna("football fixture source")
    df["SourceUrl"] = df["SourceUrl"].fillna("")
    df["IngestedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df = build_fixture_key(df)
    df = add_missing_columns(df, OUTPUT_COLUMNS)
    df = df[OUTPUT_COLUMNS].copy()

    df = df.drop_duplicates(subset=["FixtureKey"], keep="first")

    df = df.sort_values(
        by=["FixtureDateTime", "League", "HomeTeam", "AwayTeam"],
        ascending=True
    ).reset_index(drop=True)

    return df


def export_fixtures():
    ensure_directories()

    raw_df = read_cached_or_download()
    fixtures_df = transform_fixtures(raw_df)

    fixtures_df.to_csv(OUTPUT_CSV, index=False)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl", mode="w") as writer:
        fixtures_df.to_excel(
            writer,
            sheet_name="Football_Fixtures",
            index=False
        )

    print("\n======================================")
    print("FOOTBALL FIXTURES EXPORTED")
    print("======================================")
    print(f"Rows: {len(fixtures_df)}")
    print(f"Excel: {OUTPUT_FILE}")
    print(f"CSV: {OUTPUT_CSV}")
    print("======================================\n")

    return fixtures_df


def main():
    export_fixtures()


if __name__ == "__main__":
    main()