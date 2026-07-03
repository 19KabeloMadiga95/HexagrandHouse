from pathlib import Path
import sys
PROJECT_ROOT=Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0,str(PROJECT_ROOT))
import pandas as pd
import streamlit as st
from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header,kpi_grid,section_title,lottery_card,football_card

configure_page("Responsible Play","🛡️"); refresh_chip()
compact_header("Responsible intelligence","Play smart. Stay in control.","HexagrandHouse is an analytics and entertainment platform, not a guarantee engine. Use signals as information, not certainty.",tags=["No certainty","Budget first","Entertainment only"],metrics=[{"label":"Rule 1","value":"Limit","note":"budget"},{"label":"Rule 2","value":"Stop","note":"never chase"},{"label":"Rule 3","value":"Review","note":"behaviour"},{"label":"Rule 4","value":"Balance","note":"life first"}])
st.markdown('<div class="hgh-grid-3"><div class="hgh-panel"><div class="hgh-panel-title">Set a hard limit</div><p class="hgh-panel-sub">Only use money already allocated for entertainment.</p></div><div class="hgh-panel"><div class="hgh-panel-title">Predictions are not promises</div><p class="hgh-panel-sub">Random systems remain random. A good signal can still lose.</p></div><div class="hgh-panel"><div class="hgh-panel-title">No chasing</div><p class="hgh-panel-sub">Never increase stakes to recover losses.</p></div></div>',unsafe_allow_html=True)
section_title("Platform stance","🛡️"); st.info("HexagrandHouse should support better decisions, not unhealthy behaviour. Keep it recreational, controlled and optional.")
