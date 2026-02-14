from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-0qry-7^qyipob(^0e6grc+%#@+k^)jw-tyy=(y48t5wyb*c(z7"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DJANGO_VITE = {
  "default": {
    "dev_mode": DEBUG,
    "dev_server_host": "localhost",
    "dev_server_port": 5173,
    # En dev, le chemin du manifest n'est pas utilisé par django-vite,
    # mais il vaut mieux laisser la structure
    "manifest_path": PROJECT_DIR / "static" / "dist" / ".vite" / "manifest.json",
  }
}
