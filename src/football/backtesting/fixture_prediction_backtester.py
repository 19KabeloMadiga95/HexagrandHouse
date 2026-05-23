from pathlib import Path
from datetime import datetime

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[3]

MASTER_DIR = BASE_DIR / "data" / "football" / "master"
BACKTEST_DIR = BASE_DIR / "data" / "football" / "exports" / "backtesting"

ARCHIVE_FILE = BACKTEST_DIR / "prediction_snapshot_archive.csv"
MASTER_RESULTS_FILE = MASTER_DIR / "football_master_all_leagues.xlsx"

OUTPUT_EXCEL = BACKTEST_DIR / "football_fixture_backtest_history.xlsx"
OUTPUT_CSV = BACKTEST_DIR / "football_fixture_backtest_history.csv"


def ensure_directories():
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)


def safe_read_excel(path, sheet_name=0):
    try:
        if not path.exists():
            return pd.DataFrame()

        return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")

    except Exception:
        return pd.DataFrame()


def safe_read_csv(path):
    try:
        if not path.exists():
            return pd.DataFrame()

        return pd.read_csv(path, low_memory=False)

    except Exception:
        return pd.DataFrame()


def clean_text(value):
    if pd.isna(value):
        return ""

    return str(value).strip().lower()


def clean_league(value):
    if pd.isna(value):
        return ""

    return str(value).strip().upper()


def build_fixture_datetime(df):
    df = df.copy()

    if "FixtureDate" not in df.columns:
        df["FixtureDateTime"] = pd.NaT
        return df

    if "KickoffTime" not in df.columns:
        df["KickoffTime"] = "12:00"

    df["FixtureDateTime"] = pd.to_datetime(
        df["FixtureDate"].astype(str)
        + " "
        + df["KickoffTime"].fillna("12:00").astype(str),
        errors="coerce"
    )

    return df


