from .base import *

SECRET_KEY = get_secret('PRODUCTION_SECRET_KEY')

DEBUG = False

ALLOWED_HOSTS = [get_secret('ALLOWED_HOST')]

ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / 'db.sqlite3'),
    }
}

ROOT_URLCONF = 'config.urls_production'

PRODUCTION_WEBSOCKET_URLS = True

REDIS_UNIX_PATH = get_secret('REDIS_UNIX_PATH')
REDIS_UNIX = True

STATIC_URL = get_secret('STATIC_URL')
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = get_secret('STATIC_ROOT')

# django channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [get_secret('CHANNEL_REDIS_HOST')]
        },
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True
