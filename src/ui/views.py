import streamlit as st
import html
import streamlit.components.v1 as components
import re

from src.utils.context_builder import build_song_snapshot
from src.config.settings import (
    COLORS, MODE_LYRICS, MODE_MELODY, DEFAULT_MODE,
    DEFAULT_SONG_TITLE, BUTTON_STYLES
)
from src.models.song import Song
from src.agents.lyrics_agent import LyricsAgent
from src.agents.melody_agent import MelodyAgent
from src.ui.genre_tiles import render_genre_tiles
from src.storage.drafts_store import load_drafts, dict_to_song, save_draft, delete_draft, next_draft_title
from src.services import music_generator
from src.agents.knowledge_base import retrieve_rules, format_rules_for_prompt


def inject_global_css():
    st.markdown(f"""
    <style>
      /* =========================
         THEME VARS (single source of truth)
         ========================= */
      :root {{
        --bg: {COLORS['background']};
        --card: {COLORS['card']};
        --borders: {COLORS['borders']};
        --text: {COLORS['primary_text']};
        --muted: {COLORS['secondary_text']};

        /* lyrics */
        --lyrics-text: {COLORS['lyrics_text_c']};
        --lyrics-num: {COLORS['secondary_text']};
      }}

      /* =========================
         BASE / BACKGROUND / TEXT
         ========================= */
      .main, .stApp {{
        background-color: var(--bg) !important;
      }}

      div[data-testid="stSidebarNav"] {{
        display: none !important;
      }}

      html, body, .stApp, .main, [data-testid="stAppViewContainer"] {{
        color: var(--text) !important;
      }}

      /* ✅ panel headings: keep */
      .panel-box h1, .panel-box h2, .panel-box h3 {{
        color: var(--text) !important;
      }}

      /* ✅ IMPORTANT FIX:
         do NOT force color on every span (it kills special titles like Echo)
         keep paragraphs only */
      .panel-box .stMarkdown p {{
        color: var(--text) !important;
      }}

      /* =========================
         LYRICS TYPOGRAPHY (FIX)
         ========================= */
      .lyricsbox .line {{
        display: flex !important;
        align-items: baseline !important;
        gap: 6px !important;
        margin: 0 !important;
        padding: 2px 6px !important;
      }}

      .lyricsbox .ln {{
        color: var(--lyrics-num) !important;
        font-weight: 400 !important;
        min-width: 4px !important;
        width: 5px !important;
        flex: 0 0 15px !important;
        text-align: right !important;
        font-size: 13px !important;
      }}

      .lyricsbox .lyric-txt {{
        color: var(--lyrics-text) !important;
        flex: 1 1 auto !important;
        font-weight: 550 !important;
        font-size: 16px !important;
        line-height: 1.2 !important;
        font-family: Arial, Helvetica, sans-serif !important;
      }}

      /* =========================
         IMPORTANT: FIX STREAMLIT DEFAULT SPACING (NO :has)
         ========================= */
      div[data-testid="stMarkdownContainer"] {{
        margin: 0 !important;
        padding: 0 !important;
      }}
      div[data-testid="stMarkdownContainer"] > * {{
        margin-top: 0 !important;
        margin-bottom: 0 !important;
      }}

      div[data-testid="stVerticalBlock"] {{
        gap: 12px !important;
      }}
      div[data-testid="stVerticalBlock"] > div {{
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
      }}

      div[data-testid="stForm"],
      div[data-testid="stForm"] > div {{
        margin: 0 !important;
        padding: 0 !important;
      }}

      /* =========================
         PANEL BOX
         ========================= */
      .panel-box {{
        background: var(--card) !important;
        border-radius: 7px !important;
        border: 2px solid var(--borders) !important;
        padding: 14px !important;
      }}

      /* =========================
         INPUTS: ALWAYS WHITE, NO BORDER
         ========================= */
      div[data-testid="stTextInput"] [data-baseweb="input"] > div {{
        background: #FFFFFF !important;
        border: 0 !important;
        box-shadow: none !important;
        border-radius: 12px !important;
      }}

      div[data-testid="stTextInput"] input,
      div[data-testid="stTextInput"] input:focus,
      div[data-testid="stTextInput"] input:active {{
        background: #FFFFFF !important;
        color: #333333 !important;
        border: 0 !important;
        box-shadow: none !important;
        outline: none !important;
      }}

      div[data-testid="stTextInput"] input::placeholder {{
        color: var(--muted) !important;
      }}

      div[data-testid="stTextArea"] [data-baseweb="textarea"] > div {{
        background: #FFFFFF !important;
        border: 0 !important;
        box-shadow: none !important;
        border-radius: 12px !important;
      }}

      div[data-testid="stTextArea"] textarea,
      div[data-testid="stTextArea"] textarea:focus,
      div[data-testid="stTextArea"] textarea:active {{
        background: #FFFFFF !important;
        color: #333333 !important;
        border: 0 !important;
        box-shadow: none !important;
        outline: none !important;
      }}

      div[data-testid="stTextArea"] textarea::placeholder {{
        color: var(--muted) !important;
      }}

      div[data-testid="stTextArea"] textarea {{
        resize: none !important;
      }}

      /* =========================
         REMOVE "FORM CARD" AROUND GROUPS
         ========================= */
      div[data-testid="stForm"],
      div[data-testid="stForm"] > div {{
        background: transparent !important;
        border: 0 !important;
        box-shadow: none !important;
      }}

      /* =========================
         BUTTON RESET
         ========================= */
      div.stButton button,
      div[data-testid="stFormSubmitButton"] button {{
        border-width: 2px !important;
        border-style: solid !important;
        border-color: var(--borders) !important;
        border-radius: 12px !important;
        min-height: 48px !important;
        height: auto !important;
        padding: 10px 12px !important;
        font-size: 17px !important;
        font-weight: 800 !important;
        outline: none !important;
        box-shadow: none !important;
        background-clip: padding-box !important;
      }}

      div.stButton button:focus,
      div.stButton button:focus-visible,
      div.stButton button:active,
      div[data-testid="stFormSubmitButton"] button:focus,
      div[data-testid="stFormSubmitButton"] button:focus-visible,
      div[data-testid="stFormSubmitButton"] button:active {{
        outline: none !important;
        box-shadow: none !important;
      }}

      /* =========================
         MELODY GENERATE STATES
         ========================= */
      .melody-generate.empty button {{
        background: #E5E7EB !important;
        border-color: #E5E7EB !important;
        color: #6B728E !important;
        cursor: not-allowed !important;
        box-shadow: none !important;
      }}

      .melody-generate.full button {{
        background: #6B728E !important;
        border-color: #6B728E !important;
        color: #6B728E !important;
      }}

      .melody-generate.full button:hover {{
        filter: brightness(0.95) !important;
      }}

      /* =========================
         LYRICS SELECTED LINE
         ========================= */
      .line.selected {{
        background: rgba(239, 68, 68, 0.10) !important;
        border-radius: 10px !important;
      }}

      /* =========================
         LYRICS SCROLL
         ========================= */
      .lyricsbox {{
        scrollbar-gutter: stable;
        scrollbar-width: auto;
        scrollbar-color: rgba(0,0,0,0.45) rgba(0,0,0,0.08);
      }}

      .lyricsbox::-webkit-scrollbar {{ width: 12px; }}
      .lyricsbox::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.06); border-radius: 999px; }}
      .lyricsbox::-webkit-scrollbar-thumb {{
        background: rgba(0,0,0,0.35);
        border-radius: 999px;
        border: 3px solid rgba(0,0,0,0.06);
      }}
      .lyricsbox::-webkit-scrollbar-thumb:hover {{ background: rgba(0,0,0,0.55); }}

      /* =========================
         CHAT CSS (GLOBAL)
         ========================= */
      .chatbox {{
        height: 453px;
        overflow-y: auto;
        padding: 10px;
        background: var(--bg);
        border-radius: 12px;
        margin: 0 !important;
        border: 2px solid var(--borders);
        scrollbar-gutter: stable;

        scrollbar-width: auto;
        scrollbar-color: rgba(0,0,0,0.45) rgba(0,0,0,0.08);
      }}

      .chatbox::-webkit-scrollbar {{ width: 12px; }}
      .chatbox::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.06); border-radius: 999px; }}
      .chatbox::-webkit-scrollbar-thumb {{
        background: rgba(0,0,0,0.35);
        border-radius: 999px;
        border: 3px solid rgba(0,0,0,0.06);
      }}
      .chatbox::-webkit-scrollbar-thumb:hover {{ background: rgba(0,0,0,0.55); }}

      .chatbox .msg {{
        display: block;
        margin: 10px 0;
        padding: 8px 12px;
        border-radius: 14px;
        max-width: 85%;
        white-space: pre-wrap;
        word-break: break-word;
        line-height: 1.5;
        font-size: 16px;

        border: 2px solid rgba(0,0,0,0.18);
        background: rgba(255,255,255,0.92);
        color: #111 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.06);
      }}

      .chatbox .msg.user {{
        margin-left: auto;
        margin-right: 1px !important;
        background: rgba(59, 130, 246, 0.14) !important;
        border-color: rgba(59, 130, 246, 0.35) !important;
        color: #1F2A44 !important;
      }}

      .chatbox .msg.assistant {{
        margin-right: auto;
        margin-left: 1px;
        border-color: rgba(255, 209, 102, 0.75) !important;
        background: rgba(255, 209, 102, 0.28) !important;
        color: #111 !important;
      }}

      .emptyhint {{
        opacity: 0.7 !important;
        font-style: italic !important;
        color: #4B5563 !important;
      }}

      /* ===== tiles caption (optional) ===== */
      .tiles-caption{{
          margin: 0 0 6px 0 !important;
          color: var(--text) !important;
          font-weight: 700 !important;
          letter-spacing: 0.08em !important;
          text-transform: uppercase !important;
          font-size: 0.85rem !important;
      }}

      /* =========================
         ✅ GENRE TILES ROOT (MAIN + SUB)
         ========================= */
      .genre-tiles-root div.stButton > button:not(.play-btn) {{
        height: 64px !important;
        font-size: 14px !important;
        min-height: 64px !important;
        width: 100% !important;
        padding: 2px 4px !important;
        border-radius: 18px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        overflow: hidden !important;
      }}

      .genre-tiles-root div.stButton > button:not(.play-btn) p,
      .genre-tiles-root div.stButton > button:not(.play-btn) span {{
        margin: 0 !important;
        text-align: center !important;
        line-height: 1.1 !important;
        font-size: 13px !important;

        display: -webkit-box !important;
        -webkit-line-clamp: 2 !important;
        -webkit-box-orient: vertical !important;
        overflow: hidden !important;
      }}

      .genre-tiles-root div.stButton > button.play-btn {{
        height: 36px !important;
        min-height: 36px !important;
        padding: 0 !important;
        border-radius: 12px !important;
      }}
      
            /* =========================
         PLAY BUTTON (main + sub)
         ========================= */
      .genre-tiles-root div.stButton > button.play-btn {{
        background: var(--lyrics-text) !important;   /* primary blue */
        border-color: var(--lyrics-text) !important;
        color: #ffffff !important;
        font-weight: 900 !important;
      }}

      .genre-tiles-root div.stButton > button.play-btn:hover {{
        filter: brightness(0.95) !important;
      }}

      .genre-tiles-root div.stButton > button.play-btn:disabled {{
        background: rgba(59, 130, 246, 0.25) !important;
        border-color: rgba(59, 130, 246, 0.25) !important;
        color: rgba(255,255,255,0.9) !important;
        cursor: not-allowed !important;
        filter: none !important;
      }}


      /* =========================
         ✅ IMPORTANT: hide ONLY the genre JS custom component
         (fix: first click doesn't work)
         ========================= */
      .genre-js-marker + div[data-testid="stCustomComponent"] {{
        height: 0 !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
        pointer-events: none !important;
      }}

      .genre-js-marker + div[data-testid="stCustomComponent"] iframe {{
        height: 0 !important;
        min-height: 0 !important;
        display: none !important;
        pointer-events: none !important;
      }}

      /* =========================
         LANDING TYPOGRAPHY
         ========================= */
      /* טקסט ההנחיה - נשאר קטן ועדין */
      .landing-hint {{
        color: var(--muted) !important;
        font-size: 1rem !important;
        margin-top: 2rem !important;
        font-style: italic !important;
        opacity: 0.7 !important;
        font-family: Arial, Helvetica, sans-serif !important;
      }}
      
      .landing-subtitle {{
        color: #0B1F3B !important;
        font-size: 20px !important; 
        max-width: 300px !important;
        line-height: 1.2 !important;
        font-weight: 600 !important;
        font-family: Arial, Helvetica, sans-serif !important;
      }}

      .echo-title {{
        font-family: Arial, Helvetica, sans-serif !important;
        font-size: 140px !important; 
        font-weight: 900 !important;
        color: #0B1F3B !important;
        margin: 0 !important;
        line-height: 0.8 !important;
        letter-spacing: -0.02em !important;
      }}

    </style>
    """, unsafe_allow_html=True)


