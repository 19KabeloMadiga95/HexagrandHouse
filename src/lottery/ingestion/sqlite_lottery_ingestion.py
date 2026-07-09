from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import sqlite3
import traceback
from typing import Callable, Any

import pandas as pd

from src.core.paths import DATABASE_FILE, ensure_parent_directory


# =========================================================
# SQLITE LOTTERY HISTORY INGESTION
# =========================================================

LOTTERY_HISTORY_TABLE = "lottery_history"
LOTTERY_INGESTION_LOG_TABLE = "lottery_ingestion_log"
SOURCE_NAME = "za.national-lottery.com"

HISTORICAL_COLUMNS = [
    "GameFamily",
    "GameName",
    "DrawType",
    "DrawNumber",
    "DrawDate",
    "DrawDay",
    "N1",
    "N2",
    "N3",
    "N4",
    "N5",
    "N6",
    "Bonus",
    "Jackpot",
    "Outcome",
    "SourceName",
    "SourceUrl",
    "LoadedAt",
    "RecordKey",
]

NUMBER_COLUMNS = ["N1", "N2", "N3", "N4", "N5", "N6", "Bonus"]


@dataclass
class IngestionSource:
    name: str
    function: Callable[..., list[dict]]
    kwargs: dict[str, Any]
    required: bool = True


def current_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _connect() -> sqlite3.Connection:
    ensure_parent_directory(DATABASE_FILE)
    return sqlite3.connect(DATABASE_FILE)


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _read_table(conn: sqlite3.Connection, table_name: str) -> pd.DataFrame:
    if not _table_exists(conn, table_name):
        return pd.DataFrame(columns=HISTORICAL_COLUMNS)

    return pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)


def _normalise_date(value) -> str | None:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.strftime("%Y-%m-%d 00:00:00")


def _draw_day(value) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return ""
    return parsed.day_name()


def _normalise_number(value):
    if value is None or pd.isna(value) or value == "":
        return None
    try:
        return int(value)
    except Exception:
        return None


def _normalise_text(value) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _build_record_key(row: pd.Series | dict) -> str:
    def get(name: str):
        if isinstance(row, dict):
            return row.get(name)
        return row.get(name)

    draw_date = pd.to_datetime(get("DrawDate"), errors="coerce")
    draw_date_key = "" if pd.isna(draw_date) else draw_date.strftime("%Y-%m-%d")

    parts = [
        _normalise_text(get("GameFamily")),
        _normalise_text(get("GameName")),
        _normalise_text(get("DrawType")),
        draw_date_key,
        _normalise_text(_normalise_number(get("N1"))),
        _normalise_text(_normalise_number(get("N2"))),
        _normalise_text(_normalise_number(get("N3"))),
        _normalise_text(_normalise_number(get("N4"))),
        _normalise_text(_normalise_number(get("N5"))),
        _normalise_text(_normalise_number(get("N6"))),
        _normalise_text(_normalise_number(get("Bonus"))),
    ]

    return "|".join(parts)


def _standardise_history(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=HISTORICAL_COLUMNS)

    out = df.copy()

    for col in HISTORICAL_COLUMNS:
        if col not in out.columns:
            out[col] = None

    out = out[HISTORICAL_COLUMNS].copy()

    out["DrawDate"] = out["DrawDate"].apply(_normalise_date)
    out["DrawDay"] = out["DrawDate"].apply(_draw_day)

    for col in NUMBER_COLUMNS:
        out[col] = out[col].apply(_normalise_number)

    for col in ["GameFamily", "GameName", "DrawType", "DrawNumber", "Outcome", "SourceName", "SourceUrl", "LoadedAt"]:
        out[col] = out[col].apply(_normalise_text)

    if "Jackpot" in out.columns:
        out["Jackpot"] = pd.to_numeric(out["Jackpot"], errors="coerce")

    missing_loaded = out["LoadedAt"].eq("") | out["LoadedAt"].isna()
    out.loc[missing_loaded, "LoadedAt"] = current_timestamp()

    missing_key = out["RecordKey"].isna() | out["RecordKey"].astype(str).str.strip().eq("")
    if missing_key.any():
        out.loc[missing_key, "RecordKey"] = out[missing_key].apply(_build_record_key, axis=1)

    out = out.dropna(subset=["DrawDate", "N1", "N2", "N3", "N4", "N5"])

    return out


