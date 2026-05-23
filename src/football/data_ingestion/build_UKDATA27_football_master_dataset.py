from pathlib import Path
from datetime import datetime
import time

import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

RAW_DIR = BASE_DIR / "data" / "football" / "raw"
MASTER_DIR = BASE_DIR / "data" / "football" / "master"

OUTPUT_ALL_FILE = MASTER_DIR / "football_master_all_leagues.xlsx"
OUTPUT_TIER1_FILE = MASTER_DIR / "football_master_tier1_elite.xlsx"
OUTPUT_TIER2_FILE = MASTER_DIR / "football_master_tier2_europe.xlsx"
OUTPUT_TIER3_FILE = MASTER_DIR / "football_master_tier3_global.xlsx"


# =========================================================
# CONFIG
# =========================================================

MAX_RETRIES = 3
RETRY_SLEEP_SECONDS = 3

SEASONS = [
    {"Season": "2022-23", "SeasonCode": "2223"},
    {"Season": "2023-24", "SeasonCode": "2324"},
    {"Season": "2024-25", "SeasonCode": "2425"},
    {"Season": "2025-26", "SeasonCode": "2526"},
]


LEAGUES = [
    {"LeagueCode": "E0", "LeagueName": "Premier League", "Country": "England", "Tier": "Tier 1 - Elite Europe", "SourceMode": "standard"},
    {"LeagueCode": "SP1", "LeagueName": "La Liga", "Country": "Spain", "Tier": "Tier 1 - Elite Europe", "SourceMode": "standard"},
    {"LeagueCode": "D1", "LeagueName": "Bundesliga", "Country": "Germany", "Tier": "Tier 1 - Elite Europe", "SourceMode": "standard"},
    {"LeagueCode": "I1", "LeagueName": "Serie A", "Country": "Italy", "Tier": "Tier 1 - Elite Europe", "SourceMode": "standard"},
    {"LeagueCode": "F1", "LeagueName": "Ligue 1", "Country": "France", "Tier": "Tier 1 - Elite Europe", "SourceMode": "standard"},
    {"LeagueCode": "P1", "LeagueName": "Primeira Liga", "Country": "Portugal", "Tier": "Tier 1 - Elite Europe", "SourceMode": "standard"},
    {"LeagueCode": "N1", "LeagueName": "Eredivisie", "Country": "Netherlands", "Tier": "Tier 1 - Elite Europe", "SourceMode": "standard"},
    {"LeagueCode": "B1", "LeagueName": "Belgian Pro League", "Country": "Belgium", "Tier": "Tier 1 - Elite Europe", "SourceMode": "standard"},

    {"LeagueCode": "E1", "LeagueName": "Championship", "Country": "England", "Tier": "Tier 2 - Europe Depth", "SourceMode": "standard"},
    {"LeagueCode": "E2", "LeagueName": "League One", "Country": "England", "Tier": "Tier 2 - Europe Depth", "SourceMode": "standard"},
    {"LeagueCode": "E3", "LeagueName": "League Two", "Country": "England", "Tier": "Tier 2 - Europe Depth", "SourceMode": "standard"},
    {"LeagueCode": "EC", "LeagueName": "National League", "Country": "England", "Tier": "Tier 2 - Europe Depth", "SourceMode": "standard"},
    {"LeagueCode": "SC0", "LeagueName": "Scottish Premiership", "Country": "Scotland", "Tier": "Tier 2 - Europe Depth", "SourceMode": "standard"},
    {"LeagueCode": "SC1", "LeagueName": "Scottish Championship", "Country": "Scotland", "Tier": "Tier 2 - Europe Depth", "SourceMode": "standard"},
    {"LeagueCode": "D2", "LeagueName": "2. Bundesliga", "Country": "Germany", "Tier": "Tier 2 - Europe Depth", "SourceMode": "standard"},
    {"LeagueCode": "I2", "LeagueName": "Serie B", "Country": "Italy", "Tier": "Tier 2 - Europe Depth", "SourceMode": "standard"},
    {"LeagueCode": "SP2", "LeagueName": "La Liga 2", "Country": "Spain", "Tier": "Tier 2 - Europe Depth", "SourceMode": "standard"},
    {"LeagueCode": "F2", "LeagueName": "Ligue 2", "Country": "France", "Tier": "Tier 2 - Europe Depth", "SourceMode": "standard"},
    {"LeagueCode": "T1", "LeagueName": "Turkish Super Lig", "Country": "Turkey", "Tier": "Tier 2 - Europe Depth", "SourceMode": "standard"},
    {"LeagueCode": "G1", "LeagueName": "Greek Super League", "Country": "Greece", "Tier": "Tier 2 - Europe Depth", "SourceMode": "standard"},

    {"LeagueCode": "ARG", "LeagueName": "Argentine Primera Division", "Country": "Argentina", "Tier": "Tier 3 - Global", "SourceMode": "extra"},
    {"LeagueCode": "AUT", "LeagueName": "Austrian Bundesliga", "Country": "Austria", "Tier": "Tier 3 - Global", "SourceMode": "extra"},
    {"LeagueCode": "BRA", "LeagueName": "Brazil Serie A", "Country": "Brazil", "Tier": "Tier 3 - Global", "SourceMode": "extra"},
    {"LeagueCode": "CHN", "LeagueName": "Chinese Super League", "Country": "China", "Tier": "Tier 3 - Global", "SourceMode": "extra"},
    {"LeagueCode": "DNK", "LeagueName": "Danish Superliga", "Country": "Denmark", "Tier": "Tier 3 - Global", "SourceMode": "extra"},
    {"LeagueCode": "FIN", "LeagueName": "Finnish Veikkausliiga", "Country": "Finland", "Tier": "Tier 3 - Global", "SourceMode": "extra"},
    {"LeagueCode": "IRL", "LeagueName": "League of Ireland Premier Division", "Country": "Ireland", "Tier": "Tier 3 - Global", "SourceMode": "extra"},
    {"LeagueCode": "JPN", "LeagueName": "J1 League", "Country": "Japan", "Tier": "Tier 3 - Global", "SourceMode": "extra"},
    {"LeagueCode": "MEX", "LeagueName": "Liga MX", "Country": "Mexico", "Tier": "Tier 3 - Global", "SourceMode": "extra"},
    {"LeagueCode": "NOR", "LeagueName": "Norwegian Eliteserien", "Country": "Norway", "Tier": "Tier 3 - Global", "SourceMode": "extra"},
    {"LeagueCode": "POL", "LeagueName": "Polish Ekstraklasa", "Country": "Poland", "Tier": "Tier 3 - Global", "SourceMode": "extra"},
    {"LeagueCode": "ROU", "LeagueName": "Romanian Liga 1", "Country": "Romania", "Tier": "Tier 3 - Global", "SourceMode": "extra"},
    {"LeagueCode": "RUS", "LeagueName": "Russian Premier League", "Country": "Russia", "Tier": "Tier 3 - Global", "SourceMode": "extra"},
    {"LeagueCode": "SWE", "LeagueName": "Swedish Allsvenskan", "Country": "Sweden", "Tier": "Tier 3 - Global", "SourceMode": "extra"},
    {"LeagueCode": "SWZ", "LeagueName": "Swiss Super League", "Country": "Switzerland", "Tier": "Tier 3 - Global", "SourceMode": "extra"},
    {"LeagueCode": "USA", "LeagueName": "Major League Soccer", "Country": "USA", "Tier": "Tier 3 - Global", "SourceMode": "extra"},
]


