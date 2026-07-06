from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.data.sqlite_store import (
    create_indexes,
    read_sqlite_table,
    replace_sqlite_table,
)


# =========================================================
# SQLITE TABLES
# =========================================================

SOURCE_TABLE = "football_history"
MATCH_FEATURES_TABLE = "football_match_features"
TEAM_MATCH_LONG_TABLE = "football_team_match_long"
TEAM_FEATURES_TABLE = "football_team_features"
TIER1_MATCH_FEATURES_TABLE = "football_match_features_tier1"
TIER2_MATCH_FEATURES_TABLE = "football_match_features_tier2"
TIER3_MATCH_FEATURES_TABLE = "football_match_features_tier3"
FEATURE_SUMMARY_TABLE = "football_feature_summary"
FEATURE_DICTIONARY_TABLE = "football_feature_dictionary"


# =========================================================
# CONFIG
# =========================================================

ROLLING_WINDOWS = [
    3,
    5,
    10,
]

BASE_REQUIRED_COLUMNS = [
    "Season",
    "SeasonCode",
    "LeagueCode",
    "League",
    "Country",
    "Tier",
    "MatchDate",
    "HomeTeam",
    "AwayTeam",
    "HomeGoals",
    "AwayGoals",
    "Result",
    "ResultLabel",
    "HomeShots",
    "AwayShots",
    "HomeShotsOnTarget",
    "AwayShotsOnTarget",
    "HomeCorners",
    "AwayCorners",
    "TotalGoals",
    "TotalCorners",
    "BTTS",
    "Over25Goals",
    "Over95Corners",
]

NUMERIC_COLUMNS = [
    "HomeGoals",
    "AwayGoals",
    "HomeShots",
    "AwayShots",
    "HomeShotsOnTarget",
    "AwayShotsOnTarget",
    "HomeCorners",
    "AwayCorners",
    "TotalGoals",
    "TotalCorners",
    "BTTS",
    "Over25Goals",
    "Over95Corners",
]

TIER_LABELS = {
    "tier1": "Tier 1 - Elite Europe",
    "tier2": "Tier 2 - Europe Depth",
    "tier3": "Tier 3 - Global",
}


# =========================================================
# BASIC HELPERS
# =========================================================

def add_missing_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()

    for col in columns:
        if col not in out.columns:
            out[col] = None

    return out


def safe_numeric(df: pd.DataFrame, col: str) -> pd.DataFrame:
    out = df.copy()

    if col in out.columns:
        out[col] = pd.to_numeric(
            out[col],
            errors="coerce",
        )

    return out


def result_points_for_team(result: str, side: str) -> int:
    if result == "H" and side == "Home":
        return 3

    if result == "A" and side == "Away":
        return 3

    if result == "D":
        return 1

    return 0


def result_win_flag(result: str, side: str) -> int:
    if result == "H" and side == "Home":
        return 1

    if result == "A" and side == "Away":
        return 1

    return 0


def result_draw_flag(result: str) -> int:
    if result == "D":
        return 1

    return 0


def result_loss_flag(result: str, side: str) -> int:
    if result == "A" and side == "Home":
        return 1

    if result == "H" and side == "Away":
        return 1

    return 0


# =========================================================
# SOURCE LOAD
# =========================================================

def load_football_history() -> pd.DataFrame:
    df = read_sqlite_table(SOURCE_TABLE)

    if df.empty:
        return pd.DataFrame()

    df = add_missing_columns(df, BASE_REQUIRED_COLUMNS)

    df["MatchDate"] = pd.to_datetime(
        df["MatchDate"],
        errors="coerce",
    )

    for col in NUMERIC_COLUMNS:
        df = safe_numeric(df, col)

    # Make the model layer resilient where older source data has blanks.
    if "TotalGoals" in df.columns:
        df["TotalGoals"] = df["TotalGoals"].fillna(
            df["HomeGoals"].fillna(0) + df["AwayGoals"].fillna(0)
        )

    if "TotalCorners" in df.columns:
        df["TotalCorners"] = df["TotalCorners"].fillna(
            df["HomeCorners"].fillna(0) + df["AwayCorners"].fillna(0)
        )

    if "BTTS" in df.columns:
        df["BTTS"] = df["BTTS"].fillna(
            (
                (df["HomeGoals"].fillna(0) > 0)
                & (df["AwayGoals"].fillna(0) > 0)
            ).astype(int)
        )

    if "Over25Goals" in df.columns:
        df["Over25Goals"] = df["Over25Goals"].fillna(
            (df["TotalGoals"].fillna(0) > 2.5).astype(int)
        )

    if "Over95Corners" in df.columns:
        df["Over95Corners"] = df["Over95Corners"].fillna(
            (df["TotalCorners"].fillna(0) > 9.5).astype(int)
        )

    df = df[df["MatchDate"].notna()].copy()

    df = df.sort_values(
        by=[
            "LeagueCode",
            "MatchDate",
            "HomeTeam",
            "AwayTeam",
        ],
        ascending=[
            True,
            True,
            True,
            True,
        ],
    ).reset_index(drop=True)

    return df


