from deep_translator import GoogleTranslator


def translate_msg(message: str, target_lang: str = "en") -> str:
    if target_lang == "en":
        return message

    try:
        translated: str | None = GoogleTranslator(
            source="auto", target=target_lang
        ).translate(message)

        if translated is None:
            return message

        return translated

    except Exception as e:
        print("Translation failed:", e)
        return message