def build_prediction_match_key(df):
    df = df.copy()

    fixture_date = pd.to_datetime(
        df["FixtureDate"],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    df["MatchKey"] = (
        df["LeagueCode"].apply(clean_league)
        + "_"
        + fixture_date.fillna("")
        + "_"
        + df["HomeTeam"].apply(clean_text)
        + "_"
        + df["AwayTeam"].apply(clean_text)
    )

    return df


def build_results_match_key(df):
    df = df.copy()

    date_col = None

    for col in ["MatchDate", "Date", "FixtureDate"]:
        if col in df.columns:
            date_col = col
            break

    if date_col is None:
        df["MatchKey"] = None
        return df

    fixture_date = pd.to_datetime(
        df[date_col],
        errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    df["MatchKey"] = (
        df["LeagueCode"].apply(clean_league)
        + "_"
        + fixture_date.fillna("")
        + "_"
        + df["HomeTeam"].apply(clean_text)
        + "_"
        + df["AwayTeam"].apply(clean_text)
    )

    return df


def get_home_goals(row):
    for col in ["HomeGoals", "FTHG", "HG"]:
        if col in row.index and pd.notna(row.get(col)):
            try:
                return int(float(row.get(col)))
            except Exception:
                pass

    return None


def get_away_goals(row):
    for col in ["AwayGoals", "FTAG", "AG"]:
        if col in row.index and pd.notna(row.get(col)):
            try:
                return int(float(row.get(col)))
            except Exception:
                pass

    return None


def get_actual_result(row):
    existing_label = row.get("ResultLabel", None)

    if pd.notna(existing_label):
        label = str(existing_label).strip()

        if label in ["Home Win", "Away Win", "Draw"]:
            return label

    home_goals = get_home_goals(row)
    away_goals = get_away_goals(row)

    if home_goals is None or away_goals is None:
        return None

    if home_goals > away_goals:
        return "Home Win"

    if away_goals > home_goals:
        return "Away Win"

    return "Draw"


def get_total_goals(row):
    if "TotalGoals" in row.index and pd.notna(row.get("TotalGoals")):
        try:
            return int(float(row.get("TotalGoals")))
        except Exception:
            pass

    home_goals = get_home_goals(row)
    away_goals = get_away_goals(row)

    if home_goals is None or away_goals is None:
        return None

    return home_goals + away_goals


def get_total_corners(row):
    if "TotalCorners" in row.index and pd.notna(row.get("TotalCorners")):
        try:
            return int(float(row.get("TotalCorners")))
        except Exception:
            pass

    possible_pairs = [
        ("HomeCorners", "AwayCorners"),
        ("HC", "AC"),
    ]

    for home_col, away_col in possible_pairs:
        if home_col in row.index and away_col in row.index:
            try:
                home_corners = row.get(home_col)
                away_corners = row.get(away_col)

                if pd.notna(home_corners) and pd.notna(away_corners):
                    return int(float(home_corners)) + int(float(away_corners))
            except Exception:
                pass

    return None


def score_goals_pick(best_goals_pick, total_goals):
    if pd.isna(best_goals_pick) or total_goals is None:
        return None

    pick = str(best_goals_pick)

    if "Over 1.5" in pick:
        return int(total_goals > 1.5)

    if "Over 2.5" in pick:
        return int(total_goals > 2.5)

    if "Over 3.5" in pick:
        return int(total_goals > 3.5)

    return None


def score_corners_pick(best_corners_pick, total_corners):
    if pd.isna(best_corners_pick) or total_corners is None:
        return None

    pick = str(best_corners_pick)

    if "Over 7.5" in pick:
        return int(total_corners > 7.5)

    if "Over 8.5" in pick:
        return int(total_corners > 8.5)

    if "Over 9.5" in pick:
        return int(total_corners > 9.5)

    if "Over 10.5" in pick:
        return int(total_corners > 10.5)

    return None


def build_backtest_rows(predictions_df, results_df):
    predictions = predictions_df.copy()
    results = results_df.copy()

    predictions = build_fixture_datetime(predictions)

    now = pd.Timestamp.now()

    predictions = predictions[
        predictions["FixtureDateTime"].notna()
        & (predictions["FixtureDateTime"] < now)
    ].copy()

    if predictions.empty:
        return pd.DataFrame()

    predictions = build_prediction_match_key(predictions)
    results = build_results_match_key(results)

    results["ActualResult"] = results.apply(get_actual_result, axis=1)
    results["ActualTotalGoals"] = results.apply(get_total_goals, axis=1)
    results["ActualTotalCorners"] = results.apply(get_total_corners, axis=1)

    results["ActualHomeGoals"] = results.apply(get_home_goals, axis=1)
    results["ActualAwayGoals"] = results.apply(get_away_goals, axis=1)

    results = results[
        results["ActualResult"].notna()
    ].copy()

    merge_cols = [
        "MatchKey",
        "ActualResult",
        "ActualTotalGoals",
        "ActualTotalCorners",
        "ActualHomeGoals",
        "ActualAwayGoals",
    ]

    merge_cols = [
        col for col in merge_cols
        if col in results.columns
    ]

    scored = predictions.merge(
        results[merge_cols],
        on="MatchKey",
        how="left"
    )

    scored = scored[
        scored["ActualResult"].notna()
    ].copy()

    if scored.empty:
        return pd.DataFrame()

    scored["ResultHit"] = (
        scored["PredictedResult"].astype(str)
        == scored["ActualResult"].astype(str)
    ).astype(int)

    scored["GoalsHit"] = scored.apply(
        lambda row: score_goals_pick(
            row.get("BestGoalsPick"),
            row.get("ActualTotalGoals")
        ),
        axis=1
    )

    scored["CornersHit"] = scored.apply(
        lambda row: score_corners_pick(
            row.get("BestCornersPick"),
            row.get("ActualTotalCorners")
        ),
        axis=1
    )

    scored["BacktestedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return scored


def remove_duplicates(df):
    if df.empty:
        return df

    key_cols = [
        col for col in [
            "MatchKey",
            "SnapshotDate",
        ]
        if col in df.columns
    ]

    if not key_cols:
        return df.drop_duplicates().reset_index(drop=True)

    return (
        df
        .drop_duplicates(
            subset=key_cols,
            keep="last"
        )
        .reset_index(drop=True)
    )


def build_summary(df):
    if df.empty:
        return pd.DataFrame([
            {
                "Metric": "Backtested Fixtures",
                "Value": 0,
            }
        ])

    return pd.DataFrame([
        {
            "Metric": "Backtested Fixtures",
            "Value": len(df),
        },
        {
            "Metric": "Result Accuracy",
            "Value": round(
                pd.to_numeric(df["ResultHit"], errors="coerce").mean(),
                3
            ),
        },
        {
            "Metric": "Goals Accuracy",
            "Value": round(
                pd.to_numeric(df["GoalsHit"], errors="coerce").mean(),
                3
            ),
        },
        {
            "Metric": "Corners Accuracy",
            "Value": round(
                pd.to_numeric(df["CornersHit"], errors="coerce").mean(),
                3
            ),
        },
        {
            "Metric": "Generated At",
            "Value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    ])


def build_league_summary(df):
    if df.empty or "League" not in df.columns:
        return pd.DataFrame()

    summary = (
        df
        .groupby(
            [
                "Country",
                "League",
            ],
            dropna=False
        )
        .agg(
            BacktestedFixtures=("League", "count"),
            ResultAccuracy=("ResultHit", "mean"),
            GoalsAccuracy=("GoalsHit", "mean"),
            CornersAccuracy=("CornersHit", "mean"),
        )
        .reset_index()
    )

    for col in [
        "ResultAccuracy",
        "GoalsAccuracy",
        "CornersAccuracy",
    ]:
        summary[col] = summary[col].round(3)

    return summary


def build_grade_summary(df):
    if df.empty or "BettingGrade" not in df.columns:
        return pd.DataFrame()

    summary = (
        df
        .groupby("BettingGrade", dropna=False)
        .agg(
            BacktestedFixtures=("BettingGrade", "count"),
            ResultAccuracy=("ResultHit", "mean"),
            GoalsAccuracy=("GoalsHit", "mean"),
            CornersAccuracy=("CornersHit", "mean"),
        )
        .reset_index()
    )

    for col in [
        "ResultAccuracy",
        "GoalsAccuracy",
        "CornersAccuracy",
    ]:
        summary[col] = summary[col].round(3)

    return summary


def export_fixture_prediction_backtest():
    ensure_directories()

    predictions_df = safe_read_csv(ARCHIVE_FILE)

    results_df = safe_read_excel(
        MASTER_RESULTS_FILE,
        "Football_Master"
    )

    if results_df.empty:
        results_df = safe_read_excel(MASTER_RESULTS_FILE)

    if predictions_df.empty:
        print("No archived predictions found.")
        return pd.DataFrame()

    if results_df.empty:
        print("No historical football results found.")
        return pd.DataFrame()

    backtest_df = build_backtest_rows(
        predictions_df,
        results_df
    )

    backtest_df = remove_duplicates(backtest_df)

    summary_df = build_summary(backtest_df)
    league_summary_df = build_league_summary(backtest_df)
    grade_summary_df = build_grade_summary(backtest_df)

    backtest_df.to_csv(
        OUTPUT_CSV,
        index=False
    )

    with pd.ExcelWriter(
        OUTPUT_EXCEL,
        engine="openpyxl",
        mode="w"
    ) as writer:
        backtest_df.to_excel(
            writer,
            sheet_name="Backtest_History",
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

        grade_summary_df.to_excel(
            writer,
            sheet_name="Grade_Summary",
            index=False
        )

    print("\n======================================")
    print("FOOTBALL BACKTEST COMPLETE")
    print("======================================")
    print(f"Fixtures scored : {len(backtest_df)}")
    print(f"Output Excel    : {OUTPUT_EXCEL}")
    print(f"Output CSV      : {OUTPUT_CSV}")
    print("======================================\n")

    return backtest_df


def main():
    export_fixture_prediction_backtest()


if __name__ == "__main__":
    main()