# services/voice_service.py
import asyncio
import tempfile

import edge_tts

LANGUAGE_CODE_MAP = {
    "en": "en-US",
    "hi": "hi-IN",
}


def generate_voice_note(text: str, lang: str = "en") -> str:
    try:
        edge_lang = LANGUAGE_CODE_MAP.get(lang, lang)

        async def _generate() -> str:
            communicate = edge_tts.Communicate(text, edge_lang)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
                path = temp.name
            await communicate.save(path)
            return path

        return asyncio.run(_generate())
    except Exception as e:
        print("Voice note generation failed:", e)
        return ""
