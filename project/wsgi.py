"""
WSGI config for project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
from pathlib import Path
import environ


env = environ.Env()

BASE_DIR = Path(__file__).resolve().parent

environ.Env.read_env(BASE_DIR.parent / ".env")

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", env("DJANGO_SETTINGS_MODULE"))

application = get_wsgi_application()
