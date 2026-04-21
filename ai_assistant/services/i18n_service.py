# services/i18n_service.py

from googletrans import Translator

translator = Translator()

def translate_msg(message: str, target_lang: str = "en") -> str:
    if target_lang == "en":
        return message
    try:
        translated = translator.translate(message, dest=target_lang)
        return translated.text
    except Exception as e:
        print("Translation failed:", e)
        return message