def panel_title(text: str):
    st.markdown(
        f"""
        <div style="
            font-size:0.85rem;
            font-weight:700;
            letter-spacing:0.12em;
            color:{COLORS['secondary_text']} !important;
            margin-bottom:12px;
            text-transform:uppercase;
        ">{html.escape(text)}</div>
        """,
        unsafe_allow_html=True
    )


def main_title(text: str, align: str = "left"):
    st.markdown(
        f"""
        <div style="
            font-size:1.6rem;   /* 👈 היה לך בערך ככה קודם */
            font-weight:800;
            color:{COLORS['primary_text']};
            line-height:1.1;
            margin:0 0 8px 0;
            text-align:{align};
        ">{html.escape(text)}</div>
        """,
        unsafe_allow_html=True
    )


def initialize_session_state():
    """Initialize all session state variables."""
    if "current_mode" not in st.session_state:
        st.session_state.current_mode = DEFAULT_MODE

    if "current_song" not in st.session_state:
        st.session_state.current_song = None

    if "show_creation_modal" not in st.session_state:
        st.session_state.show_creation_modal = False

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "selected_line_index" not in st.session_state:
        st.session_state.selected_line_index = None

    if "line_replacement_text" not in st.session_state:
        st.session_state.line_replacement_text = None

    if "waiting_for_line_replacement" not in st.session_state:
        st.session_state.waiting_for_line_replacement = False

    if "show_genre_tiles" not in st.session_state:
        st.session_state.show_genre_tiles = False

    if "melody_mode_entered" not in st.session_state:
        st.session_state.melody_mode_entered = False

    if "selected_genre" not in st.session_state:
        st.session_state.selected_genre = None

    if "selected_sub_genre" not in st.session_state:
        st.session_state.selected_sub_genre = None

    if "show_finish_modal" not in st.session_state:
        st.session_state.show_finish_modal = False

    if "mode_greeted_once" not in st.session_state:
        st.session_state.mode_greeted_once = False

    if "melody_genre_hint_sent" not in st.session_state:
        st.session_state.melody_genre_hint_sent = False

    if "last_genre_applied" not in st.session_state:
        st.session_state.last_genre_applied = None

    if "current_draft_id" not in st.session_state:
        st.session_state.current_draft_id = None

    # Initialize AI agents
    if "lyrics_agent" not in st.session_state:
        try:
            st.session_state.lyrics_agent = LyricsAgent()
        except Exception as e:
            st.session_state.lyrics_agent = None
            st.error(f"Failed to initialize AI agent: {str(e)}")

    if "melody_agent" not in st.session_state:
        try:
            st.session_state.melody_agent = MelodyAgent()
        except Exception as e:
            st.session_state.melody_agent = None
            st.error(f"Failed to initialize AI agent: {str(e)}")


