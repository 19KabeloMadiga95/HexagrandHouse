from pathlib import Path
from datetime import datetime

import pandas as pd


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[3]

MASTER_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "master"
)

FEATURES_DIR = (
    BASE_DIR
    / "data"
    / "football"
    / "processed"
    / "features"
)

MASTER_ALL_FILE = (
    MASTER_DIR
    / "football_master_all_leagues.xlsx"
)

OUTPUT_ALL_FILE = (
    FEATURES_DIR
    / "football_features_all_leagues.xlsx"
)

OUTPUT_TIER1_FILE = (
    FEATURES_DIR
    / "football_features_tier1_elite.xlsx"
)

OUTPUT_TIER2_FILE = (
    FEATURES_DIR
    / "football_features_tier2_europe.xlsx"
)

OUTPUT_TIER3_FILE = (
    FEATURES_DIR
    / "football_features_tier3_global.xlsx"
)


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


# =========================================================
# HELPERS
# =========================================================

def ensure_directories():
    FEATURES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def safe_read_excel(
    path,
    sheet_name=0
):
    try:
        return pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine="openpyxl"
        )

    except Exception as e:
        print(f"Failed to read file: {path}")
        print(f"Error: {e}")

        return pd.DataFrame()


def add_missing_columns(
    df,
    columns
):
    for col in columns:
        if col not in df.columns:
            df[col] = None

    return df


def safe_numeric(
    df,
    col
):
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    return df


def result_points_for_team(
    result,
    side
):
    if result == "H" and side == "Home":
        return 3

    if result == "A" and side == "Away":
        return 3

    if result == "D":
        return 1

    return 0


def result_win_flag(
    result,
    side
):
    if result == "H" and side == "Home":
        return 1

    if result == "A" and side == "Away":
        return 1

    return 0


def result_draw_flag(result):
    if result == "D":
        return 1

    return 0


def result_loss_flag(
    result,
    side
):
    if result == "A" and side == "Home":
        return 1

    if result == "H" and side == "Away":
        return 1

    return 0


def export_feature_workbook(
    output_file,
    match_features,
    team_features,
    update_note
):
    output_folder = output_file.with_suffix("")
    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    match_features_file = (
        output_folder
        / "match_features.csv"
    )

    team_features_file = (
        output_folder
        / "team_features_long.csv"
    )

    summary_file = (
        output_folder
        / "feature_summary.xlsx"
    )

    feature_summary = build_feature_summary(
        match_features,
        update_note
    )

    feature_dictionary = build_feature_dictionary()

    match_features.to_csv(
        match_features_file,
        index=False
    )

    team_features.to_csv(
        team_features_file,
        index=False
    )

    with pd.ExcelWriter(
        summary_file,
        engine="openpyxl",
        mode="w"
    ) as writer:

        feature_summary.to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

        feature_dictionary.to_excel(
            writer,
            sheet_name="Feature_Dictionary",
            index=False
        )


# =========================================================
# TEAM MATCH LONG TABLE
# =========================================================

def build_team_match_long(master_df):
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
        lambda x: result_points_for_team(
            x,
            "Home"
        )
    )

    away_rows["Points"] = away_rows["Result"].apply(
        lambda x: result_points_for_team(
            x,
            "Away"
        )
    )

    home_rows["Win"] = home_rows["Result"].apply(
        lambda x: result_win_flag(
            x,
            "Home"
        )
    )

    away_rows["Win"] = away_rows["Result"].apply(
        lambda x: result_win_flag(
            x,
            "Away"
        )
    )

    home_rows["Draw"] = home_rows["Result"].apply(
        result_draw_flag
    )

    away_rows["Draw"] = away_rows["Result"].apply(
        result_draw_flag
    )

    home_rows["Loss"] = home_rows["Result"].apply(
        lambda x: result_loss_flag(
            x,
            "Home"
        )
    )

    away_rows["Loss"] = away_rows["Result"].apply(
        lambda x: result_loss_flag(
            x,
            "Away"
        )
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
        ignore_index=True
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
        ]
    ).reset_index(drop=True)

    return team_long


