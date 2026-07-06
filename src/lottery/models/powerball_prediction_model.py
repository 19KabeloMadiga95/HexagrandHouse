from __future__ import annotations

from src.lottery.models.sqlite_prediction_engine import export_prediction_group


def export_powerball_predictions(update_combined_table: bool = True):
    return export_prediction_group("powerball", update_combined_table=update_combined_table)


def main():
    export_powerball_predictions(update_combined_table=True)


if __name__ == "__main__":
    main()