STANDARD_URL_TEMPLATE = "https://www.football-data.co.uk/mmz4281/{season_code}/{league_code}.csv"
EXTRA_URL_TEMPLATE = "https://www.football-data.co.uk/new/{league_code}.csv"


COLUMN_MAP = {
    "Div": "Division",
    "Country": "SourceCountry",
    "League": "SourceLeague",
    "Season": "SourceSeason",
    "Date": "MatchDate",
    "Time": "KickoffTime",
    "Home": "HomeTeam",
    "Away": "AwayTeam",
    "HomeTeam": "HomeTeam",
    "AwayTeam": "AwayTeam",
    "HG": "HomeGoals",
    "AG": "AwayGoals",
    "Res": "Result",
    "FTHG": "HomeGoals",
    "FTAG": "AwayGoals",
    "FTR": "Result",
    "HTHG": "HalfTimeHomeGoals",
    "HTAG": "HalfTimeAwayGoals",
    "HTR": "HalfTimeResult",
    "Referee": "Referee",
    "HS": "HomeShots",
    "AS": "AwayShots",
    "HST": "HomeShotsOnTarget",
    "AST": "AwayShotsOnTarget",
    "HF": "HomeFouls",
    "AF": "AwayFouls",
    "HC": "HomeCorners",
    "AC": "AwayCorners",
    "HY": "HomeYellowCards",
    "AY": "AwayYellowCards",
    "HR": "HomeRedCards",
    "AR": "AwayRedCards",
}


