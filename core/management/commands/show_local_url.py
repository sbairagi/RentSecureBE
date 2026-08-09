"""
Print the local IP address and the API base URL for mobile clients.

Usage:
    python manage.py show_local_url
"""

import socket

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Display the local LAN IP and API base URL for mobile development"

    def handle(self, *args, **kwargs):
        local_ip = self._get_local_ip()
        port = 8000
        api_base = f"http://{local_ip}:{port}/"

        self.stdout.write("Backend running at:")
        self.stdout.write(api_base)

    @staticmethod
    def _get_local_ip() -> str:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # The IP doesn't need to be reachable; this just figures out
                # which interface the OS would use to reach the internet.
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"
