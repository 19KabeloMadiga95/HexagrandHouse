from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent

INPUT_FILE = PROJECT_ROOT / "docs" / "project_structure_inventory.xlsx"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "hexagrandhouse_architecture_blueprint.xlsx"


ARCHITECTURE_MAP = {
    "Frontend": "src/app",
    "Database": "src/data",
    "Core": "src/core",
    "Automation": "src/automation",
    "Football": "src/football",
    "Lottery": "src/lottery",
    "API": "src/api",
    "Unclassified": "_archive/legacy_scripts",
}


def recommend_action(row):
    path = str(row["FilePath"]).lower()
    name = str(row["FileName"]).lower()
    lines = int(row["LineCount"])

    if "__init__.py" in name:
        return "Keep"

    if "test" in name or "debug" in name or "backup" in name:
        return "Archive"

    if "old" in name or "legacy" in name or "copy" in name:
        return "Archive"

    if lines < 20 and row["Category"] == "Core":
        return "Review"

    if row["Category"] in ["Frontend", "Database", "Automation"]:
        return "Keep"

    if row["Category"] in ["Lottery", "Football"]:
        if "pipeline" in name or "daily" in name:
            return "Keep"
        if "model" in name or "prediction" in name or "feature" in name:
            return "Merge"
        if "report" in name or "export" in name:
            return "Review"
        return "Review"

    return "Review"


def recommend_target(row):
    category = row["Category"]
    base = ARCHITECTURE_MAP.get(category, "_archive/legacy_scripts")

    name = row["FileName"]

    if category == "Lottery":
        if "feature" in name.lower():
            return "src/lottery/features"
        if "model" in name.lower() or "prediction" in name.lower():
            return "src/lottery/models"
        if "optimizer" in name.lower() or "optimization" in str(row["FilePath"]).lower():
            return "src/lottery/optimization"
        if "pipeline" in name.lower() or "daily" in name.lower():
            return "src/lottery/pipeline.py"
        return "src/lottery/_review"

    if category == "Football":
        if "fixture" in name.lower():
            return "src/football/fixtures.py"
        if "feature" in name.lower():
            return "src/football/features"
        if "model" in name.lower() or "prediction" in name.lower():
            return "src/football/models"
        if "pipeline" in name.lower() or "daily" in name.lower():
            return "src/football/pipeline.py"
        return "src/football/_review"

    return base


def main():
    df = pd.read_excel(INPUT_FILE, sheet_name="All_Files")

    df["RecommendedAction"] = df.apply(recommend_action, axis=1)
    df["RecommendedTarget"] = df.apply(recommend_target, axis=1)

    summary = (
        df.groupby(["Category", "RecommendedAction"])
        .agg(
            FileCount=("FilePath", "count"),
            TotalLines=("LineCount", "sum"),
        )
        .reset_index()
        .sort_values(["Category", "RecommendedAction"])
    )

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Migration_Blueprint", index=False)
        summary.to_excel(writer, sheet_name="Action_Summary", index=False)

    print("Blueprint created:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()