def _latest_lottery_year(conn: sqlite3.Connection) -> int:
    if not _table_exists(conn, LOTTERY_HISTORY_TABLE):
        return datetime.now().year

    row = conn.execute(f'SELECT MAX(DrawDate) FROM "{LOTTERY_HISTORY_TABLE}"').fetchone()
    latest = row[0] if row else None
    parsed = pd.to_datetime(latest, errors="coerce")

    if pd.isna(parsed):
        return datetime.now().year

    # Re-read the previous year too. It protects us around year-end and late source updates.
    return max(int(parsed.year) - 1, 2000)


def _build_sources(start_year: int, end_year: int) -> list[IngestionSource]:
    from src.lottery.scrapers.powerball_scraper import scrape_powerball_history
    from src.lottery.scrapers.lotto_scraper import scrape_lotto_history
    from src.lottery.scrapers.daily_lotto_scraper import scrape_daily_lotto_history
    from src.lottery.scrapers.uk49s_scraper import scrape_uk49s_history

    return [
        IngestionSource(
            name="PowerBall",
            function=scrape_powerball_history,
            kwargs={"start_year": start_year, "end_year": end_year},
            required=False,
        ),
        IngestionSource(
            name="Lotto",
            function=scrape_lotto_history,
            kwargs={"start_year": start_year, "end_year": end_year},
            required=False,
        ),
        IngestionSource(
            name="Daily Lotto",
            function=scrape_daily_lotto_history,
            kwargs={"start_year": start_year, "end_year": end_year},
            required=False,
        ),
        IngestionSource(
            name="UK49s",
            function=scrape_uk49s_history,
            kwargs={},
            required=False,
        ),
    ]


def _write_history(conn: sqlite3.Connection, history_df: pd.DataFrame) -> None:
    history_df.to_sql(LOTTERY_HISTORY_TABLE, conn, if_exists="replace", index=False)

    conn.execute(
        f'CREATE INDEX IF NOT EXISTS idx_{LOTTERY_HISTORY_TABLE}_recordkey '
        f'ON "{LOTTERY_HISTORY_TABLE}" ("RecordKey")'
    )
    conn.execute(
        f'CREATE INDEX IF NOT EXISTS idx_{LOTTERY_HISTORY_TABLE}_drawdate '
        f'ON "{LOTTERY_HISTORY_TABLE}" ("DrawDate")'
    )
    conn.execute(
        f'CREATE INDEX IF NOT EXISTS idx_{LOTTERY_HISTORY_TABLE}_game '
        f'ON "{LOTTERY_HISTORY_TABLE}" ("GameFamily", "GameName", "DrawType")'
    )


def _write_ingestion_log(conn: sqlite3.Connection, log_rows: list[dict]) -> None:
    if not log_rows:
        return

    log_df = pd.DataFrame(log_rows)
    log_df.to_sql(LOTTERY_INGESTION_LOG_TABLE, conn, if_exists="append", index=False)

    conn.execute(
        f'CREATE INDEX IF NOT EXISTS idx_{LOTTERY_INGESTION_LOG_TABLE}_run '
        f'ON "{LOTTERY_INGESTION_LOG_TABLE}" ("RunID", "SourceName", "Status")'
    )


