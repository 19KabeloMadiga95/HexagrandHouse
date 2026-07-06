from __future__ import annotations

from src.lottery.models.sqlite_prediction_engine import export_prediction_group


def export_uk49s_predictions(update_combined_table: bool = True):
    return export_prediction_group("uk49s", update_combined_table=update_combined_table)


def main():
    export_uk49s_predictions(update_combined_table=True)


if __name__ == "__main__":
    main()
