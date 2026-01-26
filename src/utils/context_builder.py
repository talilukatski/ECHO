def build_song_snapshot(song):
    if not song:
        return "CURRENT SONG STATE:\nNo song yet."

    lines = [
        "CURRENT SONG STATE:",
        f"Title: {song.title}",
        f"Genre: {song.genre or 'Not set'}",
        f"Sub-Genre: {song.sub_genre or 'Not set'}",
        f"Melody: {song.melody_description or 'Not set'}",
        "",
        "Lyrics (current version):"
    ]

    if song.lyrics:
        for i, line in enumerate(song.lyrics, 1):
            lines.append(f"{i}. {line}")
    else:
        lines.append("— No lyrics yet —")

    return "\n".join(lines)

def get_recent_messages(chat_history, limit=7):
    return chat_history[-limit:]
