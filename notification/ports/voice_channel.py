from __future__ import annotations

from typing import Protocol


class VoiceChannel(Protocol):
    def generate_voice_note(self, text: str, lang: str) -> str: ...