# =========================================================
# TEAM MATCH LONG TABLE
# =========================================================

def build_team_match_long(master_df: pd.DataFrame) -> pd.DataFrame:
    home_rows = master_df.copy()

    home_rows["Team"] = home_rows["HomeTeam"]
    home_rows["Opponent"] = home_rows["AwayTeam"]
    home_rows["Venue"] = "Home"

    home_rows["GoalsFor"] = home_rows["HomeGoals"]
    home_rows["GoalsAgainst"] = home_rows["AwayGoals"]

    home_rows["ShotsFor"] = home_rows["HomeShots"]
    home_rows["ShotsAgainst"] = home_rows["AwayShots"]

    home_rows["ShotsOnTargetFor"] = home_rows["HomeShotsOnTarget"]
    home_rows["ShotsOnTargetAgainst"] = home_rows["AwayShotsOnTarget"]

    home_rows["CornersFor"] = home_rows["HomeCorners"]
    home_rows["CornersAgainst"] = home_rows["AwayCorners"]

    away_rows = master_df.copy()

    away_rows["Team"] = away_rows["AwayTeam"]
    away_rows["Opponent"] = away_rows["HomeTeam"]
    away_rows["Venue"] = "Away"

    away_rows["GoalsFor"] = away_rows["AwayGoals"]
    away_rows["GoalsAgainst"] = away_rows["HomeGoals"]

    away_rows["ShotsFor"] = away_rows["AwayShots"]
    away_rows["ShotsAgainst"] = away_rows["HomeShots"]

    away_rows["ShotsOnTargetFor"] = away_rows["AwayShotsOnTarget"]
    away_rows["ShotsOnTargetAgainst"] = away_rows["HomeShotsOnTarget"]

    away_rows["CornersFor"] = away_rows["AwayCorners"]
    away_rows["CornersAgainst"] = away_rows["HomeCorners"]

    home_rows["Points"] = home_rows["Result"].apply(
        lambda x: result_points_for_team(x, "Home")
    )

    away_rows["Points"] = away_rows["Result"].apply(
        lambda x: result_points_for_team(x, "Away")
    )

    home_rows["Win"] = home_rows["Result"].apply(
        lambda x: result_win_flag(x, "Home")
    )

    away_rows["Win"] = away_rows["Result"].apply(
        lambda x: result_win_flag(x, "Away")
    )

    home_rows["Draw"] = home_rows["Result"].apply(result_draw_flag)
    away_rows["Draw"] = away_rows["Result"].apply(result_draw_flag)

    home_rows["Loss"] = home_rows["Result"].apply(
        lambda x: result_loss_flag(x, "Home")
    )

    away_rows["Loss"] = away_rows["Result"].apply(
        lambda x: result_loss_flag(x, "Away")
    )

    common_cols = [
        "Season",
        "SeasonCode",
        "LeagueCode",
        "League",
        "Country",
        "Tier",
        "MatchDate",
        "Team",
        "Opponent",
        "Venue",
        "GoalsFor",
        "GoalsAgainst",
        "ShotsFor",
        "ShotsAgainst",
        "ShotsOnTargetFor",
        "ShotsOnTargetAgainst",
        "CornersFor",
        "CornersAgainst",
        "TotalGoals",
        "TotalCorners",
        "BTTS",
        "Over25Goals",
        "Over95Corners",
        "Result",
        "Points",
        "Win",
        "Draw",
        "Loss",
    ]

    team_long = pd.concat(
        [
            home_rows[common_cols],
            away_rows[common_cols],
        ],
        ignore_index=True,
    )

    team_long = team_long.sort_values(
        by=[
            "LeagueCode",
            "Team",
            "MatchDate",
        ],
        ascending=[
            True,
            True,
            True,
        ],
    ).reset_index(drop=True)

    return team_long


