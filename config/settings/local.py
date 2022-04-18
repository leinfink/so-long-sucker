from .base import *

SECRET_KEY = get_secret('DEBUG_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = "config.asgi.application"

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': str(BASE_DIR / 'db.sqlite3'),
    }
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# django channels
# use Redis in production use
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
    # "default": {
    #     "BACKEND": "channels_redis.core.RedisChannelLayer",
    #     "CONFIG": {
    #         "hosts": [("127.0.0.1", 6379)],
    #     },
    # }
}

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379',
#     }
# }

# SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

PRODUCTION_WEBSOCKET_URLS = False
REDIS_HOST = "localhost"
REDIS_UNIX = False
