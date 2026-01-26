"""
ECHO - Landing Page
"""

import streamlit as st
from dotenv import load_dotenv

from src.ui.views import (
    initialize_session_state,
    inject_global_css,
    render_landing_page,
    render_sidebar_drafts,   # ✅ add
)

load_dotenv()

st.set_page_config(
    page_title="ECHO",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

initialize_session_state()
inject_global_css()

render_sidebar_drafts()      # ✅ add (draw drafts in sidebar)

render_landing_page()

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