# =========================================================
# ROLLING FEATURES
# =========================================================

def add_rolling_features(team_long: pd.DataFrame) -> pd.DataFrame:
    df = team_long.copy()

    rolling_columns = [
        "Points",
        "Win",
        "Draw",
        "Loss",
        "GoalsFor",
        "GoalsAgainst",
        "ShotsFor",
        "ShotsAgainst",
        "ShotsOnTargetFor",
        "ShotsOnTargetAgainst",
        "CornersFor",
        "CornersAgainst",
        "BTTS",
        "Over25Goals",
        "Over95Corners",
    ]

    group_cols = [
        "LeagueCode",
        "Team",
    ]

    for window in ROLLING_WINDOWS:
        for col in rolling_columns:
            feature_name = f"{col}_Last{window}"

            df[feature_name] = (
                df.groupby(group_cols)[col]
                .transform(
                    lambda x: (
                        x.shift(1)
                        .rolling(window=window, min_periods=1)
                        .mean()
                    )
                )
            )

        df[f"FormPoints_Last{window}"] = df[f"Points_Last{window}"]
        df[f"WinRate_Last{window}"] = df[f"Win_Last{window}"]
        df[f"DrawRate_Last{window}"] = df[f"Draw_Last{window}"]
        df[f"LossRate_Last{window}"] = df[f"Loss_Last{window}"]

        df[f"GoalDifference_Last{window}"] = (
            df[f"GoalsFor_Last{window}"]
            - df[f"GoalsAgainst_Last{window}"]
        )

        df[f"ShotDifference_Last{window}"] = (
            df[f"ShotsFor_Last{window}"]
            - df[f"ShotsAgainst_Last{window}"]
        )

        df[f"SOTDifference_Last{window}"] = (
            df[f"ShotsOnTargetFor_Last{window}"]
            - df[f"ShotsOnTargetAgainst_Last{window}"]
        )

        df[f"CornerDifference_Last{window}"] = (
            df[f"CornersFor_Last{window}"]
            - df[f"CornersAgainst_Last{window}"]
        )

    return df


def add_home_away_rolling_features(team_long: pd.DataFrame) -> pd.DataFrame:
    df = team_long.copy()

    rolling_columns = [
        "Points",
        "Win",
        "GoalsFor",
        "GoalsAgainst",
        "CornersFor",
        "CornersAgainst",
        "BTTS",
        "Over25Goals",
        "Over95Corners",
    ]

    group_cols = [
        "LeagueCode",
        "Team",
        "Venue",
    ]

    for window in ROLLING_WINDOWS:
        for col in rolling_columns:
            feature_name = f"{col}_VenueLast{window}"

            df[feature_name] = (
                df.groupby(group_cols)[col]
                .transform(
                    lambda x: (
                        x.shift(1)
                        .rolling(window=window, min_periods=1)
                        .mean()
                    )
                )
            )

    return df


# =========================================================
# MATCH LEVEL FEATURES
# =========================================================

