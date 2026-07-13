# services/voice_service.py
import asyncio
import os
import tempfile

import edge_tts

LANGUAGE_CODE_MAP = {
    "en": "en-US",
    "hi": "hi-IN",
}


def generate_voice_note(text: str, lang: str = "en") -> str:
    try:
        edge_lang = LANGUAGE_CODE_MAP.get(lang, lang)

        async def _generate(path: str) -> str:
            communicate = edge_tts.Communicate(text, edge_lang)
            await communicate.save(path)
            return path

        fd, path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        try:
            return asyncio.run(_generate(path))
        finally:
            pass
    except Exception as e:
        print("Voice note generation failed:", e)
        return ""
