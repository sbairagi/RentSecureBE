"""Tests for rentsecure_be/services/i18n_service.py."""

from unittest.mock import MagicMock, patch

from rentsecure_be.services.i18n_service import translate_msg


class TestTranslateMsg:
    def test_returns_original_when_target_lang_is_en(self):
        with patch(
            "rentsecure_be.services.i18n_service.GoogleTranslator"
        ) as mock_translator:
            result = translate_msg("Hello world", target_lang="en")
        assert result == "Hello world"
        mock_translator.assert_not_called()

    @patch("rentsecure_be.services.i18n_service.GoogleTranslator")
    def test_returns_translated_text_on_success(self, mock_translator_cls):
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "Hola mundo"
        mock_translator_cls.return_value = mock_instance

        result = translate_msg("Hello world", target_lang="es")

        assert result == "Hola mundo"
        mock_translator_cls.assert_called_once_with(source="auto", target="es")
        mock_instance.translate.assert_called_once_with("Hello world")

    @patch("rentsecure_be.services.i18n_service.GoogleTranslator")
    def test_returns_original_when_translated_is_none(self, mock_translator_cls):
        mock_instance = MagicMock()
        mock_instance.translate.return_value = None
        mock_translator_cls.return_value = mock_instance

        result = translate_msg("Hello world", target_lang="fr")

        assert result == "Hello world"
        mock_instance.translate.assert_called_once_with("Hello world")

    @patch("rentsecure_be.services.i18n_service.GoogleTranslator")
    def test_returns_original_on_exception(self, mock_translator_cls):
        mock_instance = MagicMock()
        mock_instance.translate.side_effect = Exception("API error")
        mock_translator_cls.return_value = mock_instance

        result = translate_msg("Hello world", target_lang="de")

        assert result == "Hello world"
        mock_instance.translate.assert_called_once_with("Hello world")
