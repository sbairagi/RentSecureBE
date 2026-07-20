"""Tests for rentsecure_be type compatibility and configuration modules."""

from django.test import TestCase

from rentsecure_be.asgi import django_asgi_app
from rentsecure_be.type_compat import override
from rentsecure_be.wsgi import application


class TypeCompatTest(TestCase):
    def test_override_decorator_preserves_function(self):
        @override
        def my_method(self):
            return "hello"

        self.assertEqual(my_method(None), "hello")

    def test_override_decorator_preserves_name(self):
        @override
        def my_method(self):
            return "hello"

        self.assertEqual(my_method.__name__, "my_method")


class AsgiConfigTest(TestCase):
    def test_asgi_application_exists(self):
        self.assertIsNotNone(django_asgi_app)

    def test_asgi_application_is_callable(self):
        self.assertTrue(callable(django_asgi_app))


class WsgiConfigTest(TestCase):
    def test_wsgi_application_exists(self):
        self.assertIsNotNone(application)

    def test_wsgi_application_is_callable(self):
        self.assertTrue(callable(application))
