from pathlib import Path
import ast
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "project_structure_inventory.xlsx"


def get_imports(file_path):
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return sorted(set(imports))


def classify_file(path):
    text = str(path).lower()

    if "frontend" in text or "streamlit" in text or "pages" in text:
        return "Frontend"
    if "database" in text or "query" in text or "db" in text:
        return "Database"
    if "football" in text:
        return "Football"
    if "lottery" in text or "lotto" in text or "powerball" in text or "uk49" in text:
        return "Lottery"
    if "automation" in text or "daily" in text:
        return "Automation"
    if "api" in text:
        return "API"
    if "common" in text or "config" in text:
        return "Core"

    return "Unclassified"


def main():
    rows = []

    for file_path in SRC_DIR.rglob("*.py"):
        if "__pycache__" in file_path.parts:
            continue

        rel_path = file_path.relative_to(PROJECT_ROOT)

        rows.append({
            "FilePath": str(rel_path),
            "FileName": file_path.name,
            "Folder": str(file_path.parent.relative_to(PROJECT_ROOT)),
            "Category": classify_file(file_path),
            "LineCount": len(file_path.read_text(encoding="utf-8", errors="ignore").splitlines()),
            "Imports": ", ".join(get_imports(file_path)),
        })

    df = pd.DataFrame(rows)

    summary = (
        df.groupby("Category")
        .agg(
            FileCount=("FilePath", "count"),
            TotalLines=("LineCount", "sum")
        )
        .reset_index()
        .sort_values("FileCount", ascending=False)
    )

    duplicates = (
        df.groupby("FileName")
        .filter(lambda x: len(x) > 1)
        .sort_values("FileName")
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="All_Files", index=False)
        summary.to_excel(writer, sheet_name="Summary", index=False)
        duplicates.to_excel(writer, sheet_name="Duplicate_Names", index=False)

    print("Project structure inventory created:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()