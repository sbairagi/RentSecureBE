# services/voice_service.py
import tempfile

from gtts import gTTS


def generate_voice_note(text: str, lang: str = "en") -> str:
    try:
        tts = gTTS(text=text, lang=lang)
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp.name)
        return temp.name
    except Exception as e:
        print("Voice note generation failed:", e)
        return ""
