"""
Base AI agent for ECHO application.
Handles Gemini API integration (Fixed Logic).
"""

import os
from google import genai
from typing import List, Dict, Optional


class BaseAgent:
    """Base class for AI agents using Gemini (google-genai)."""

    def __init__(self, system_prompt: str):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # google-genai client
        self.client = genai.Client(api_key=self.api_key)

        # keep these so you can reuse in requests
        self.model_name = "gemini-2.0-flash"
        self.system_prompt = system_prompt

    def get_response(
            self,
            user_message: str,
            song_snapshot,
            chat_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Get a response from the AI agent.
        Avoids sending duplicate user messages in the history.
        """
        try:
            contents = []

            # 1) Song snapshot as constant context (send as USER context)
            if song_snapshot:
                contents.append({
                    "role": "user",
                    "parts": [{"text": f"SONG SNAPSHOT (context):\n{str(song_snapshot)}"}],
                })

            # 2) Chat history (avoid duplicating the current user message)
            if chat_history:
                history_to_process = chat_history
                if (
                        chat_history
                        and chat_history[-1].get("content") == user_message
                        and chat_history[-1].get("role") == "user"
                ):
                    history_to_process = chat_history[:-1]

                for msg in history_to_process:
                    role = "model" if msg.get("role") == "assistant" else "user"
                    contents.append({
                        "role": role,
                        "parts": [{"text": msg.get("content", "")}],
                    })

            # 3) Current message (this already includes your short-rules + title/topic/mood prefix)
            contents.append({
                "role": "user",
                "parts": [{"text": user_message}],
            })

            # 4) Call Gemini (LIMIT OUTPUT!)
            resp = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config={
                    "system_instruction": self.system_prompt,
                    "max_output_tokens": 160,  # ✅ הכי חשוב כדי לעצור פסקאות
                    "temperature": 0.6,  # ✅ פחות נטייה להאריך
                },
            )

            text = (resp.text or "").strip()
            return text if text else "..."

        except Exception as e:
            print(f"Gemini API Error: {e}")
            return "Error calling Gemini API."