def update_lottery_history_sqlite(
    start_year: int | None = None,
    end_year: int | None = None,
) -> dict:
    """
    Fetch latest lottery history from web sources and upsert it into SQLite.

    This is the missing daily-refresh layer. The model cycle can only update its
    predictions if lottery_history has first been refreshed with new draws.
    """

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    end_year = end_year or datetime.now().year

    conn = _connect()
    existing = _standardise_history(_read_table(conn, LOTTERY_HISTORY_TABLE))

    if start_year is None:
        start_year = _latest_lottery_year(conn)

    print("\n======================================")
    print("HEXAGRANDHOUSE LOTTERY HISTORY INGESTION")
    print("SQLite-first runtime mode")
    print("======================================")
    print(f"Run ID    : {run_id}")
    print(f"Start year: {start_year}")
    print(f"End year  : {end_year}")
    print(f"Existing  : {len(existing)} rows")
    print("======================================\n")

    all_new_frames: list[pd.DataFrame] = []
    log_rows: list[dict] = []

    for source in _build_sources(start_year=start_year, end_year=end_year):
        print("\n--------------------------------------")
        print(f"FETCHING: {source.name}")
        print("--------------------------------------")

        started_at = current_timestamp()

        try:
            rows = source.function(**source.kwargs)
            new_df = _standardise_history(pd.DataFrame(rows))

            all_new_frames.append(new_df)

            latest = new_df["DrawDate"].max() if not new_df.empty else None
            print(f"Fetched rows: {len(new_df)}")
            print(f"Latest draw : {latest}")

            log_rows.append(
                {
                    "RunID": run_id,
                    "SourceName": source.name,
                    "Status": "Success",
                    "StartedAt": started_at,
                    "FinishedAt": current_timestamp(),
                    "RowsFetched": len(new_df),
                    "LatestDrawDate": latest,
                    "ErrorMessage": "",
                }
            )

        except Exception as exc:
            print(f"FAILED: {source.name}: {exc}")
            print(traceback.format_exc())

            log_rows.append(
                {
                    "RunID": run_id,
                    "SourceName": source.name,
                    "Status": "Failed",
                    "StartedAt": started_at,
                    "FinishedAt": current_timestamp(),
                    "RowsFetched": 0,
                    "LatestDrawDate": None,
                    "ErrorMessage": str(exc),
                }
            )

            if source.required:
                _write_ingestion_log(conn, log_rows)
                conn.commit()
                conn.close()
                raise

    fetched = pd.concat(all_new_frames, ignore_index=True) if all_new_frames else pd.DataFrame(columns=HISTORICAL_COLUMNS)
    fetched = _standardise_history(fetched)

    before_rows = len(existing)

    combined = pd.concat([existing, fetched], ignore_index=True)
    combined = _standardise_history(combined)
    combined = combined.drop_duplicates(subset=["RecordKey"], keep="last")
    combined = combined.sort_values(
        by=["DrawDate", "GameFamily", "GameName", "DrawType"],
        ascending=[False, True, True, True],
    ).reset_index(drop=True)

    after_rows = len(combined)
    added_rows = max(after_rows - before_rows, 0)
    skipped_rows = max(len(fetched) - added_rows, 0)
    latest_after = combined["DrawDate"].max() if not combined.empty else None

    _write_history(conn, combined)
    _write_ingestion_log(conn, log_rows)
    conn.commit()
    conn.close()

    print("\n======================================")
    print("LOTTERY HISTORY INGESTION COMPLETE")
    print("======================================")
    print(f"Fetched rows : {len(fetched)}")
    print(f"Added rows   : {added_rows}")
    print(f"Skipped rows : {skipped_rows}")
    print(f"Total rows   : {after_rows}")
    print(f"Latest draw  : {latest_after}")
    print("======================================\n")

    return {
        "RunID": run_id,
        "RowsFetched": int(len(fetched)),
        "RowsAdded": int(added_rows),
        "RowsSkipped": int(skipped_rows),
        "RowsTotal": int(after_rows),
        "LatestDrawDate": latest_after,
        "Status": "Success",
    }


def main() -> dict:
    return update_lottery_history_sqlite()


if __name__ == "__main__":
    main()