def build_match_features(
    master_df: pd.DataFrame,
    team_features: pd.DataFrame,
) -> pd.DataFrame:
    home_features = team_features[team_features["Venue"] == "Home"].copy()
    away_features = team_features[team_features["Venue"] == "Away"].copy()

    base_keys = [
        "Season",
        "SeasonCode",
        "LeagueCode",
        "MatchDate",
    ]

    home_features["HomeTeam"] = home_features["Team"]
    away_features["AwayTeam"] = away_features["Team"]

    home_feature_cols = [
        col
        for col in home_features.columns
        if (
            col.endswith("_Last3")
            or col.endswith("_Last5")
            or col.endswith("_Last10")
            or col.endswith("_VenueLast3")
            or col.endswith("_VenueLast5")
            or col.endswith("_VenueLast10")
        )
    ]

    away_feature_cols = [
        col
        for col in away_features.columns
        if (
            col.endswith("_Last3")
            or col.endswith("_Last5")
            or col.endswith("_Last10")
            or col.endswith("_VenueLast3")
            or col.endswith("_VenueLast5")
            or col.endswith("_VenueLast10")
        )
    ]

    home_rename = {
        col: f"Home_{col}"
        for col in home_feature_cols
    }

    away_rename = {
        col: f"Away_{col}"
        for col in away_feature_cols
    }

    home_merge = home_features[
        base_keys + ["HomeTeam"] + home_feature_cols
    ].rename(columns=home_rename)

    away_merge = away_features[
        base_keys + ["AwayTeam"] + away_feature_cols
    ].rename(columns=away_rename)

    df = master_df.copy()

    df = df.merge(
        home_merge,
        on=base_keys + ["HomeTeam"],
        how="left",
    )

    df = df.merge(
        away_merge,
        on=base_keys + ["AwayTeam"],
        how="left",
    )

    for window in ROLLING_WINDOWS:
        home_points_col = f"Home_FormPoints_Last{window}"
        away_points_col = f"Away_FormPoints_Last{window}"

        if home_points_col in df.columns and away_points_col in df.columns:
            df[f"FormPointsDiff_Last{window}"] = (
                df[home_points_col].fillna(0)
                - df[away_points_col].fillna(0)
            )

        home_goals_for_col = f"Home_GoalsFor_Last{window}"
        away_goals_for_col = f"Away_GoalsFor_Last{window}"

        if home_goals_for_col in df.columns and away_goals_for_col in df.columns:
            df[f"AttackStrengthDiff_Last{window}"] = (
                df[home_goals_for_col].fillna(0)
                - df[away_goals_for_col].fillna(0)
            )

        home_goals_against_col = f"Home_GoalsAgainst_Last{window}"
        away_goals_against_col = f"Away_GoalsAgainst_Last{window}"

        if home_goals_against_col in df.columns and away_goals_against_col in df.columns:
            df[f"DefenceWeaknessDiff_Last{window}"] = (
                df[home_goals_against_col].fillna(0)
                - df[away_goals_against_col].fillna(0)
            )

        home_corners_for_col = f"Home_CornersFor_Last{window}"
        away_corners_for_col = f"Away_CornersFor_Last{window}"

        if home_corners_for_col in df.columns and away_corners_for_col in df.columns:
            df[f"CornerAttackDiff_Last{window}"] = (
                df[home_corners_for_col].fillna(0)
                - df[away_corners_for_col].fillna(0)
            )

    return df


# =========================================================
# SUMMARY TABLES
# =========================================================

def build_feature_summary(
    match_features: pd.DataFrame,
    update_note: str,
) -> pd.DataFrame:
    if match_features.empty:
        return pd.DataFrame(
            [
                {
                    "Metric": "Rows",
                    "Value": 0,
                }
            ]
        )

    feature_cols = [
        col
        for col in match_features.columns
        if (
            "_Last" in col
            or "_VenueLast" in col
            or "Diff_Last" in col
        )
    ]

    rows = [
        {
            "Metric": "Rows",
            "Value": len(match_features),
        },
        {
            "Metric": "Feature Columns",
            "Value": len(feature_cols),
        },
        {
            "Metric": "Leagues",
            "Value": match_features["League"].nunique()
            if "League" in match_features.columns
            else 0,
        },
        {
            "Metric": "Tiers",
            "Value": match_features["Tier"].nunique()
            if "Tier" in match_features.columns
            else 0,
        },
        {
            "Metric": "Seasons",
            "Value": match_features["Season"].nunique()
            if "Season" in match_features.columns
            else 0,
        },
        {
            "Metric": "Teams",
            "Value": pd.concat(
                [
                    match_features["HomeTeam"],
                    match_features["AwayTeam"],
                ]
            ).nunique()
            if (
                "HomeTeam" in match_features.columns
                and "AwayTeam" in match_features.columns
            )
            else 0,
        },
        {
            "Metric": "Generated At",
            "Value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        {
            "Metric": "Output Scope",
            "Value": update_note,
        },
    ]

    return pd.DataFrame(rows)


def build_feature_dictionary() -> pd.DataFrame:
    rows = [
        {
            "FeatureFamily": "Form",
            "Description": "Rolling points, wins, draws and losses per league/team.",
        },
        {
            "FeatureFamily": "Goals",
            "Description": "Rolling goals scored and conceded.",
        },
        {
            "FeatureFamily": "Shots",
            "Description": "Rolling shots and shots-on-target created and allowed.",
        },
        {
            "FeatureFamily": "Corners",
            "Description": "Rolling corners created and conceded.",
        },
        {
            "FeatureFamily": "Markets",
            "Description": "Rolling BTTS, over 2.5 goals and over 9.5 corners rates.",
        },
        {
            "FeatureFamily": "Diff Features",
            "Description": "Home minus away comparative features at match level.",
        },
        {
            "FeatureFamily": "Venue Features",
            "Description": "Home-only and away-only rolling strength indicators.",
        },
    ]

    return pd.DataFrame(rows)


