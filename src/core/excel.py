from pathlib import Path
import pandas as pd

from src.core.logging import warning, info


def list_excel_sheets(path: Path) -> list[str]:
    try:
        if not path.exists():
            return []

        excel_file = pd.ExcelFile(path, engine="openpyxl")
        return excel_file.sheet_names

    except Exception as exc:
        warning(f"Could not list sheets for {path}: {exc}")
        return []


def read_excel_preferred(
    file_path,
    sheet_names,
    warn_if_missing: bool = True,
):
    """
    Read the first available worksheet from an Excel file.

    Parameters
    ----------
    file_path : Path
    sheet_names : list[str]
        Ordered list of preferred sheet names.
    warn_if_missing : bool
        If False, missing files quietly return an empty DataFrame.
    """

    import pandas as pd

    from src.core.logging import info, warning

    if not file_path.exists():

        if warn_if_missing:
            warning(f"Missing file: {file_path}")

        return pd.DataFrame()

    workbook = pd.ExcelFile(
        file_path,
        engine="openpyxl",
    )

    for sheet in sheet_names:

        if sheet in workbook.sheet_names:

            info(
                f"Reading {file_path.name} | Sheet: {sheet}"
            )

            return pd.read_excel(
                workbook,
                sheet_name=sheet,
            )

    info(
        f"Reading {file_path.name} | Sheet: {workbook.sheet_names[0]}"
    )

    return pd.read_excel(
        workbook,
        sheet_name=workbook.sheet_names[0],
    )


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    df.columns = [
        str(col)
        .strip()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace("(", "")
        .replace(")", "")
        .replace(".", "_")
        .replace("%", "Pct")
        for col in df.columns
    ]

    return df


def normalise_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    for col in df.columns:
        col_lower = col.lower()

        if (
            "date" in col_lower
            or "generatedat" in col_lower
            or "backtestedat" in col_lower
            or "updatedat" in col_lower
            or "loadedat" in col_lower
        ):
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce").astype(str)
            except Exception:
                pass

    return df