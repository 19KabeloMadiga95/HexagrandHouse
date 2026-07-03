from __future__ import annotations

from src.services.results.dashboard import get_results_dashboard_data
from src.services.results.filtering import (
    filter_lottery_game,
    filter_football_league,
)
from src.services.results.analytics import (
    get_lottery_volume,
    get_football_result_distribution,
)
from src.services.results.formatting import (
    safe_text,
    safe_number,
    format_date,
    format_short_date,
    format_currency,
)