# =========================================================
# ROLLING FEATURES
# =========================================================

def add_rolling_features(team_long):
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
                df
                .groupby(group_cols)[col]
                .transform(
                    lambda x: (
                        x.shift(1)
                        .rolling(
                            window=window,
                            min_periods=1
                        )
                        .mean()
                    )
                )
            )

        df[f"FormPoints_Last{window}"] = (
            df[f"Points_Last{window}"]
        )

        df[f"WinRate_Last{window}"] = (
            df[f"Win_Last{window}"]
        )

        df[f"DrawRate_Last{window}"] = (
            df[f"Draw_Last{window}"]
        )

        df[f"LossRate_Last{window}"] = (
            df[f"Loss_Last{window}"]
        )

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


def add_home_away_rolling_features(team_long):
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
                df
                .groupby(group_cols)[col]
                .transform(
                    lambda x: (
                        x.shift(1)
                        .rolling(
                            window=window,
                            min_periods=1
                        )
                        .mean()
                    )
                )
            )

    return df


# =========================================================
# MATCH LEVEL FEATURES
# =========================================================

def build_match_features(master_df, team_features):
    home_features = team_features[
        team_features["Venue"] == "Home"
    ].copy()

    away_features = team_features[
        team_features["Venue"] == "Away"
    ].copy()

    base_keys = [
        "Season",
        "SeasonCode",
        "LeagueCode",
        "MatchDate",
    ]

    home_features["HomeTeam"] = home_features["Team"]
    away_features["AwayTeam"] = away_features["Team"]

    home_feature_cols = [
        col for col in home_features.columns
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
        col for col in away_features.columns
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
        base_keys
        + ["HomeTeam"]
        + home_feature_cols
    ].rename(
        columns=home_rename
    )

    away_merge = away_features[
        base_keys
        + ["AwayTeam"]
        + away_feature_cols
    ].rename(
        columns=away_rename
    )

    df = master_df.copy()

    df = df.merge(
        home_merge,
        on=base_keys + ["HomeTeam"],
        how="left"
    )

    df = df.merge(
        away_merge,
        on=base_keys + ["AwayTeam"],
        how="left"
    )

    for window in ROLLING_WINDOWS:
        home_points_col = f"Home_FormPoints_Last{window}"
        away_points_col = f"Away_FormPoints_Last{window}"

        if (
            home_points_col in df.columns
            and away_points_col in df.columns
        ):
            df[f"FormPointsDiff_Last{window}"] = (
                df[home_points_col].fillna(0)
                - df[away_points_col].fillna(0)
            )

        home_goals_for_col = f"Home_GoalsFor_Last{window}"
        away_goals_for_col = f"Away_GoalsFor_Last{window}"

        if (
            home_goals_for_col in df.columns
            and away_goals_for_col in df.columns
        ):
            df[f"AttackStrengthDiff_Last{window}"] = (
                df[home_goals_for_col].fillna(0)
                - df[away_goals_for_col].fillna(0)
            )

        home_goals_against_col = f"Home_GoalsAgainst_Last{window}"
        away_goals_against_col = f"Away_GoalsAgainst_Last{window}"

        if (
            home_goals_against_col in df.columns
            and away_goals_against_col in df.columns
        ):
            df[f"DefenceWeaknessDiff_Last{window}"] = (
                df[home_goals_against_col].fillna(0)
                - df[away_goals_against_col].fillna(0)
            )

        home_corners_for_col = f"Home_CornersFor_Last{window}"
        away_corners_for_col = f"Away_CornersFor_Last{window}"

        if (
            home_corners_for_col in df.columns
            and away_corners_for_col in df.columns
        ):
            df[f"CornerAttackDiff_Last{window}"] = (
                df[home_corners_for_col].fillna(0)
                - df[away_corners_for_col].fillna(0)
            )

    return df