MASTER_COLUMNS = [
    "Season", "SeasonCode", "LeagueCode", "League", "Country", "Tier",
    "Division", "MatchDate", "KickoffTime", "HomeTeam", "AwayTeam",
    "HomeGoals", "AwayGoals", "TotalGoals", "Result", "ResultLabel",
    "HalfTimeHomeGoals", "HalfTimeAwayGoals", "HalfTimeResult",
    "HomeShots", "AwayShots", "TotalShots",
    "HomeShotsOnTarget", "AwayShotsOnTarget", "TotalShotsOnTarget",
    "HomeCorners", "AwayCorners", "TotalCorners",
    "HomeFouls", "AwayFouls",
    "HomeYellowCards", "AwayYellowCards", "TotalYellowCards",
    "HomeRedCards", "AwayRedCards", "TotalRedCards",
    "HomeCleanSheet", "AwayCleanSheet", "BTTS",
    "Over05Goals", "Over15Goals", "Over25Goals", "Over35Goals", "Over45Goals",
    "Over75Corners", "Over85Corners", "Over95Corners", "Over105Corners", "Over115Corners",
    "Referee", "SourceMode", "SourceName", "SourceUrl", "IngestedAt",
]


NUMERIC_COLUMNS = [
    "HomeGoals", "AwayGoals", "HalfTimeHomeGoals", "HalfTimeAwayGoals",
    "HomeShots", "AwayShots", "HomeShotsOnTarget", "AwayShotsOnTarget",
    "HomeFouls", "AwayFouls", "HomeCorners", "AwayCorners",
    "HomeYellowCards", "AwayYellowCards", "HomeRedCards", "AwayRedCards",
]


# =========================================================
# HELPERS
# =========================================================

def ensure_directories():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    MASTER_DIR.mkdir(parents=True, exist_ok=True)


def build_source_url(season_code, league_code, source_mode):
    if source_mode == "extra":
        return EXTRA_URL_TEMPLATE.format(league_code=league_code)

    return STANDARD_URL_TEMPLATE.format(
        season_code=season_code,
        league_code=league_code
    )


def get_raw_file_path(season_code, league_code, source_mode):
    league_raw_dir = RAW_DIR / league_code
    league_raw_dir.mkdir(parents=True, exist_ok=True)

    if source_mode == "extra":
        return league_raw_dir / f"{league_code}_raw.csv"

    return league_raw_dir / f"{league_code}_{season_code}_raw.csv"


