"""
Song data model for ECHO application.
"""

from typing import List, Optional


class Song:
    """Represents a song draft with lyrics, melody, and metadata."""
    
    def __init__(self, title: str = "Draft", intent: Optional[str] = None):
        self.title = title
        self.intent = intent  # Initial creation intent from user
        self.lyrics: List[str] = []  # List of lyric lines
        self.melody_description: str = ""  # Textual description of melody
        self.genre: Optional[str] = None
        self.sub_genre: Optional[str] = None
        self.audio_path: Optional[str] = None  # Path to generated MP3
        self.generated: bool = False  # Whether music has been generated
        
    def add_lyric_line(self, line: str, index: Optional[int] = None):
        """Add a lyric line. If index is provided, insert at that position."""
        if index is not None:
            self.lyrics.insert(index, line)
        else:
            self.lyrics.append(line)
    
    def replace_lyric_line(self, old_index: int, new_line: str):
        """Replace a lyric line at the given index."""
        if 0 <= old_index < len(self.lyrics):
            self.lyrics[old_index] = new_line
    
    def remove_lyric_line(self, index: int):
        """Remove a lyric line at the given index."""
        if 0 <= index < len(self.lyrics):
            self.lyrics.pop(index)
    
    def has_melody(self) -> bool:
        """Check if melody description exists."""
        return bool(self.melody_description.strip())

    def delete_lyric_line(self, index: int):
        if 0 <= index < len(self.lyrics):
            self.lyrics.pop(index)

    def to_dict(self):
        """Convert song to dictionary for easy serialization."""
        return {
            "title": self.title,
            "intent": self.intent,
            "lyrics": self.lyrics,
            "melody_description": self.melody_description,
            "genre": self.genre,
            "sub_genre": self.sub_genre,
            "audio_path": self.audio_path,
            "generated": self.generated
        }

    def set_generated_audio(self, path: str):
        """
        Updates the song with the generated audio path and marks it as generated.
        Use this method instead of setting attributes directly to ensure consistency.
        """
        self.audio_path = path
        self.generated = True
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create a Song instance from a dictionary."""
        song = cls(title=data.get("title", "DRAFT"), intent=data.get("intent"))
        song.lyrics = data.get("lyrics", [])
        song.melody_description = data.get("melody_description", "")
        song.genre = data.get("genre")
        song.sub_genre = data.get("sub_genre")
        song.audio_path = data.get("audio_path")
        song.generated = data.get("generated", False)
        return song

