import os
import uuid
import requests
from typing import Optional, List
from datetime import datetime

# נתיב שמירה
OUTPUT_DIR = os.path.join("assets", "audio", "generated")


def generate_music(lyrics: List[str], melody_description: str) -> Optional[str]:
    """
    Generate music using the verified endpoint: /v1/music
    Based on official API docs found by user.
    """

    api_key = os.getenv("ELEVENLABS_API_KEY")
    url = "https://api.elevenlabs.io/v1/music"

    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not found")
        return None

    try:
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        lyrics_text = "\n".join(lyrics) if lyrics else ""
        style_desc = f"{melody_description}".strip()
        full_prompt = "Generate a song based on the user's request below.\n Follow it as closely as possible while keeping musical coherence. \n Avoid adding elements that are clearly outside the requested style.\n"

        if lyrics_text:
            full_prompt += (
                f"User request melody of style:\n {style_desc}. "
                f"User song lyrics: {lyrics_text}"
            )
            instrumental_flag = False
        else:
            full_prompt += f"User request melody of style:\n {style_desc}\n no lyrics only melody"
            instrumental_flag = True

        print("=== GENERATING VIA /V1/MUSIC ===")
        print(f"Endpoint: {url}")
        print(f"Target Length: 30s (to save credits)")

        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": full_prompt,
            "model_id": "music_v1",
            "music_length_ms": 20000,  # 30 שניות = 30,000 מילי-שניות (חובה שיהיה בין 3000 ל-600000)
            "force_instrumental": instrumental_flag
        }

        # 3. שליחה
        response = requests.post(url, json=payload, headers=headers, timeout=120)

        # 4. בדיקת תוצאה
        if response.status_code == 200:
            # יצירת חותמת זמן: שנה-חודש-יום_שעה-דקה-שניות
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"song_{timestamp}.mp3"

            # המשך הקוד נשאר אותו דבר:
            file_path = os.path.join(OUTPUT_DIR, unique_filename)

            with open(file_path, "wb") as f:
                f.write(response.content)

            print(f"SUCCESS: Music generated! Saved to {file_path}")
            return file_path

        else:
            print(f"API ERROR {response.status_code}: {response.text}")
            err_json = response.json()
            return err_json["detail"]["message"]

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        return None