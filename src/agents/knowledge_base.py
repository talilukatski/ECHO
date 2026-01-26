from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import re


# ---------- helpers ----------
_WORD_RE = re.compile(r"[a-zA-Z']+")

def _tokenize(text: str) -> List[str]:
    return _WORD_RE.findall((text or "").lower())

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()

def _contains_phrase(norm_msg: str, phrase: str) -> bool:
    # phrase match (space-normalized)
    phrase = _normalize(phrase)
    return phrase and phrase in norm_msg


# ---------- rules ----------
LYRICS_GUIDE_RULES = [
    {"keywords": ["message", "theme", "meaning", "what is it about"], "rule": "Focus on ONE clear core message. Avoid mixing unrelated ideas."},
    {"keywords": ["emotion", "feeling", "sad", "happy", "angry", "nostalgic"], "rule": "Show emotion through moments/images, not by naming the emotion."},
    {"keywords": ["pov", "perspective", "narrator", "i", "you", "he", "she"], "rule": "Pick ONE point of view (I/you/he) and keep it consistent."},
    {"keywords": ["imagery", "visual", "scene", "picture", "describe"], "rule": "Prefer concrete images/actions over abstract statements."},
    {"keywords": ["details", "specific", "real", "story"], "rule": "Add specific details (place/time/object) to make it believable."},
    {"keywords": ["metaphor", "symbol", "like", "as if"], "rule": "Metaphors should be easy to visualize and stay consistent."},
    {"keywords": ["cliche", "generic", "cringe"], "rule": "Avoid clichés unless you personalize or flip them."},
    {"keywords": ["flow", "rhythm", "cadence"], "rule": "Keep line length similar within the same section for better flow."},
    {"keywords": ["syllables", "too long", "hard to sing"], "rule": "If it’s hard to sing: reduce syllables, simplify words, shorten lines."},
    {"keywords": ["spoken", "natural", "say it"], "rule": "Read it out loud—lyrics should sound natural when spoken."},
    {"keywords": ["rhyme", "rhymes"], "rule": "Rhyme should support clarity—don’t force awkward words."},
    {"keywords": ["near rhyme", "imperfect rhyme", "slant rhyme"], "rule": "Near-rhymes often sound more modern and natural than perfect rhymes."},
    {"keywords": ["repetition", "repeat", "again"], "rule": "Use repetition intentionally to strengthen hooks and emotion."},
    {"keywords": ["chorus", "hook", "refrain"], "rule": "Chorus = simplest words + main message + a repeatable hook."},
    {"keywords": ["title", "name of the song"], "rule": "Strong titles often appear in the chorus hook."},
    {"keywords": ["catchy", "memorable"], "rule": "A hook is short, repeatable, and emotionally direct."},
    {"keywords": ["verse", "story", "details"], "rule": "Verses should add NEW details; don’t just repeat the chorus idea."},
    {"keywords": ["bridge", "switch", "change up"], "rule": "Bridge adds contrast (new angle/emotion/imagery), then returns to chorus."},
    {"keywords": ["progress", "develop", "advance"], "rule": "Each section should move the song forward (new info or new feeling)."},
    {"keywords": ["edit", "rewrite", "improve"], "rule": "Edit in small steps: change ONE thing at a time (image, rhyme, or rhythm)."},
    {"keywords": ["clarity", "confusing", "doesn't make sense"], "rule": "If intent is unclear, clarify the message before rewriting lines."},
]

MELODY_GUIDE_RULES = [
    {"keywords": ["tempo", "bpm", "speed", "fast", "slow"], "rule": "Tempo should support the emotional intent (sad=slower, hype=faster)."},
    {"keywords": ["groove", "rhythm", "beat", "swing"], "rule": "Pick one groove and keep it consistent across sections."},
    {"keywords": ["energy", "dynamic", "build"], "rule": "Build energy into the chorus (more drums, wider melody, stronger bass)."},
    {"keywords": ["contrast", "different", "switch"], "rule": "Contrast between sections keeps listeners engaged (texture/beat/range)."},
    {"keywords": ["arc", "journey", "progression"], "rule": "Think of the song as an emotional arc, not a static loop."},
    {"keywords": ["melody", "shape", "range", "higher"], "rule": "Choruses usually lift: higher notes + longer held tones on the hook."},
    {"keywords": ["hook melody", "catchy melody", "motif"], "rule": "Strong melodic hooks are short and repeatable (motif)."},
    {"keywords": ["instruments", "arrangement", "production"], "rule": "Arrange to leave space for vocals; avoid clutter in the same frequency range."},
    {"keywords": ["minimal", "sparse", "dense", "full"], "rule": "Sparse = intimate emotion; dense = impact/energy."},
    {"keywords": ["vocal", "delivery", "singing"], "rule": "Vocal delivery should match the lyric emotion (soft/intimate vs powerful)."},
    {"keywords": ["intimate", "powerful"], "rule": "Intimate: softer dynamics; Powerful: stronger drums + more lift in chorus."},
    {"keywords": ["genre", "style"], "rule": "Melody/production choices should fit genre expectations unless intentionally breaking them."},
    {"keywords": ["reference", "artist", "like", "similar to"], "rule": "Reference songs/artists help lock tempo, groove, and instrument palette."},
    {"keywords": ["theory", "chords", "key"], "rule": "Avoid heavy theory—describe feel, contour, and instruments in simple language."},
    {"keywords": ["options", "choose", "which"], "rule": "Offer 2–3 options; user chooses the final direction."},
]


# You can map your modes instead of ECHOState if you want:
# e.g. state can be "LYRICS" / "MELODY"
RULES_BY_STATE = {
    "LYRICS": LYRICS_GUIDE_RULES,
    "MELODY": MELODY_GUIDE_RULES,
}


DEFAULT_RULES = {
    "LYRICS": [
        "Keep it simple and singable. Prefer concrete images.",
        "Chorus = main message + repeatable hook (title helps).",
    ],
    "MELODY": [
        "Match tempo/groove to mood; keep it consistent.",
        "Chorus should lift (bigger energy + wider melody range).",
    ],
}


def retrieve_rules(message: str, state: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Select relevant rules for the current state using keyword + phrase matching.
    Returns list of rule dicts.
    """
    state = (state or "").upper().strip()
    rules = RULES_BY_STATE.get(state, [])
    if not rules:
        return []

    norm_msg = _normalize(message)
    tokens = set(_tokenize(message))

    scored = []
    for rule in rules:
        kws = rule.get("keywords", [])
        score = 0

        for kw in kws:
            kw_norm = _normalize(kw)
            if " " in kw_norm:
                # phrase keyword
                if _contains_phrase(norm_msg, kw_norm):
                    score += 3
            else:
                # token keyword
                if kw_norm in tokens:
                    score += 2
                # light fallback: substring (for cases like "rhymes" vs "rhyme")
                elif kw_norm and kw_norm in norm_msg:
                    score += 1

        if score > 0:
            scored.append((score, rule))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [r for _, r in scored][:limit]

    # fallback: always provide something
    if not top:
        top = [{"keywords": [], "rule": r} for r in DEFAULT_RULES.get(state, [])][:limit]

    return top


def format_rules_for_prompt(rules: List[Dict[str, Any]]) -> str:
    if not rules:
        return ""
    lines = ["DYNAMIC GUIDE RULES (apply if relevant):"]
    for r in rules:
        lines.append(f"- {r['rule']}")
    return "\n".join(lines) + "\n"
