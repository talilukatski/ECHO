import streamlit as st
from dotenv import load_dotenv

from src.ui.views import (
    initialize_session_state,
    inject_global_css,
    render_creation_modal,
    render_sidebar_drafts
)

load_dotenv()

st.set_page_config(
    page_title="ECHO - Choose Start",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

initialize_session_state()
inject_global_css()

# Sidebar drafts נשארים זמינים גם פה
render_sidebar_drafts()

render_creation_modal()
