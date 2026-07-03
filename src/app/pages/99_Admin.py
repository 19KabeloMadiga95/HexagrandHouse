from pathlib import Path
import sys
PROJECT_ROOT=Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0,str(PROJECT_ROOT))
import pandas as pd
import streamlit as st
from src.app.utils.page import configure_page, refresh_chip
from src.app.components.premium import compact_header,kpi_grid,section_title,lottery_card,football_card

from src.services.admin_service import get_admin_dashboard_data
configure_page("Admin","⚙️")
@st.cache_data(ttl=300)
def load_data(): return get_admin_dashboard_data()
d=load_data(); k=d.get('kpis',{}); platform=d.get('platform',{}); refresh_chip(value=k.get('last_refresh'))
compact_header("Admin console","Platform operations.","Database health, service checks and environment metadata in one compact operating view.",tags=[f"Database: {k.get('database','-')}",f"Services: {k.get('services','-')}"],metrics=[{"label":"Rows","value":f"{k.get('total_rows',0):,}","note":"warehouse"},{"label":"DB size","value":platform.get('database_size_mb','-'),"note":"MB"},{"label":"Tables","value":platform.get('table_count','-'),"note":"SQLite"},{"label":"Refresh","value":k.get('last_refresh','-'),"note":"marker"}])
c1,c2=st.columns([1,1])
with c1: section_title("Services","🧩"); st.dataframe(pd.DataFrame(d.get('services',[])),use_container_width=True,height=340); section_title("Database","▦"); st.dataframe(platform.get('database_summary',pd.DataFrame()),use_container_width=True,height=280)
with c2: section_title("Environment","🧰"); env=pd.DataFrame([{"Setting":a,"Value":b} for a,b in d.get('environment',{}).items()]); st.dataframe(env,use_container_width=True,height=340); st.markdown(f'<div class="hgh-panel"><div class="hgh-panel-title">Database file</div><p class="hgh-panel-sub">{platform.get("database_file","-")}</p></div>',unsafe_allow_html=True)
