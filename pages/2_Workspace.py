import streamlit as st
from dotenv import load_dotenv

from src.ui.views import (
    initialize_session_state,
    inject_global_css,
    render_sidebar_drafts,
    render_top_bar,
    render_main_workspace
)

load_dotenv()

st.set_page_config(
    page_title="ECHO - Workspace",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

initialize_session_state()
inject_global_css()

# אם אין שיר פעיל → חזרה לבחירה
if st.session_state.current_song is None:
    st.switch_page("pages/1_Choose_Start.py")

render_sidebar_drafts()
render_main_workspace()
