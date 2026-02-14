from .base import *

DEBUG = False

# ManifestStaticFilesStorage is recommended in production, to prevent
# outdated JavaScript / CSS assets being served from cache
# (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/6.0/ref/contrib/staticfiles/#manifeststaticfilesstorage
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"


DJANGO_VITE = {
  "default": {
    "dev_mode": False,
    "manifest_path": PROJECT_DIR / "static" / "dist" / ".vite" / "manifest.json",
    "static_url_prefix": "dist/", # Pour que Django sache qu'il faut chercher dans static/dist/
  }
}
