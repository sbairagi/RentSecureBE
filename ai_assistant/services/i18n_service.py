# services/i18n_service.py

from deep_translator import GoogleTranslator


def translate_msg(message: str, target_lang: str = "en") -> str:
    if target_lang == "en":
        return message

    try:
        translated = GoogleTranslator(
            source='auto',
            target=target_lang
        ).translate(message)

        return translated

    except Exception as e:
        print("Translation failed:", e)
        return message
