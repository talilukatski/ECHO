"""
Configuration constants for ECHO application.
UI colors, settings, and constants.
"""

# Color Palette (Soft Pastel Blues)
COLORS = {
    "primary_blue": "#42A5F5",
    "secondary_accent": "#FFD166",

    # רקעים
    "background": "#F5F7FB",
    "card": "#FFFFFF",

    # קווים והפרדות
    "borders": "#DDE3F8",

    # צ'אט
    "ai_chat_bubble": "#E6EBFF",

    # טקסט
    "primary_text": "#1F2A44",
    "secondary_text": "#8A94B8",
    "greyed_out": "#F1F3F6",
    "lyrics_text_c": "#6B728E",
    "lyrics_num_c":  "#6B7280",
}
BUTTON_STYLES = {
  "btn_add_line":        {"bg": "#22C55E", "border": "#16A34A", "text": "#0B1F12"},
  "btn_edit":            {"bg": "#A855F7", "border": "#7C3AED", "text": "#FFFFFF"},
  "btn_send":            {"bg": "#F97316", "border": "#EA580C", "text": "#111827"},
  "btn_switch":          {"bg": "#0EA5E9", "border": "#0284C7", "text": "#06222E"},
  "melody_generate_btn": {"bg": "#5A6FF0", "border": "#4158E6", "text": "#FFFFFF"},
}



# Application Modes
MODE_LYRICS = "LYRICS"
MODE_MELODY = "MELODY"

# Default Mode
DEFAULT_MODE = MODE_LYRICS

# Genre Configuration
GENRES = {
    "Pop": {
        "sub_genres": ["Pop Ballad", "Dance Pop", "Indie Pop"]
    },
    "Rock": {
        "sub_genres": ["Alternative Rock", "Classic Rock", "Soft Rock"]
    },
    "Indie": {
        "sub_genres": ["Indie Folk", "Indie Rock", "Indie Pop"]
    },
    "Jazz": {
        "sub_genres": ["Smooth Jazz", "Bebop", "Cool Jazz"]
    },
    "Hip-Hop": {
        "sub_genres": ["Trap", "Old School", "Alternative Hip-Hop"]
    },
    "Electronic": {
        "sub_genres": ["EDM", "Ambient", "Synthwave"]
    }
}

# Audio Sample Paths (relative to project root)
AUDIO_SAMPLES_DIR = "assets/audio/genre_samples"

# LLM Configuration
LLM_MODEL = "gemini-1.5-flash"

# Default Song Values
DEFAULT_SONG_TITLE = "DRAFT"
DEFAULT_LYRICS_PLACEHOLDER = "Start writing your song"
