from .base import *

DEBUG = False
SECRET_KEY = env("SECRET_KEY")

# ManifestStaticFilesStorage is recommended in production, to prevent
# outdated JavaScript / CSS assets being served from cache
# (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/6.0/ref/contrib/staticfiles/#manifeststaticfilesstorage
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"


ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# HTTPS settings
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')



# HSTS settings
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": "localhost",
        "PORT": "3306",
        "OPTIONS": {
            "sql_mode": "STRICT_TRANS_TABLES",
        },
    }
}

LOGGING = {
   # Version du format de configuration (obligatoire)
   'version': 1,
   # Garde les loggers Django existants actifs
   'disable_existing_loggers': False,
   # FORMATTERS : définissent la mise en forme des messages de log
   'formatters': {
       'verbose': {
           # Format détaillé : niveau, horodatage, module, message
           'format': '{levelname} {asctime} {module} {message}',
           # Style moderne avec accolades (recommandé)
           'style': '{',
       },
   },
   # HANDLERS : définissent où vont les logs (fichier, console, email, etc.)
   'handlers': {
       'file': {
           # Niveau minimum : warnings, erreurs et critiques
           'level': 'WARNING',
           # Handler avec rotation automatique pour éviter les gros fichiers
           'class': 'logging.handlers.RotatingFileHandler',
           # Nom du fichier de destination
           'filename': BASE_DIR / 'logs' / 'django.log',
           # Taille maximum par fichier : 5 MB
           'maxBytes': 1024*1024*5,
           # Nombre de fichiers de sauvegarde à conserver
           'backupCount': 5,
           # Utilise le formatter "verbose" défini ci-dessus
           'formatter': 'verbose',
       },
   },
   # LOGGERS : définissent qui envoie les logs et comment
   'loggers': {
       # Logger principal de Django (capture toutes les erreurs Django)
       'django': {
           # Utilise le handler "file" défini ci-dessus
           'handlers': ['file'],
           # Niveau du logger : accepte WARNING, ERROR et CRITICAL
           'level': 'WARNING',
           # Pas de propagation vers les loggers parents
           'propagate': False,
       },
   },
}