# =========================================================
# SQLITE EXPORT
# =========================================================

def save_football_features_to_sqlite(
    master_df: pd.DataFrame,
    team_long: pd.DataFrame,
    team_features: pd.DataFrame,
    match_features: pd.DataFrame,
) -> dict[str, int]:
    tier1_match = match_features[
        match_features["Tier"] == TIER_LABELS["tier1"]
    ].copy()

    tier2_match = match_features[
        match_features["Tier"] == TIER_LABELS["tier2"]
    ].copy()

    tier3_match = match_features[
        match_features["Tier"] == TIER_LABELS["tier3"]
    ].copy()

    summary_df = build_feature_summary(
        match_features,
        "All football leagues from SQLite warehouse",
    )

    dictionary_df = build_feature_dictionary()

    row_counts = {
        TEAM_MATCH_LONG_TABLE: replace_sqlite_table(
            TEAM_MATCH_LONG_TABLE,
            team_long,
        ),
        TEAM_FEATURES_TABLE: replace_sqlite_table(
            TEAM_FEATURES_TABLE,
            team_features,
        ),
        MATCH_FEATURES_TABLE: replace_sqlite_table(
            MATCH_FEATURES_TABLE,
            match_features,
        ),
        TIER1_MATCH_FEATURES_TABLE: replace_sqlite_table(
            TIER1_MATCH_FEATURES_TABLE,
            tier1_match,
        ),
        TIER2_MATCH_FEATURES_TABLE: replace_sqlite_table(
            TIER2_MATCH_FEATURES_TABLE,
            tier2_match,
        ),
        TIER3_MATCH_FEATURES_TABLE: replace_sqlite_table(
            TIER3_MATCH_FEATURES_TABLE,
            tier3_match,
        ),
        FEATURE_SUMMARY_TABLE: replace_sqlite_table(
            FEATURE_SUMMARY_TABLE,
            summary_df,
        ),
        FEATURE_DICTIONARY_TABLE: replace_sqlite_table(
            FEATURE_DICTIONARY_TABLE,
            dictionary_df,
        ),
    }

    create_indexes(
        MATCH_FEATURES_TABLE,
        [
            "MatchDate",
            "League",
            "LeagueCode",
            "HomeTeam",
            "AwayTeam",
            "Tier",
        ],
    )

    create_indexes(
        TEAM_FEATURES_TABLE,
        [
            "MatchDate",
            "League",
            "LeagueCode",
            "Team",
            "Venue",
            "Tier",
        ],
    )

    create_indexes(
        TEAM_MATCH_LONG_TABLE,
        [
            "MatchDate",
            "League",
            "LeagueCode",
            "Team",
            "Venue",
            "Tier",
        ],
    )

    return row_counts


# =========================================================
# MAIN PIPELINE
# =========================================================

def build_football_features() -> pd.DataFrame:
    print("\n======================================")
    print("HEXAGRANDHOUSE FOOTBALL FEATURE BUILD")
    print("SQLite-first runtime mode")
    print("======================================")
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("======================================\n")

    master_df = load_football_history()

    if master_df.empty:
        print("No football history found in SQLite.")
        return pd.DataFrame()

    team_long = build_team_match_long(master_df)

    team_features = add_rolling_features(team_long)
    team_features = add_home_away_rolling_features(team_features)

    match_features = build_match_features(
        master_df,
        team_features,
    )

    row_counts = save_football_features_to_sqlite(
        master_df=master_df,
        team_long=team_long,
        team_features=team_features,
        match_features=match_features,
    )

    print("\n======================================")
    print("FOOTBALL FEATURE BUILD COMPLETE")
    print("======================================")

    for table_name, row_count in row_counts.items():
        print(f"{table_name:<36} | Rows: {row_count}")

    print("--------------------------------------")
    print(f"TOTAL MATCH FEATURES{'':<17} | Rows: {len(match_features)}")
    print("======================================\n")

    return match_features


def main() -> None:
    build_football_features()


if __name__ == "__main__":
    main()
