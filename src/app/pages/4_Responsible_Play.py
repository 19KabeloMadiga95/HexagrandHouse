from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
import streamlit as st
from src.app.utils.page import configure_page
configure_page("Responsible Play", "🛡️")
st.info("Responsible play guidance has moved to Settings.")
st.page_link("pages/5_Settings.py", label="Open Settings", icon="⚙")
