from pathlib import Path
import sys
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.app.utils.page import configure_page

configure_page("HexaGrandBet", "◆")
st.switch_page("pages/1_Home.py")