# =========================================================
# SUMMARY
# =========================================================

def build_feature_summary(
    match_features,
    update_note
):
    if match_features.empty:
        return pd.DataFrame([
            {
                "Metric": "Rows",
                "Value": 0,
            }
        ])

    feature_cols = [
        col for col in match_features.columns
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
            "Value": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        },
        {
            "Metric": "Output Scope",
            "Value": update_note,
        },
    ]

    return pd.DataFrame(rows)


def build_feature_dictionary():
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
# MAIN
# =========================================================

def build_football_features():
    ensure_directories()

    master_df = safe_read_excel(
        MASTER_ALL_FILE,
        "Football_Master"
    )

    if master_df.empty:
        print("No football master data found.")
        return pd.DataFrame()

    master_df = add_missing_columns(
        master_df,
        BASE_REQUIRED_COLUMNS
    )

    master_df["MatchDate"] = pd.to_datetime(
        master_df["MatchDate"],
        errors="coerce"
    )

    for col in NUMERIC_COLUMNS:
        master_df = safe_numeric(
            master_df,
            col
        )

    master_df = master_df[
        master_df["MatchDate"].notna()
    ].copy()

    master_df = master_df.sort_values(
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
        ]
    ).reset_index(drop=True)

    team_long = build_team_match_long(
        master_df
    )

    team_features = add_rolling_features(
        team_long
    )

    team_features = add_home_away_rolling_features(
        team_features
    )

    match_features = build_match_features(
        master_df,
        team_features
    )

    tier1_match = match_features[
        match_features["Tier"] == "Tier 1 - Elite Europe"
    ].copy()

    tier2_match = match_features[
        match_features["Tier"] == "Tier 2 - Europe Depth"
    ].copy()

    tier3_match = match_features[
        match_features["Tier"] == "Tier 3 - Global"
    ].copy()

    tier1_team = team_features[
        team_features["Tier"] == "Tier 1 - Elite Europe"
    ].copy()

    tier2_team = team_features[
        team_features["Tier"] == "Tier 2 - Europe Depth"
    ].copy()

    tier3_team = team_features[
        team_features["Tier"] == "Tier 3 - Global"
    ].copy()

    export_feature_workbook(
        output_file=OUTPUT_ALL_FILE,
        match_features=match_features,
        team_features=team_features,
        update_note="All UKDATA27 leagues"
    )

    export_feature_workbook(
        output_file=OUTPUT_TIER1_FILE,
        match_features=tier1_match,
        team_features=tier1_team,
        update_note="Tier 1 - Elite Europe"
    )

    export_feature_workbook(
        output_file=OUTPUT_TIER2_FILE,
        match_features=tier2_match,
        team_features=tier2_team,
        update_note="Tier 2 - Europe Depth"
    )

    export_feature_workbook(
        output_file=OUTPUT_TIER3_FILE,
        match_features=tier3_match,
        team_features=tier3_team,
        update_note="Tier 3 - Global"
    )

    print("\n======================================")
    print("UKDATA27 FOOTBALL FEATURES EXPORTED")
    print("======================================")
    print(f"All rows : {len(match_features)}")
    print(f"Tier 1   : {len(tier1_match)} rows")
    print(f"Tier 2   : {len(tier2_match)} rows")
    print(f"Tier 3   : {len(tier3_match)} rows")
    print(f"All file : {OUTPUT_ALL_FILE}")
    print(f"Tier 1   : {OUTPUT_TIER1_FILE}")
    print(f"Tier 2   : {OUTPUT_TIER2_FILE}")
    print(f"Tier 3   : {OUTPUT_TIER3_FILE}")
    print("======================================\n")

    return match_features


# =========================================================
# CLI
# =========================================================

def main():
    build_football_features()


if __name__ == "__main__":
    main()