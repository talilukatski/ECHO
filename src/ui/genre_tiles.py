"""
Genre selection UI component for MELODY mode.
"""

import streamlit as st
import os
from src.config.settings import COLORS, GENRES, AUDIO_SAMPLES_DIR
import streamlit.components.v1 as components
import base64


# Get absolute path for audio samples
def get_audio_path(filename):
    """Get absolute path to audio sample file."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, AUDIO_SAMPLES_DIR, filename)


def render_genre_tiles(selected_genre=None, selected_sub_genre=None):
    """
    Render genre selection tiles.
    Returns: (selected_genre, selected_sub_genre)
    """
    st.markdown("<div id='genre-tiles-start'></div>", unsafe_allow_html=True)
    st.markdown("<div class='genre-js-marker'></div>", unsafe_allow_html=True)

    components.html("""
    <script>
    (function () {
      const doc = window.parent.document;

      function mark() {
        const start = doc.querySelector('#genre-tiles-start');
        if (!start) return false;

        let root = start.parentElement;
        while (root && !root.querySelector('#genre-tiles-end')) root = root.parentElement;
        if (!root) return false;

        doc.querySelectorAll('.genre-tiles-root').forEach(el => el.classList.remove('genre-tiles-root'));
        root.classList.add('genre-tiles-root');

        root.querySelectorAll('button.play-btn').forEach(b => b.classList.remove('play-btn'));
        root.querySelectorAll('button').forEach(btn => {
          const t = (btn.textContent || '').replace(/\\s+/g,'');
          if (t.includes('▶')) btn.classList.add('play-btn');
        });

        return true;
      }

      let tries = 0;
      function loop() {
        tries++;
        if (mark() || tries > 60) return;
        requestAnimationFrame(loop);
      }
      requestAnimationFrame(loop);

      const obs = new MutationObserver(() => mark());
      obs.observe(doc.body, { childList: true, subtree: true });

      // ✅ extra passes after Streamlit finishes rendering
      setTimeout(mark, 120);
      setTimeout(mark, 260);
    })();
    </script>
    """, height=0)

    # -------- CONTENT --------
    if selected_sub_genre:
        res = (selected_genre, selected_sub_genre)
    elif selected_genre:
        res = render_sub_genre_tiles(selected_genre)
    else:
        res = render_main_genre_tiles()

    st.markdown("<div id='genre-tiles-end'></div>", unsafe_allow_html=True)
    return res


def render_main_genre_tiles():
    """Render main genre tiles + preview (single audio player)."""
    st.markdown("<div class='tiles-caption'>Select a Genre</div>", unsafe_allow_html=True)

    if "genre_preview" not in st.session_state:
        st.session_state.genre_preview = None

    cols = st.columns(3, gap="small")

    for idx, (genre_name, genre_data) in enumerate(GENRES.items()):
        with cols[idx % 3]:
            is_selected = (st.session_state.get("selected_genre") == genre_name)
            label = f"✅ Pick {genre_name}" if is_selected else f"Pick {genre_name}"

            if st.button(label, key=f"genre_pick_{genre_name}", use_container_width=True):
                st.session_state.genre_preview = None
                st.session_state.selected_genre = genre_name
                st.session_state.selected_sub_genre = None  # ✅ איפוס תת־ז'אנר כשמחליפים ז'אנר
                st.rerun()

            genre_file_name = genre_name.lower().replace("-", "").replace(" ", "_")
            audio_filename = f"{genre_file_name}_sample.mp3"
            audio_path = get_audio_path(audio_filename)
            audio_exists = os.path.exists(audio_path)

            # ✅ WRAP play button
            st.markdown("<div class='play-wrap'>", unsafe_allow_html=True)
            if st.button("▶", key=f"genre_prev_{genre_name}", use_container_width=True, disabled=not audio_exists):
                st.session_state.genre_preview = genre_name
            st.markdown("</div>", unsafe_allow_html=True)

    preview = st.session_state.get("genre_preview")
    if preview:
        genre_file_name = preview.lower().replace("-", "").replace(" ", "_")
        audio_filename = f"{genre_file_name}_sample.mp3"
        audio_path = get_audio_path(audio_filename)

        if os.path.exists(audio_path):
            st.markdown("<div class='audio-wrap-spacer'></div>", unsafe_allow_html=True)
            with open(audio_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            components.html(
                f"""
                <audio autoplay controls style="width:100%;">
                  <source src="data:audio/mpeg;base64,{b64}" type="audio/mpeg">
                </audio>
                """,
                height=60,
            )

    return st.session_state.get("selected_genre"), None


def render_sub_genre_tiles(genre_name: str):
    """Render sub-genre tiles + preview (single audio player)."""
    st.markdown("<div class='tiles-caption'>Select a Sub-Genre</div>", unsafe_allow_html=True)

    sub_genres = GENRES[genre_name]["sub_genres"]

    if "subgenre_preview" not in st.session_state:
        st.session_state.subgenre_preview = None

    cols = st.columns(3, gap="small")
    g = genre_name.lower().replace("-", "").replace(" ", "_")

    for idx, sub_genre in enumerate(sub_genres):
        with cols[idx % 3]:
            is_selected = (st.session_state.get("selected_sub_genre") == sub_genre)
            label = f"✅ Pick {sub_genre}" if is_selected else f"Pick {sub_genre}"

            if st.button(label, key=f"subgenre_pick_{genre_name}_{sub_genre}", use_container_width=True):
                st.session_state.genre_preview = None
                st.session_state.subgenre_preview = None
                st.session_state.selected_sub_genre = sub_genre
                st.rerun()

            # preview
            s = sub_genre.lower().replace("-", "").replace(" ", "_")
            audio_filename = f"{g}_{s}_sample.mp3"
            audio_path = get_audio_path(audio_filename)
            audio_exists = os.path.exists(audio_path)

            # ✅ WRAP play button
            st.markdown("<div class='play-wrap'>", unsafe_allow_html=True)
            if st.button("▶", key=f"subgenre_prev_{genre_name}_{sub_genre}", use_container_width=True, disabled=not audio_exists):
                st.session_state.subgenre_preview = (genre_name, sub_genre)
            st.markdown("</div>", unsafe_allow_html=True)

    preview = st.session_state.get("subgenre_preview")
    if preview:
        g_name, s_name = preview
        g2 = g_name.lower().replace("-", "").replace(" ", "_")
        s2 = s_name.lower().replace("-", "").replace(" ", "_")
        audio_filename = f"{g2}_{s2}_sample.mp3"
        audio_path = get_audio_path(audio_filename)

        if os.path.exists(audio_path):
            st.markdown("<div class='audio-wrap-spacer'></div>", unsafe_allow_html=True)
            with open(audio_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            components.html(
                f"""
                <audio autoplay controls style="width:100%;">
                  <source src="data:audio/mpeg;base64,{b64}" type="audio/mpeg">
                </audio>
                """,
                height=60,
            )
    return st.session_state.get("selected_genre"), st.session_state.get("selected_sub_genre")





