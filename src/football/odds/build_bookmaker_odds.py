from pathlib import Path
from datetime import datetime

import pandas as pd


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

MASTER_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "master"
)

ODDS_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "odds"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "exports"
    / "odds"
)

FIXTURES_FILE = (
    MASTER_DIR
    / "football_fixtures.csv"
)

MANUAL_ODDS_TEMPLATE_FILE = (
    ODDS_DIR
    / "manual_bookmaker_odds_template.xlsx"
)

MANUAL_ODDS_INPUT_FILE = (
    ODDS_DIR
    / "manual_bookmaker_odds_input.xlsx"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "bookmaker_odds_master.xlsx"
)

OUTPUT_CSV = (
    OUTPUT_DIR
    / "bookmaker_odds_master.csv"
)


# =========================================================
# CONFIG
# =========================================================

ODDS_COLUMNS = [
    "AverageHomeOdds",
    "AverageDrawOdds",
    "AverageAwayOdds",
    "AverageOver25Odds",
    "AverageUnder25Odds",
]

BASE_COLUMNS = [
    "FixtureKey",
    "FixtureDate",
    "KickoffTime",
    "Tier",
    "Country",
    "League",
    "LeagueCode",
    "HomeTeam",
    "AwayTeam",
]


# =========================================================
# HELPERS
# =========================================================

def ensure_directories():
    ODDS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def safe_read_csv(path):
    try:
        return pd.read_csv(
            path,
            low_memory=False
        )

    except Exception as e:
        print(f"Could not read CSV: {path}")
        print(f"Error: {e}")
        return pd.DataFrame()


def safe_read_excel(path, sheet_name=0):
    try:
        return pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine="openpyxl"
        )

    except Exception as e:
        print(f"Could not read Excel: {path}")
        print(f"Error: {e}")
        return pd.DataFrame()


def safe_numeric(df, col):
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    return df


def build_fixture_key(row):
    date_value = row.get(
        "FixtureDate",
        ""
    )

    try:
        date_value = pd.to_datetime(
            date_value
        ).strftime("%Y-%m-%d")

    except Exception:
        date_value = str(date_value)

    league_code = str(
        row.get(
            "LeagueCode",
            ""
        )
    ).strip()

    home_team = str(
        row.get(
            "HomeTeam",
            ""
        )
    ).strip()

    away_team = str(
        row.get(
            "AwayTeam",
            ""
        )
    ).strip()

    return (
        date_value
        + "|"
        + league_code
        + "|"
        + home_team
        + "|"
        + away_team
    )


def create_fixture_key_if_missing(df):
    df = df.copy()

    if "FixtureKey" not in df.columns:
        df["FixtureKey"] = df.apply(
            build_fixture_key,
            axis=1
        )

    return df


# =========================================================
# TEMPLATE
# =========================================================

def create_manual_odds_template(fixtures_df):
    if fixtures_df.empty:
        return pd.DataFrame()

    df = fixtures_df.copy()

    df = create_fixture_key_if_missing(
        df
    )

    keep_cols = [
        col for col in BASE_COLUMNS
        if col in df.columns
    ]

    template_df = df[
        keep_cols
    ].copy()

    for col in ODDS_COLUMNS:
        if col not in template_df.columns:
            template_df[col] = None

    template_df["OddsSource"] = "Manual"
    template_df["OddsCapturedAt"] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return template_df


# =========================================================
# ODDS NORMALISATION
# =========================================================

