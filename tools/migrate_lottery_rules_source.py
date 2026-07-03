from pathlib import Path
from datetime import datetime
import shutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

CORE_RULES = SRC_DIR / "core" / "rules" / "lottery_rules.py"
LOTTERY_RULES = SRC_DIR / "lottery" / "config" / "lottery_game_rules.py"

ARCHIVE_DIR = PROJECT_ROOT / "_archive" / f"lottery_rules_migration_{datetime.now():%Y%m%d_%H%M%S}"

REPLACEMENTS = {
    "from src.core.rules.lottery_rules import": "from src.lottery.config.lottery_game_rules import",
    "import src.core.rules.lottery_rules": "import src.lottery.config.lottery_game_rules",
}


def replace_imports():
    changed = []

    for file in SRC_DIR.rglob("*.py"):
        text = file.read_text(encoding="utf-8", errors="ignore")
        new_text = text

        for old, new in REPLACEMENTS.items():
            new_text = new_text.replace(old, new)

        if new_text != text:
            file.write_text(new_text, encoding="utf-8")
            changed.append(file.relative_to(PROJECT_ROOT))

    return changed


def archive_core_rules():
    if not CORE_RULES.exists():
        print("[OK] Core lottery rules already removed.")
        return

    destination = ARCHIVE_DIR / CORE_RULES.relative_to(PROJECT_ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)

    shutil.move(str(CORE_RULES), str(destination))
    print(f"[ARCHIVED] {CORE_RULES.relative_to(PROJECT_ROOT)}")


def main():
    print("======================================")
    print("LOTTERY RULES SOURCE MIGRATION")
    print("======================================")

    if not LOTTERY_RULES.exists():
        raise FileNotFoundError(f"Missing required rules file: {LOTTERY_RULES}")

    changed = replace_imports()

    for file in changed:
        print(f"[UPDATED IMPORT] {file}")

    archive_core_rules()

    print("======================================")
    print(f"Files updated: {len(changed)}")
    print("Authoritative rules file:")
    print(LOTTERY_RULES.relative_to(PROJECT_ROOT))
    print("======================================")


if __name__ == "__main__":
    main()