def safe_read_existing_master():
    if not OUTPUT_ALL_FILE.exists():
        return pd.DataFrame(columns=MASTER_COLUMNS)

    try:
        df = pd.read_excel(
            OUTPUT_ALL_FILE,
            sheet_name="Football_Master",
            engine="openpyxl"
        )

        df = add_missing_columns(df, MASTER_COLUMNS)

        return df[MASTER_COLUMNS].copy()

    except Exception as e:
        print(f"Could not read existing master file: {OUTPUT_ALL_FILE}")
        print(f"Error: {e}")
        return pd.DataFrame(columns=MASTER_COLUMNS)


def league_season_exists(master_df, season, league_code):
    if master_df.empty:
        return False

    if "Season" not in master_df.columns or "LeagueCode" not in master_df.columns:
        return False

    existing = master_df[
        (master_df["Season"].astype(str) == str(season))
        & (master_df["LeagueCode"].astype(str) == str(league_code))
    ]

    return not existing.empty

def is_active_season(season):
    """
    Detect if season should still refresh.

    Example:
    2025-26 is active during 2025 and 2026.
    """

    current_year = datetime.now().year

    start_year = int(season.split("-")[0])
    end_year_short = int(season.split("-")[1])

    end_year = 2000 + end_year_short

    return current_year in [start_year, end_year]

def read_csv_with_retry(url):
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Download attempt {attempt}/{MAX_RETRIES}")
            return pd.read_csv(url)

        except Exception as e:
            last_error = e
            print(f"Attempt {attempt} failed: {e}")

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_SLEEP_SECONDS)

    print(f"All retries failed for URL: {url}")
    print(f"Last error: {last_error}")

    return pd.DataFrame()


def safe_read_csv_with_cache(url, raw_file, force_refresh=False):
    if raw_file.exists() and not force_refresh:
        try:
            print(f"Using cached raw file: {raw_file}")
            return pd.read_csv(raw_file)

        except Exception as e:
            print(f"Cached file failed, will try URL: {raw_file}")
            print(f"Cache error: {e}")

    df = read_csv_with_retry(url)

    if not df.empty:
        df.to_csv(raw_file, index=False)
        print(f"Saved raw cache: {raw_file}")

    return df


def clean_team_name(value):
    if pd.isna(value):
        return None

    return str(value).strip()


def parse_match_date(series):
    return pd.to_datetime(series, dayfirst=True, errors="coerce")


def safe_numeric(df, col):
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def add_missing_columns(df, required_columns):
    for col in required_columns:
        if col not in df.columns:
            df[col] = None

    return df


def standardise_result_label(result):
    if result == "H":
        return "Home Win"

    if result == "D":
        return "Draw"

    if result == "A":
        return "Away Win"

    return "Unknown"


def filter_extra_league_by_season(df, season):
    if df.empty:
        return df

    if "SourceSeason" not in df.columns:
        return df

    season_start_year = int(str(season).split("-")[0])
    season_end_year = season_start_year + 1

    source_season = df["SourceSeason"].astype(str).str.strip()

    mask_standard = source_season.eq(f"{season_start_year}/{season_end_year}")
    mask_short = source_season.eq(f"{season_start_year}/{str(season_end_year)[-2:]}")
    mask_calendar_start = source_season.eq(str(season_start_year))
    mask_calendar_end = source_season.eq(str(season_end_year))

    return df[
        mask_standard
        | mask_short
        | mask_calendar_start
        | mask_calendar_end
    ].copy()


# =========================================================
# TRANSFORM
# =========================================================

