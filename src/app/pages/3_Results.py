from pathlib import Path
import sys
PROJECT_ROOT=Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0,str(PROJECT_ROOT))
import pandas as pd
import streamlit as st
from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header,kpi_grid,section_title,lottery_card,football_card

from src.services.results_service import get_results_dashboard_data
configure_page("Results Centre","📊")
@st.cache_data(ttl=300)
def load_data(): return get_results_dashboard_data(days=14)
d=load_data(); k=d.get('kpis',{}); refresh_chip()
compact_header("Results centre","Latest outcomes and scoring.","Review lottery results, football outcomes and scoring summaries from the latest loaded data.",tags=["14-day window"],metrics=[{"label":"Lottery","value":k.get('lottery_results',0),"note":"recent"},{"label":"Football","value":k.get('football_results',0),"note":"matches"},{"label":"Scored","value":k.get('scored_predictions',0),"note":"predictions"},{"label":"Accuracy","value":k.get('result_accuracy','-'),"note":"hit rate"}])
c1,c2=st.columns(2)
with c1: section_title("Lottery results","🎲"); ldf=d.get('lottery_results_df',d.get('lottery_df',pd.DataFrame())); st.dataframe(ldf.head(100),use_container_width=True,height=520)
with c2: section_title("Football results","⚽"); fdf=d.get('football_results_df',d.get('football_df',pd.DataFrame())); st.dataframe(fdf.head(100),use_container_width=True,height=520)