def normalise_manual_odds(input_df):
    if input_df.empty:
        return pd.DataFrame()

    df = input_df.copy()

    df = create_fixture_key_if_missing(
        df
    )

    for col in ODDS_COLUMNS:
        df = safe_numeric(
            df,
            col
        )

    keep_cols = [
        col for col in BASE_COLUMNS + ODDS_COLUMNS + [
            "OddsSource",
            "OddsCapturedAt",
        ]
        if col in df.columns
    ]

    df = df[
        keep_cols
    ].copy()

    if "OddsSource" not in df.columns:
        df["OddsSource"] = "Manual"

    if "OddsCapturedAt" not in df.columns:
        df["OddsCapturedAt"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    return df


def remove_empty_odds_rows(df):
    if df.empty:
        return df

    available_odds_cols = [
        col for col in ODDS_COLUMNS
        if col in df.columns
    ]

    if not available_odds_cols:
        return pd.DataFrame()

    return df[
        df[available_odds_cols]
        .notna()
        .any(axis=1)
    ].copy()


# =========================================================
# SUMMARIES
# =========================================================

def build_summary(odds_df, template_df):
    return pd.DataFrame(
        [
            {
                "Metric": "Template Rows",
                "Value": len(template_df),
            },
            {
                "Metric": "Odds Rows",
                "Value": len(odds_df),
            },
            {
                "Metric": "Rows With Home Odds",
                "Value": int(
                    odds_df["AverageHomeOdds"].notna().sum()
                )
                if "AverageHomeOdds" in odds_df.columns
                else 0,
            },
            {
                "Metric": "Rows With Draw Odds",
                "Value": int(
                    odds_df["AverageDrawOdds"].notna().sum()
                )
                if "AverageDrawOdds" in odds_df.columns
                else 0,
            },
            {
                "Metric": "Rows With Away Odds",
                "Value": int(
                    odds_df["AverageAwayOdds"].notna().sum()
                )
                if "AverageAwayOdds" in odds_df.columns
                else 0,
            },
            {
                "Metric": "Rows With Over 2.5 Odds",
                "Value": int(
                    odds_df["AverageOver25Odds"].notna().sum()
                )
                if "AverageOver25Odds" in odds_df.columns
                else 0,
            },
            {
                "Metric": "Rows With Under 2.5 Odds",
                "Value": int(
                    odds_df["AverageUnder25Odds"].notna().sum()
                )
                if "AverageUnder25Odds" in odds_df.columns
                else 0,
            },
            {
                "Metric": "Generated At",
                "Value": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            },
        ]
    )


def build_league_summary(odds_df):
    if odds_df.empty:
        return pd.DataFrame()

    if "League" not in odds_df.columns:
        return pd.DataFrame()

    return (
        odds_df
        .groupby(
            [
                "Tier",
                "Country",
                "League",
            ],
            dropna=False
        )
        .agg(
            FixturesWithOdds=("League", "count"),
            AvgHomeOdds=("AverageHomeOdds", "mean"),
            AvgDrawOdds=("AverageDrawOdds", "mean"),
            AvgAwayOdds=("AverageAwayOdds", "mean"),
            AvgOver25Odds=("AverageOver25Odds", "mean"),
            AvgUnder25Odds=("AverageUnder25Odds", "mean"),
        )
        .reset_index()
        .round(3)
    )


# =========================================================
# EXPORT
# =========================================================

def export_bookmaker_odds():
    ensure_directories()

    fixtures_df = safe_read_csv(
        FIXTURES_FILE
    )

    if fixtures_df.empty:
        print("No fixtures found.")
        return pd.DataFrame()

    template_df = create_manual_odds_template(
        fixtures_df
    )

    with pd.ExcelWriter(
        MANUAL_ODDS_TEMPLATE_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:

        template_df.to_excel(
            writer,
            sheet_name="Manual_Odds_Template",
            index=False
        )

    if MANUAL_ODDS_INPUT_FILE.exists():
        manual_input_df = safe_read_excel(
            MANUAL_ODDS_INPUT_FILE,
            "Manual_Odds_Template"
        )

        odds_df = normalise_manual_odds(
            manual_input_df
        )

        odds_df = remove_empty_odds_rows(
            odds_df
        )

    else:
        odds_df = pd.DataFrame(
            columns=template_df.columns
        )

    summary_df = build_summary(
        odds_df,
        template_df
    )

    league_summary_df = build_league_summary(
        odds_df
    )

    odds_df.to_csv(
        OUTPUT_CSV,
        index=False
    )

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
        mode="w"
    ) as writer:

        odds_df.to_excel(
            writer,
            sheet_name="Bookmaker_Odds",
            index=False
        )

        template_df.to_excel(
            writer,
            sheet_name="Manual_Odds_Template",
            index=False
        )

        summary_df.to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

        league_summary_df.to_excel(
            writer,
            sheet_name="League_Summary",
            index=False
        )

    print("\n======================================")
    print("BOOKMAKER ODDS EXPORTED")
    print("======================================")
    print(f"Template rows : {len(template_df)}")
    print(f"Odds rows     : {len(odds_df)}")
    print(f"Template file : {MANUAL_ODDS_TEMPLATE_FILE}")
    print(f"Excel         : {OUTPUT_FILE}")
    print(f"CSV           : {OUTPUT_CSV}")
    print("======================================\n")

    return odds_df


def main():
    export_bookmaker_odds()


if __name__ == "__main__":
    main()