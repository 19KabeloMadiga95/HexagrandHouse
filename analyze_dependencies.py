from pathlib import Path
import ast
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "dependency_graph.xlsx"


def safe_read(path):
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def get_imports(file_path):
    text = safe_read(file_path)

    try:
        tree = ast.parse(text)
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


def is_entry_point(file_path):
    text = safe_read(file_path)

    return 'if __name__ == "__main__"' in text


def main():
    files = []

    for file_path in SRC_DIR.rglob("*.py"):
        if "__pycache__" in file_path.parts:
            continue

        rel = file_path.relative_to(PROJECT_ROOT)

        files.append({
            "FilePath": str(rel),
            "FileName": file_path.name,
            "Folder": str(file_path.parent.relative_to(PROJECT_ROOT)),
            "Imports": get_imports(file_path),
            "IsEntryPoint": is_entry_point(file_path),
            "LineCount": len(safe_read(file_path).splitlines()),
        })

    df = pd.DataFrame(files)

    edges = []

    for _, row in df.iterrows():
        for imported in row["Imports"]:
            edges.append({
                "SourceFile": row["FilePath"],
                "ImportedModule": imported,
            })

    edges_df = pd.DataFrame(edges)

    entry_points_df = df[df["IsEntryPoint"] == True].copy()

    import_text = edges_df["ImportedModule"].astype(str).str.cat(sep="|") if not edges_df.empty else ""

    df["LikelyUnused"] = df.apply(
        lambda row: (
            not row["IsEntryPoint"]
            and row["FileName"].replace(".py", "") not in import_text
        ),
        axis=1
    )

    likely_unused_df = df[df["LikelyUnused"] == True].copy()

    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df.drop(columns=["Imports"]).to_excel(writer, sheet_name="Files", index=False)
        edges_df.to_excel(writer, sheet_name="Import_Edges", index=False)
        entry_points_df.drop(columns=["Imports"]).to_excel(writer, sheet_name="Entry_Points", index=False)
        likely_unused_df.drop(columns=["Imports"]).to_excel(writer, sheet_name="Likely_Unused", index=False)

    print("Dependency graph created:")
    print(OUTPUT_FILE)


if __name__ == "__main__":
    main()