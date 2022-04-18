from .base import *

SECRET_KEY = get_secret('DEBUG_KEY')

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / 'db.sqlite3'),
    }
}

ROOT_URLCONF = 'config.urls_local'

PRODUCTION_WEBSOCKET_URLS = False
REDIS_HOST = "localhost"
REDIS_UNIX = False

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
#STATIC_ROOT = '/static'

# django channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    }
}

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': 'unix:///home/chezhans/.redis/sock:6379',
#     }
# }

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True
# SECURE_SSL_REDIRECT = True

SSL_WEBSOCKETS = False