def render_top_bar(display_text=None):
    """Render the top bar showing current mode or custom text."""
    if display_text is None:
        display_text = st.session_state.current_mode
    mode_color = COLORS["primary_blue"]

    st.markdown(f"""
        <div style="background-color: {mode_color}; padding: 1rem; margin-bottom: 1rem; border-radius: 8px;">
            <h2 style="color: white; margin: 0; text-align: center;">{display_text}</h2>
        </div>
    """, unsafe_allow_html=True)


def render_landing_page():
    """Landing page UI (no song yet)."""
    import os

    col_left, col_right = st.columns([1.3, 0.7])

    # Left: Image (נשארת גדולה כפי שביקשת)
    with col_left:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.abspath(os.path.join(base_dir, "..", ".."))
        image_paths = [
            os.path.join(base_dir, "assets", "images", "echo_logo.png"),
            os.path.join(base_dir, "assets", "images", "echo_logo.jpg")
        ]
        for img_path in image_paths:
            if os.path.exists(img_path):
                st.image(img_path, use_container_width=True)
                break

    # Right: Text
    with col_right:
        st.markdown("<div class='landing-right'>", unsafe_allow_html=True)
        st.markdown("<div style='height:320px'></div>", unsafe_allow_html=True)
        st.markdown("<div class='echo-title'>ECHO</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)

        st.markdown(
            "<p class='landing-subtitle'>Start your creative journey by writing lyrics and shaping a song with AI.</p>",
            unsafe_allow_html=True
        )

        st.markdown(
            "<p class='landing-hint'>Click on top left arrows to add new one</p>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)


def render_creation_modal():
    """The 'choose direction' step (topic/mood/title)."""
    TITLE_A = "#0B1F3B"
    QUESTIONS = "#B8922E"

    question_style = f"""
        font-size:20px; 
        font-weight:400; 
        margin-bottom:20px; 
        font-family: Arial, Helvetica, sans-serif !important;
        color: {QUESTIONS};
    """

    with st.container():
        st.markdown(f"""
            <div style="
                text-align:center; 
                color:{TITLE_A}; 
                margin-bottom:2.8rem; 
                font-size:3.6rem; 
                font-weight:800;
                font-family: Arial, Helvetica, sans-serif !important;
                letter-spacing: -0.5px;
            ">
                Give Your Song Its Voice:
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

        st.markdown(f'<p style="{question_style}">1. What is the spark behind this song?</p>', unsafe_allow_html=True)
        topic = st.text_input("topic", key="ideation_topic", placeholder="A memory that won't fade, a secret kept, or a story only you can tell...", label_visibility="collapsed")
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        st.markdown(f'<p style="{question_style}">2. How should the atmosphere feel?</p>', unsafe_allow_html=True)
        mood = st.text_input("mood", key="ideation_mood", placeholder="Electric and raw, a quiet midnight, or the chaos of a summer morning...", label_visibility="collapsed")
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        st.markdown(f'<p style="{question_style}">3. What is the name of your masterpiece?</p>', unsafe_allow_html=True)
        song_title = st.text_input("title", key="ideation_title", placeholder="Silence the 'Untitled'. A great title is the first note of a hit.", label_visibility="collapsed")
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # כפתור אחד בצד ימין (בערך רבע עמוד)
        sp1, sp2, sp3, btn_col = st.columns([1, 1, 1, 1])

        with btn_col:
            if st.button("Let's Make Music", use_container_width=True):
                if topic.strip() and mood.strip():
                    title = (song_title or "").strip()
                    if not title:
                        title = next_draft_title("Draft")

                    new_song = Song(
                        title=title,
                        intent=f"Topic: {topic}\nMood: {mood}"
                    )

                    st.session_state.current_draft_id = None
                    st.session_state.current_song = new_song
                    st.session_state.show_creation_modal = False
                    st.switch_page("pages/2_Workspace.py")
                else:
                    st.warning("Please answer the first two questions.")


def render_main_workspace():
    # 3 columns: lyrics (thin), melody (small), chat (wide)
    col_lyrics, col_melody, col_chat = st.columns([1.2, 0.9, 1.9], gap="large")

    with col_lyrics:
        render_lyrics_panel()

    with col_melody:
        render_melody_panel()

    with col_chat:
        render_chat_panel_header()
        render_chat()


def render_chat_panel_header():
    mode_label = st.session_state.get("current_mode", MODE_LYRICS)

    st.markdown(f"""
    <div class="main-header compact chat-header">
      <div class="title" style="font-size:1.30rem; font-weight:750;">AI ASSISTANT</div>
      <div class="mode-label">
        {html.escape(mode_label)}
      </div>
    </div>

    <style>
      .chat-header {{
        display: flex;
        align-items: flex-end;
        justify-content: flex-start;  /* 👈 לא space-between */
        gap: 14px;                   /* 👈 מרחק קטן בין הכותרת ל-label */
      }}
      .chat-header .mode-label {{
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.10em;
        color: {COLORS['secondary_text']} !important;
        text-transform: uppercase;
      }}
    </style>
    """, unsafe_allow_html=True)


def render_lyrics_panel():
    song = st.session_state.current_song

    # local UI states
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False
    if "editing_line_index" not in st.session_state:
        st.session_state.editing_line_index = None

    # ✅ confirms
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = False
    if "confirm_delete_idx" not in st.session_state:
        st.session_state.confirm_delete_idx = None

    if "confirm_save" not in st.session_state:
        st.session_state.confirm_save = False
    if "confirm_save_idx" not in st.session_state:
        st.session_state.confirm_save_idx = None

    # -------- Header --------
    # -------- Header row: title + save button on the same line --------
    hcol, bcol = st.columns([0.85, 0.15], vertical_alignment="center")

    with hcol:
        st.markdown(f"""
        <div class='main-header compact'>
          <div class='title' style='font-size:1.30rem; font-weight:750;'>{html.escape(song.title)}</div>
          <div class="mode-label-under">LYRICS</div>
        </div>

        <style>
          .mode-label-under {{
            font-size: 0.85rem;
            font-weight: 700;
            letter-spacing: 0.10em;
            color: {COLORS['secondary_text']} !important;
            text-transform: uppercase;
          }}
        </style>
        """, unsafe_allow_html=True)

    with bcol:
        if st.button("💾", key="save_draft_btn_small", help="Save Draft", use_container_width=True):
            draft_id = st.session_state.get("current_draft_id")
            st.session_state.current_draft_id = save_draft(song, draft_id)
            st.toast("Saved!")
            st.rerun()

    # -------- Lyrics list box --------
    if not song.lyrics:
        lyrics_text = """<div class="emptyhint">Start writing your song…</div>"""
    else:
        selected_idx = st.session_state.get("editing_line_index")
        if selected_idx is None:
            selected_idx = st.session_state.get("selected_line_index")

        safe_lines = []
        for i, l in enumerate(song.lyrics):
            cls = "line selected" if selected_idx == i else "line"
            safe_lines.append(
                f"<div class='{cls}'><span class='ln'>{i + 1}:</span><span class='lyric-txt'>{html.escape(l)}</span></div>"
            )
        lyrics_text = "".join(safe_lines)

    st.markdown(
        f"<div class='panel-box lyricsbox' style='height:430px; overflow-y:auto; white-space:pre-wrap; line-height:1.65;'>{lyrics_text}</div>",
        unsafe_allow_html=True
    )

    # -------- Add line + Edit toggle (only when not editing) --------
    if (st.session_state.get("editing_line_index") is None) and (not st.session_state.get("edit_mode", False)):
        with st.form("add_line_form", clear_on_submit=True):
            new_line = st.text_input(
                "Add a new line",
                key="new_lyric_text",
                placeholder="Type a lyric line...",
                label_visibility="collapsed",
            )

            b_add, b_edit = st.columns([0.78, 0.22], vertical_alignment="center")
            with b_add:
                add_submitted = st.form_submit_button("Add Line", use_container_width=True, key="btn_add_line")
            with b_edit:
                edit_clicked = st.form_submit_button(
                    "Edit",
                    use_container_width=True,
                    key="btn_edit",
                    disabled=(not song.lyrics)
                )

        if add_submitted:
            if new_line and new_line.strip():
                song.add_lyric_line(new_line.strip())
            st.rerun()

        if edit_clicked:
            # reset confirms
            st.session_state.confirm_delete = False
            st.session_state.confirm_delete_idx = None
            st.session_state.confirm_save = False
            st.session_state.confirm_save_idx = None

            st.session_state.edit_mode = True
            st.rerun()

    # -------- Choose which line to edit (only when edit_mode=True) --------
    if st.session_state.edit_mode:
        if not song.lyrics:
            st.info("No lines to edit yet.")
        else:
            line_numbers = [f"Line {i + 1}" for i in range(len(song.lyrics))]

            chosen = st.selectbox(
                "Choose a line",
                options=line_numbers,
                label_visibility="collapsed",
                key="edit_pick_line",
            )
            idx = line_numbers.index(chosen)

            # if changed selection, close confirm delete
            if st.session_state.get("confirm_delete_idx") is not None and st.session_state.confirm_delete_idx != idx:
                st.session_state.confirm_delete = False
                st.session_state.confirm_delete_idx = None

            # confirm delete UI
            if st.session_state.get("confirm_delete") and st.session_state.get("confirm_delete_idx") == idx:
                st.markdown("<small style='opacity:0.65;'>Are you sure you want to delete this line?</small>",
                            unsafe_allow_html=True)

                c_no, c_yes = st.columns(2)
                with c_no:
                    if st.button("No", use_container_width=True, key="confirm_delete_no"):
                        st.session_state.confirm_delete = False
                        st.session_state.confirm_delete_idx = None
                        st.session_state.selected_line_index = None
                        st.rerun()

                with c_yes:
                    if st.button("Yes", use_container_width=True, key="confirm_delete_yes"):
                        if 0 <= idx < len(song.lyrics):
                            if hasattr(song, "delete_lyric_line"):
                                song.delete_lyric_line(idx)
                            else:
                                song.lyrics.pop(idx)

                        # reset states
                        st.session_state.selected_line_index = None
                        st.session_state.editing_line_index = None
                        st.session_state.edit_mode = False

                        st.session_state.confirm_delete = False
                        st.session_state.confirm_delete_idx = None

                        st.rerun()

            else:
                col3, col2, col1 = st.columns(3)

                with col3:
                    if st.button("Cancel", use_container_width=True, key="cancel_edit_btn"):
                        st.session_state.confirm_delete = False
                        st.session_state.confirm_delete_idx = None
                        st.session_state.selected_line_index = None
                        st.session_state.edit_mode = False
                        st.rerun()

                with col2:
                    if st.button("Delete line", use_container_width=True, key="delete_line_btn"):
                        st.session_state.selected_line_index = idx
                        st.session_state.confirm_delete = True
                        st.session_state.confirm_delete_idx = idx
                        st.rerun()

                with col1:
                    if st.button("Edit line", use_container_width=True, key="start_edit_btn"):
                        # reset confirms
                        st.session_state.confirm_delete = False
                        st.session_state.confirm_delete_idx = None
                        st.session_state.confirm_save = False
                        st.session_state.confirm_save_idx = None

                        st.session_state.selected_line_index = idx
                        st.session_state.editing_line_index = idx
                        st.session_state.edit_mode = False

                        line_text = song.lyrics[idx] if 0 <= idx < len(song.lyrics) else ""
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": (
                                f"Okay — you want to change line {idx + 1}:\n"
                                f"“{line_text}”\n"
                                f"What vibe/meaning do you want instead?"
                            )
                        })
                        st.session_state.scroll_chat_to_bottom = True
                        st.rerun()

    # -------- Actual editing UI (with confirm-save) --------
    if st.session_state.editing_line_index is not None:
        idx = st.session_state.editing_line_index

        # guard
        if not song.lyrics or idx < 0 or idx >= len(song.lyrics):
            st.session_state.editing_line_index = None
            st.rerun()
            return

        # if we somehow switched index, close confirm save
        if st.session_state.get("confirm_save_idx") is not None and st.session_state.confirm_save_idx != idx:
            st.session_state.confirm_save = False
            st.session_state.confirm_save_idx = None

        current_text = song.lyrics[idx]
        edit_key = f"edit_line_text_{idx}"
        if edit_key not in st.session_state:
            st.session_state[edit_key] = current_text

        with st.form(f"edit_line_form_{idx}", clear_on_submit=False):
            st.text_input(
                "Edit line",
                key=edit_key,
                label_visibility="collapsed",
                placeholder="What do you want it to be?"
            )

            if st.session_state.get("confirm_save") and st.session_state.get("confirm_save_idx") == idx:
                st.markdown("<small style='opacity:0.65;'>Are you sure?</small>", unsafe_allow_html=True)
                c2, c1 = st.columns(2)
                with c2:
                    no_save = st.form_submit_button("No", use_container_width=True, key=f"no_save_{idx}")
                with c1:
                    yes_save = st.form_submit_button("Yes, save", use_container_width=True, key=f"yes_save_{idx}")
                save = False
                cancel = False
            else:
                c2, c1 = st.columns(2)
                with c2:
                    cancel = st.form_submit_button("Cancel", use_container_width=True, key=f"cancel_{idx}")
                with c1:
                    save = st.form_submit_button("Save", use_container_width=True, key=f"save_{idx}")
                yes_save = False
                no_save = False

        # first Save (or Enter) -> open confirm
        if save:
            st.session_state.confirm_save = True
            st.session_state.confirm_save_idx = idx
            st.rerun()

        # confirm yes -> actually save
        if yes_save:
            new_text = (st.session_state[edit_key] or "").strip()
            if new_text:
                song.replace_lyric_line(idx, new_text)

            st.session_state.confirm_save = False
            st.session_state.confirm_save_idx = None

            st.session_state.editing_line_index = None
            st.session_state.selected_line_index = None
            st.session_state.edit_mode = False

            if edit_key in st.session_state:
                del st.session_state[edit_key]
            st.rerun()

        # confirm cancel -> close confirm
        if no_save:
            st.session_state.confirm_save = False
            st.session_state.confirm_save_idx = None
            st.rerun()

        # cancel editing -> exit
        if cancel:
            st.session_state.confirm_save = False
            st.session_state.confirm_save_idx = None

            st.session_state.editing_line_index = None
            st.session_state.selected_line_index = None
            st.session_state.edit_mode = False

            if edit_key in st.session_state:
                del st.session_state[edit_key]
            st.rerun()


def _apply_genre_to_melody_text(song, genre, sub_genre):
    if not song or not genre or not sub_genre:
        return

    block = f"Style: {genre}\nSubstyle: {sub_genre}\nAdd extra notes about vibe, tempo, and instruments"
    current = (song.melody_description or "").strip()

    lines = current.splitlines()
    if len(lines) >= 2 and lines[0].startswith("Style:") and lines[1].startswith("Substyle:"):
        rest = "\n".join(lines[2:]).lstrip()
        new_text = (block + ("\n" + rest if rest else "")).strip()
    else:
        new_text = (block + ("\n\n" + current if current else "")).strip()

    song.melody_description = new_text
    st.session_state.melody_desc_needs_sync = True


def _push_genre_summary_to_chat(song):
    """Send a single assistant message after genre+subgenre were chosen (once per selection)."""
    genre = getattr(song, "genre", None) if song else None
    sub = getattr(song, "sub_genre", None) if song else None
    if not genre or not sub:
        return

    last_sent = st.session_state.get("last_genre_prompt_sent")  # tuple or None
    cur = (genre, sub)
    if last_sent == cur:
        return  # already sent for this selection

    st.session_state["last_genre_prompt_sent"] = cur

    msg = (
        f"Nice — you picked **{genre} / {sub}**.\n"
        "Quick direction question:\n"
        "• What vibe do you want (happy/dark/nostalgic)?\n"
        "• Tempo/BPM range?\n"
        "• Main instruments (e.g., piano, sax, drums)?\n"
        "Answer in 1–2 lines and I’ll shape a melody prompt."
    )
    st.session_state.chat_history.append({"role": "assistant", "content": msg})
    st.session_state.scroll_chat_to_bottom = True


def render_melody_panel():
    song = st.session_state.current_song

    st.markdown("""
      <div class='main-header compact'>
        <div class='title' style='font-size:1.30rem; font-weight:750;'>MELODY</div>
      </div>
    """, unsafe_allow_html=True)

    # ---- init helper state ----
    if "last_genre_applied" not in st.session_state:
        st.session_state.last_genre_applied = None
    if "melody_desc_needs_sync" not in st.session_state:
        st.session_state.melody_desc_needs_sync = False

    # --- sync BEFORE widget is created ---
    if "melody_description_input" not in st.session_state:
        st.session_state["melody_description_input"] = song.melody_description or ""

    if st.session_state.get("melody_desc_needs_sync", False):
        st.session_state["melody_description_input"] = song.melody_description or ""
        st.session_state.melody_desc_needs_sync = False

    # ✅ TEXTAREA תמיד מיד אחרי הכותרת -> מרווח קבוע
    melody_desc = st.text_area(
        "Melody description",
        key="melody_description_input",
        height=200,
        label_visibility="collapsed",
        placeholder="Write your melody idea here.\nInclude vibe, instruments, and tempo/BPM.\n",
    )
    if melody_desc != (song.melody_description or ""):
        song.melody_description = melody_desc

    # ✅ TILES מתחת
    if st.session_state.current_mode == MODE_MELODY:
        if not st.session_state.get("melody_mode_entered", False):
            st.session_state.melody_mode_entered = True
            st.session_state.show_genre_tiles = True
            if not st.session_state.get("melody_genre_hint_sent", False):
                _push_melody_genre_hint()
                st.session_state.melody_genre_hint_sent = True

        if st.session_state.get("show_genre_tiles", False):
            selected_genre, selected_sub_genre = render_genre_tiles(
                st.session_state.get("selected_genre"),
                st.session_state.get("selected_sub_genre")
            )

            # סנכרון state + song
            st.session_state.selected_genre = selected_genre
            st.session_state.selected_sub_genre = selected_sub_genre
            song.genre = selected_genre
            song.sub_genre = selected_sub_genre

            # ✅ להחיל פעם אחת לכל בחירה של (genre, subgenre)
            if song.genre and song.sub_genre:
                cur = (song.genre, song.sub_genre)
                if st.session_state.get("last_genre_applied") != cur:
                    st.session_state["last_genre_applied"] = cur

                    _apply_genre_to_melody_text(song, song.genre, song.sub_genre)

                    # ✅ חשוב: לא לשנות melody_description_input אחרי שה-text_area כבר נוצר
                    # במקום זה מסמנים sync ל-rerun הבא
                    st.session_state.melody_desc_needs_sync = True

                    _push_genre_summary_to_chat(song)
                    st.session_state.show_genre_tiles = False
                    st.rerun()

    # 3) GENERATE
    has_melody = bool((song.melody_description or "").strip())
    can_generate = has_melody

    st.markdown(
        "<hr style='border:none; border-top:1px solid rgba(0,0,0,0.12); margin:12px 0;'/>",
        unsafe_allow_html=True
    )

    wrapper_cls = "full" if can_generate else "empty"
    st.markdown(f"<div class='melody-generate {wrapper_cls}'>", unsafe_allow_html=True)

    clicked = st.button(
        "🎵 GENERATE",
        type="primary",
        use_container_width=True,
        key="melody_generate_btn",
        disabled=not can_generate
    )

    hint_h = 26
    if not can_generate:
        missing = []
        if not has_melody:
            missing.append("melody")
        st.markdown(
            f"<div style='min-height:{hint_h}px; margin-top:4px; font-size:0.95rem; opacity:0.65;'>"
            f"Add a melody description to enable Generate."
            f"</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(f"<div style='height:{hint_h}px'></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # --- לוגיקה אחרי לחיצה ---
    if clicked:
        # בדיקה נוספת (למרות שהכפתור מושבת כשחסר)
        if not can_generate:
            st.warning("Please add lyrics and a melody description first!")
        else:
            with st.spinner("Composing your song... (approx 60s)"):
                result = music_generator.generate_music(
                    lyrics=song.lyrics,
                    melody_description=song.melody_description
                )

            if isinstance(result, str) and result.endswith(".mp3"):
                song.set_generated_audio(result)
                st.success("Music generated successfully!")
                st.rerun()
            else:
                # כאן result הוא ה-message
                st.error(result or "Generation failed.")

    # --- הצגת נגן (נשאר גם אחרי rerun) ---
    if getattr(song, "generated", False) and getattr(song, "audio_path", None):
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        st.audio(song.audio_path)


def render_chat():
    if not st.session_state.get("mode_greeted_once", False):
        _push_welcome_and_mode(
            st.session_state.get("current_mode", MODE_LYRICS),
            include_welcome=True
        )
        st.session_state.mode_greeted_once = True
        st.rerun()
        return

    # -------- render messages --------
    history = st.session_state.get("chat_history", [])
    if not history:
        messages_html = "<div class='emptyhint'>Start a conversation with the AI assistant...</div>"
    else:
        parts = []
        for msg in history:
            role = msg.get("role", "assistant")
            cls = "user" if role == "user" else "assistant"
            raw = msg.get("content", "") or ""
            safe = html.escape(raw)
            # תמיכה ב-**bold** => <strong>
            safe = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe)
            safe = re.sub(r"(?m)^\s*\*\s+", "• ", safe)
            content = safe

            # ✅ keep bold markers readable in plain text bubble (optional)
            parts.append(f"<div class='msg {cls}'>{content}</div>")
        messages_html = "".join(parts)

    st.markdown(
        f"""
        <div class='panel-box chatbox' style='height:453px;margin-bottom:0px;overflow-y:auto;'>
          {messages_html}
          <div id="chat-bottom"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # -------- auto scroll once --------
    should_scroll = st.session_state.get("scroll_chat_to_bottom", False)

    components.html(
        f"""
        <script>
          (function () {{
            const shouldScroll = {str(should_scroll).lower()};
            if (!shouldScroll) return;

            const doc = window.parent.document;

            function getChatbox() {{
              return doc.querySelector('.chatbox');
            }}

            function doScroll() {{
              const box = getChatbox();
              const bottom = doc.getElementById('chat-bottom');
              if (!box) return false;

              box.scrollTop = box.scrollHeight;
              if (bottom) {{
                bottom.scrollIntoView({{ block: "end" }});
              }}
              return (box.scrollHeight - box.clientHeight - box.scrollTop) < 4;
            }}

            let tries = 0;
            function rafLoop() {{
              tries++;
              if (doScroll() || tries > 80) return;
              requestAnimationFrame(rafLoop);
            }}
            requestAnimationFrame(rafLoop);

            const obs = new MutationObserver(() => {{
              if (doScroll()) obs.disconnect();
            }});
            obs.observe(doc.body, {{ childList: true, subtree: true }});

            setTimeout(doScroll, 100);
            setTimeout(doScroll, 250);
          }})();
        </script>
        """,
        height=0,
    )

    if should_scroll:
        st.session_state.scroll_chat_to_bottom = False

    # -------- controls (FORM) --------
    current_mode = st.session_state.current_mode
    switch_to = MODE_MELODY if current_mode == MODE_LYRICS else MODE_LYRICS
    with st.form("chat_form", clear_on_submit=True):
        st.text_input(
            "Chat",
            key="chat_text",
            placeholder="Type your message...",
            label_visibility="collapsed",
        )

        c_send, c_switch = st.columns([1, 1], gap="small")
        with c_send:
            send_clicked = st.form_submit_button("Send Text", use_container_width=True, key="btn_send")
        with c_switch:
            switch_clicked = st.form_submit_button(
                f"Switch to {switch_to.capitalize()}",
                use_container_width=True,
                key="btn_switch"
            )

    # -------- handle switch --------
    if switch_clicked:
        st.session_state.current_mode = switch_to

        if switch_to == MODE_MELODY:
            st.session_state.show_genre_tiles = True
        else:
            st.session_state.show_genre_tiles = False

        _push_welcome_and_mode(switch_to, include_welcome=False)
        st.rerun()

    # -------- handle send --------
    if send_clicked:
        text = (st.session_state.get("chat_text") or "").strip()
        if text:
            # close genre tiles if open
            if st.session_state.get("show_genre_tiles"):
                st.session_state.show_genre_tiles = False

            # line replacement flow (your existing flow)
            if st.session_state.get("waiting_for_line_replacement") and st.session_state.get("selected_line_index") is not None:
                st.session_state.line_replacement_text = text
                st.session_state.waiting_for_line_replacement = False
                st.rerun()
                return

            # normal chat flow
            st.session_state.chat_history.append({"role": "user", "content": text})

            agent = st.session_state.lyrics_agent if st.session_state.current_mode == MODE_LYRICS else st.session_state.melody_agent

            if agent:
                song = st.session_state.current_song
                song_snapshot = build_song_snapshot(song)
                recent_messages = st.session_state.chat_history[-3:]

                # ===== ✅ NEW: ALWAYS SEND SONG CONTEXT + SHORT-ANSWER RULES =====
                title = (song.title or "").strip() if song else ""
                intent = (getattr(song, "intent", "") or "").strip() if song else ""
                genre = getattr(song, "genre", None) if song else None
                sub = getattr(song, "sub_genre", None) if song else None
                mel_desc = (getattr(song, "melody_description", "") or "").strip() if song else ""
                lyrics_list = (getattr(song, "lyrics", []) or []) if song else []

                lyrics_preview = "\n".join(lyrics_list[-6:]) if lyrics_list else ""

                song_context = (
                    "SONG CONTEXT (use this to tailor your answer):\n"
                    f"- Title: {title}\n"
                    f"- Intent (topic/mood): {intent}\n"
                )

                if genre or sub:
                    song_context += f"- Genre/Sub: {genre} / {sub}\n"
                if mel_desc:
                    song_context += f"- Melody description (current): {mel_desc[:240]}\n"
                if lyrics_preview:
                    song_context += f"- Recent lyrics:\n{lyrics_preview}\n"

                song_context += "\nRULES: 3 bullets max, no paragraphs, end with 1 question.\n\n"

                # ===== 🔎 DYNAMIC GUIDE RULES (keyword-based) =====
                state = "LYRICS" if st.session_state.current_mode == MODE_LYRICS else "MELODY"

                # נותנים לרטריבר גם הקשר, לא רק ההודעה
                msg_for_rules = (
                    f"{text}\n"
                    f"{title}\n"
                    f"{intent}\n"
                    f"{mel_desc}\n"
                    f"{lyrics_preview}"
                )

                picked_rules = retrieve_rules(
                    message=msg_for_rules,
                    state=state,
                    limit=3
                )

                dynamic_rules_block = format_rules_for_prompt(picked_rules)

                # ===== keep your focused-line context (rewriting) =====
                focused_idx = st.session_state.get("selected_line_index")
                focused_line = ""
                if focused_idx is not None and song and 0 <= focused_idx < len(song.lyrics):
                    focused_line = song.lyrics[focused_idx]

                focused_context = ""
                if focused_line:
                    focused_context = (
                        f"FOCUSED LINE (we are rewriting line {focused_idx + 1}):\n"
                        f"\"{focused_line}\"\n\n"
                    )

                user_payload = song_context + dynamic_rules_block + focused_context + f"USER MESSAGE:\n{text}"

                ai_response = agent.get_response(
                    user_message=user_payload,
                    song_snapshot=song_snapshot,
                    chat_history=recent_messages
                )
                ai_response = compact_newlines(ai_response)

                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            else:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": "AI agent not available. Please check your API key configuration."
                })

            st.session_state.scroll_chat_to_bottom = True
            st.rerun()
            return


def compact_newlines(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\n+", "\n", text).strip()


def render_sidebar_drafts():
    """Sidebar drafts (כמו שהיה אצלך)."""
    with st.sidebar:
        st.title("DRAFTS")

        st.markdown(f"""
        <style>
        div[data-testid="stVerticalBlock"] > button[key="create_new_song"] {{
            background-color: {COLORS['secondary_accent']} !important;
            color: {COLORS['primary_text']} !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            height: 48px !important;
        }}
        div[data-testid="stVerticalBlock"] > button[key="create_new_song"]:hover {{
            opacity: 0.9;
        }}
        </style>
        """, unsafe_allow_html=True)

        if st.button("+ Start a new song", use_container_width=True, key="create_new_song"):
            st.session_state.show_creation_modal = True
            st.session_state.current_song = None
            st.session_state.current_draft_id = None  # ✅ הכי חשוב
            st.session_state.chat_history = []

            # ✅ reset one-time hints for the new song/session
            st.session_state.mode_greeted_once = False
            st.session_state.melody_mode_entered = False
            st.session_state.show_genre_tiles = False
            st.session_state.melody_genre_hint_sent = False

            st.switch_page("pages/1_Choose_Start.py")

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        drafts = load_drafts()
        for d in drafts:
            if st.button(d["name"], key=f"draft_{d['id']}", use_container_width=True):
                st.session_state.current_song = dict_to_song(d["song"])
                st.session_state.current_draft_id = d["id"]
                st.session_state.chat_history = []
                st.session_state.mode_greeted_once = False
                st.switch_page("pages/2_Workspace.py")


def _push_welcome_message():
    _chat_add("assistant",
              "Welcome to **ECHO** ✨\n"
              "I’m your AI assistant for writing lyrics and shaping melodies.\n"
              "Let’s create something awesome."
              )


def _push_mode_greeting(mode: str):
    mode_upper = (mode or "").upper()
    if mode_upper == "LYRICS":
        msg = ("Hi! You’re in **LYRICS** mode 🎤\n"
               "Tell me what you want to write, the vibe, or paste a few lines — and I’ll help you shape them.")
    elif mode_upper == "MELODY":
        msg = ("Hi! You’re in **MELODY** mode 🎶\n"
               "What vibe do you want (happy/dark/nostalgic), tempo/BPM, and main instruments?")
    else:
        msg = f"Hi! You’re in **{mode_upper}** mode. How can I help you?"
    _chat_add("assistant", msg)


def _push_melody_genre_hint():
    _chat_add("assistant",
              "On your left, pick a **genre** 🎧\n"
              "You can preview each one by clicking the **play** button."
              )


def _push_welcome_and_mode(mode: str, include_welcome: bool = False):
    """Push welcome (optional) + mode message, then scroll."""
    if include_welcome:
        _push_welcome_message()
    _push_mode_greeting(mode)
    st.session_state.scroll_chat_to_bottom = True


def _chat_add(role: str, content: str, scroll: bool = True):
    st.session_state.chat_history.append({"role": role, "content": content})
    if scroll:
        st.session_state.scroll_chat_to_bottom = True

