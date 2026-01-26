import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.models.song import Song


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DRAFTS_PATH = os.path.join(DATA_DIR, "drafts.json")


def _ensure_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DRAFTS_PATH):
        with open(DRAFTS_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def song_to_dict(song: Song):
    return {
        "title": song.title,
        "intent": getattr(song, "intent", ""),
        "lyrics": getattr(song, "lyrics", []) or [],
        "melody_description": getattr(song, "melody_description", "") or "",
        "genre": getattr(song, "genre", None),
        "sub_genre": getattr(song, "sub_genre", None),
    }


def dict_to_song(data: Dict[str, Any]) -> Song:
    song = Song(title=data.get("title") or "Untitled", intent=data.get("intent") or "")
    song.lyrics = data.get("lyrics") or []
    song.melody_description = data.get("melody_description") or ""
    song.genre = data.get("genre")
    song.sub_genre = data.get("sub_genre")
    return song


def load_drafts() -> List[Dict[str, Any]]:
    _ensure_file()
    with open(DRAFTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f) or []


def save_draft(song: Song, draft_id: Optional[str] = None) -> str:
    _ensure_file()
    drafts = load_drafts()

    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    payload = {
        "id": draft_id or str(uuid.uuid4()),
        "name": _safe_title_or_auto(song.title, drafts),
        "updated_at": now,
        "song": song_to_dict(song),
    }

    # update if exists, else insert
    for i, d in enumerate(drafts):
        if d.get("id") == payload["id"]:
            drafts[i] = payload
            break
    else:
        drafts.insert(0, payload)  # newest first

    with open(DRAFTS_PATH, "w", encoding="utf-8") as f:
        json.dump(drafts, f, ensure_ascii=False, indent=2)

    return payload["id"]


def delete_draft(draft_id: str) -> None:
    _ensure_file()
    drafts = [d for d in load_drafts() if d.get("id") != draft_id]
    with open(DRAFTS_PATH, "w", encoding="utf-8") as f:
        json.dump(drafts, f, ensure_ascii=False, indent=2)


def _next_draft_name(drafts, base="Draft") -> str:
    existing = {(d.get("name") or "").strip().upper() for d in drafts}

    n = 1
    while f"{base} {n}".upper() in existing:
        n += 1
    return f"{base} {n}"


def _safe_title_or_auto(song_title: str, drafts) -> str:
    t = (song_title or "").strip()
    return t if t else _next_draft_name(drafts, base="Draft")


def next_draft_title(base="Draft") -> str:
    drafts = load_drafts()
    existing = {(d.get("name") or "").strip().upper() for d in drafts}

    n = 1
    while f"{base} {n}".upper() in existing:
        n += 1
    return f"{base} {n}"