def transform_match_dataframe(
    raw_df,
    season,
    season_code,
    league_code,
    league_name,
    country,
    tier,
    source_mode,
    source_url
):
    if raw_df.empty:
        return pd.DataFrame(columns=MASTER_COLUMNS)

    df = raw_df.copy()

    available_columns = [
        col for col in COLUMN_MAP.keys()
        if col in df.columns
    ]

    df = df[available_columns].rename(columns=COLUMN_MAP)

    df = add_missing_columns(df, list(COLUMN_MAP.values()))

    if source_mode == "extra":
        df = filter_extra_league_by_season(df, season)

    df["Season"] = season
    df["SeasonCode"] = season_code
    df["LeagueCode"] = league_code
    df["League"] = league_name
    df["Country"] = country
    df["Tier"] = tier
    df["SourceMode"] = source_mode
    df["SourceName"] = "football-data.co.uk"
    df["SourceUrl"] = source_url
    df["IngestedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df["HomeTeam"] = df["HomeTeam"].apply(clean_team_name)
    df["AwayTeam"] = df["AwayTeam"].apply(clean_team_name)
    df["MatchDate"] = parse_match_date(df["MatchDate"])

    for col in NUMERIC_COLUMNS:
        df = safe_numeric(df, col)

    df = df[
        df["HomeTeam"].notna()
        & df["AwayTeam"].notna()
        & df["MatchDate"].notna()
    ].copy()

    df["TotalGoals"] = df["HomeGoals"].fillna(0) + df["AwayGoals"].fillna(0)
    df["TotalShots"] = df["HomeShots"].fillna(0) + df["AwayShots"].fillna(0)
    df["TotalShotsOnTarget"] = (
        df["HomeShotsOnTarget"].fillna(0)
        + df["AwayShotsOnTarget"].fillna(0)
    )
    df["TotalCorners"] = df["HomeCorners"].fillna(0) + df["AwayCorners"].fillna(0)
    df["TotalYellowCards"] = (
        df["HomeYellowCards"].fillna(0)
        + df["AwayYellowCards"].fillna(0)
    )
    df["TotalRedCards"] = df["HomeRedCards"].fillna(0) + df["AwayRedCards"].fillna(0)

    df["ResultLabel"] = df["Result"].apply(standardise_result_label)

    df["HomeCleanSheet"] = (df["AwayGoals"].fillna(0) == 0).astype(int)
    df["AwayCleanSheet"] = (df["HomeGoals"].fillna(0) == 0).astype(int)

    df["BTTS"] = (
        (df["HomeGoals"].fillna(0) > 0)
        & (df["AwayGoals"].fillna(0) > 0)
    ).astype(int)

    df["Over05Goals"] = (df["TotalGoals"] > 0.5).astype(int)
    df["Over15Goals"] = (df["TotalGoals"] > 1.5).astype(int)
    df["Over25Goals"] = (df["TotalGoals"] > 2.5).astype(int)
    df["Over35Goals"] = (df["TotalGoals"] > 3.5).astype(int)
    df["Over45Goals"] = (df["TotalGoals"] > 4.5).astype(int)

    df["Over75Corners"] = (df["TotalCorners"] > 7.5).astype(int)
    df["Over85Corners"] = (df["TotalCorners"] > 8.5).astype(int)
    df["Over95Corners"] = (df["TotalCorners"] > 9.5).astype(int)
    df["Over105Corners"] = (df["TotalCorners"] > 10.5).astype(int)
    df["Over115Corners"] = (df["TotalCorners"] > 11.5).astype(int)

    df = add_missing_columns(df, MASTER_COLUMNS)

    return df[MASTER_COLUMNS].copy()


# =========================================================
# SUMMARY + EXPORT
# =========================================================

def build_summary(master_df):
    if master_df.empty:
        return pd.DataFrame([{"Metric": "Rows", "Value": 0}])

    return pd.DataFrame([
        {"Metric": "Rows", "Value": len(master_df)},
        {"Metric": "Leagues", "Value": master_df["League"].nunique()},
        {"Metric": "Countries", "Value": master_df["Country"].nunique()},
        {"Metric": "Tiers", "Value": master_df["Tier"].nunique()},
        {"Metric": "Seasons", "Value": master_df["Season"].nunique()},
        {"Metric": "Teams", "Value": pd.concat([master_df["HomeTeam"], master_df["AwayTeam"]]).nunique()},
        {"Metric": "Earliest Match", "Value": str(master_df["MatchDate"].min().date())},
        {"Metric": "Latest Match", "Value": str(master_df["MatchDate"].max().date())},
        {"Metric": "Average Goals", "Value": round(master_df["TotalGoals"].mean(), 2)},
        {"Metric": "Average Corners", "Value": round(master_df["TotalCorners"].mean(), 2)},
        {"Metric": "BTTS Rate", "Value": round(master_df["BTTS"].mean(), 3)},
        {"Metric": "Over 2.5 Goals Rate", "Value": round(master_df["Over25Goals"].mean(), 3)},
        {"Metric": "Over 9.5 Corners Rate", "Value": round(master_df["Over95Corners"].mean(), 3)},
    ])


def build_league_summary(master_df):
    if master_df.empty:
        return pd.DataFrame()

    summary = (
        master_df
        .groupby(["Tier", "Country", "League"], dropna=False)
        .agg(
            Rows=("League", "count"),
            Seasons=("Season", "nunique"),
            Teams=("HomeTeam", "nunique"),
            EarliestMatch=("MatchDate", "min"),
            LatestMatch=("MatchDate", "max"),
            AvgGoals=("TotalGoals", "mean"),
            AvgCorners=("TotalCorners", "mean"),
            BTTSRate=("BTTS", "mean"),
            Over25Rate=("Over25Goals", "mean"),
            Over95CornersRate=("Over95Corners", "mean"),
        )
        .reset_index()
    )

    for col in [
        "AvgGoals",
        "AvgCorners",
        "BTTSRate",
        "Over25Rate",
        "Over95CornersRate",
    ]:
        summary[col] = summary[col].round(3)

    return summary


def export_workbook(path, master_df, update_log_df):
    summary_df = build_summary(master_df)
    league_summary_df = build_league_summary(master_df)

    with pd.ExcelWriter(path, engine="openpyxl", mode="w") as writer:
        master_df.to_excel(writer, sheet_name="Football_Master", index=False)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        league_summary_df.to_excel(writer, sheet_name="League_Summary", index=False)
        update_log_df.to_excel(writer, sheet_name="Update_Log", index=False)


# =========================================================
# MAIN BUILD
# =========================================================

def build_UKDATA27_football_master_dataset():
    ensure_directories()

    existing_master_df = safe_read_existing_master()
    all_new_frames = []
    update_log_rows = []

    print("\n======================================")
    print("HEXAGRANDHOUSE UKDATA27 FOOTBALL MASTER BUILD")
    print("======================================")
    print(f"Existing master rows: {len(existing_master_df)}")
    print("======================================")

    for season_item in SEASONS:
        season = season_item["Season"]
        season_code = season_item["SeasonCode"]

        for league_item in LEAGUES:
            league_code = league_item["LeagueCode"]
            league_name = league_item["LeagueName"]
            country = league_item["Country"]
            tier = league_item["Tier"]
            source_mode = league_item["SourceMode"]

            season_exists = league_season_exists(
                existing_master_df,
                season,
                league_code
            )

            active_season = is_active_season(season)

            if season_exists and not active_season:
                print("\n--------------------------------------")
                print(f"SKIPPING EXISTING: {season} | {league_name}")
                print("--------------------------------------")

                update_log_rows.append({
                    "Season": season,
                    "SeasonCode": season_code,
                    "LeagueCode": league_code,
                    "League": league_name,
                    "Country": country,
                    "Tier": tier,
                    "SourceMode": source_mode,
                    "Url": "",
                    "RawRows": 0,
                    "TransformedRows": 0,
                    "Status": "Skipped - Already Exists In Master",
                    "RunTimestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })

                continue

            url = build_source_url(
                season_code=season_code,
                league_code=league_code,
                source_mode=source_mode
            )

            raw_file = get_raw_file_path(
                season_code=season_code,
                league_code=league_code,
                source_mode=source_mode
            )

            print("\n--------------------------------------")
            print(f"Processing: {season} | {league_name}")
            print(f"Tier      : {tier}")
            print(f"URL       : {url}")
            print("--------------------------------------")

            raw_df = safe_read_csv_with_cache(
                url=url,
                raw_file=raw_file,
                force_refresh=active_season
            )

            transformed_df = transform_match_dataframe(
                raw_df=raw_df,
                season=season,
                season_code=season_code,
                league_code=league_code,
                league_name=league_name,
                country=country,
                tier=tier,
                source_mode=source_mode,
                source_url=url
            )

            if not transformed_df.empty:
                all_new_frames.append(transformed_df)

            update_log_rows.append({
                "Season": season,
                "SeasonCode": season_code,
                "LeagueCode": league_code,
                "League": league_name,
                "Country": country,
                "Tier": tier,
                "SourceMode": source_mode,
                "Url": url,
                "RawRows": len(raw_df),
                "TransformedRows": len(transformed_df),
                "RawFile": str(raw_file),
                "Status": "Success" if not transformed_df.empty else "Empty or Failed",
                "RunTimestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })

            print(f"Raw rows        : {len(raw_df)}")
            print(f"Transformed rows: {len(transformed_df)}")

    if all_new_frames:
        new_master_df = pd.concat(all_new_frames, ignore_index=True)
    else:
        new_master_df = pd.DataFrame(columns=MASTER_COLUMNS)

    master_df = pd.concat(
        [
            existing_master_df,
            new_master_df,
        ],
        ignore_index=True
    )

    if not master_df.empty:
        master_df = add_missing_columns(master_df, MASTER_COLUMNS)

        master_df = master_df.drop_duplicates(
            subset=["Season", "LeagueCode", "MatchDate", "HomeTeam", "AwayTeam"],
            keep="last"
        )

        master_df["MatchDate"] = pd.to_datetime(master_df["MatchDate"], errors="coerce")

        master_df = master_df.sort_values(
            by=["MatchDate", "Tier", "League", "HomeTeam", "AwayTeam"],
            ascending=[False, True, True, True, True]
        ).reset_index(drop=True)

        master_df = master_df[MASTER_COLUMNS].copy()

    update_log_df = pd.DataFrame(update_log_rows)

    tier1_df = master_df[master_df["Tier"] == "Tier 1 - Elite Europe"].copy()
    tier2_df = master_df[master_df["Tier"] == "Tier 2 - Europe Depth"].copy()
    tier3_df = master_df[master_df["Tier"] == "Tier 3 - Global"].copy()

    export_workbook(OUTPUT_ALL_FILE, master_df, update_log_df)
    export_workbook(OUTPUT_TIER1_FILE, tier1_df, update_log_df)
    export_workbook(OUTPUT_TIER2_FILE, tier2_df, update_log_df)
    export_workbook(OUTPUT_TIER3_FILE, tier3_df, update_log_df)

    print("\n======================================")
    print("UKDATA27 FOOTBALL MASTER DATASETS EXPORTED")
    print("======================================")
    print(f"All rows : {len(master_df)}")
    print(f"New rows : {len(new_master_df)}")
    print(f"Tier 1   : {len(tier1_df)} rows")
    print(f"Tier 2   : {len(tier2_df)} rows")
    print(f"Tier 3   : {len(tier3_df)} rows")
    print(f"All file : {OUTPUT_ALL_FILE}")
    print(f"Tier 1   : {OUTPUT_TIER1_FILE}")
    print(f"Tier 2   : {OUTPUT_TIER2_FILE}")
    print(f"Tier 3   : {OUTPUT_TIER3_FILE}")
    print("======================================\n")

    return master_df


def main():
    build_UKDATA27_football_master_dataset()


if __name__ == "__main__":
    main()