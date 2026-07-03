from pathlib import Path
import sys
PROJECT_ROOT=Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0,str(PROJECT_ROOT))
import pandas as pd
import streamlit as st
from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header,kpi_grid,section_title,lottery_card,football_card

from src.services.accuracy_service import get_accuracy_dashboard_data
configure_page("Model Accuracy","🎯")
@st.cache_data(ttl=300)
def load_data(): return get_accuracy_dashboard_data()
d=load_data(); k=d.get('kpis',{}); refresh_chip()
compact_header("Model accuracy","Performance tracking room.","Monitor scoring, historical hits and model signal quality in a compact control view.",tags=["Evidence over hype"],metrics=[{"label":"Scored","value":k.get('fixtures_scored',0),"note":"fixtures"},{"label":"Result","value":k.get('result_accuracy','-'),"note":"accuracy"},{"label":"Goals","value":k.get('goals_accuracy','-'),"note":"accuracy"},{"label":"Corners","value":k.get('corners_accuracy','-'),"note":"accuracy"}])
kpi_grid([{"title":"Fixtures scored","value":k.get('fixtures_scored',0),"sub":"backtest rows","icon":"◎"},{"title":"Result accuracy","value":k.get('result_accuracy','-'),"sub":"hit rate","icon":"🎯"},{"title":"Goals accuracy","value":k.get('goals_accuracy','-'),"sub":"hit rate","icon":"⚽"},{"title":"Corners accuracy","value":k.get('corners_accuracy','-'),"sub":"hit rate","icon":"▦"}])
for name,val in d.items():
 if isinstance(val,pd.DataFrame) and not val.empty: section_title(name.replace('_',' ').title(),"▦"); st.dataframe(val.head(100),use_container_width=True,height=340)
