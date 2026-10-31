from datetime import timedelta
import os
from pathlib import Path
from datetime import timedelta
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('SECRET_KEY', 'changeme')
DEBUG = bool(int(os.environ.get("DEBUG", 0)))

# ALLOWED_HOSTS = []
ALLOWED_HOSTS = ['api-finance.oneapp.ph',
                 'localhost',
                 '127.0.0.1',
                 'dolphin-app-yqjv9.ondigitalocean.app',
                 'oog-finance.oneapp.ph']
ALLOWED_HOSTS.extend(
    filter(
        None,
        os.environ.get('ALLOWED_HOSTS', '').split(','),
    )
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'channels',
    'django_celery_beat',

    'rest_framework',
    'core',
    'user',
    'users',
    'administration',
    # 'reports',
    'reports.apps.ReportsConfig'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

ASGI_APPLICATION = "app.asgi.application"
WSGI_APPLICATION = 'app.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('DB_HOST'),
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASS'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'UserAttributeSimilarityValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'MinimumLengthValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'CommonPasswordValidator'
    },
    {
        'NAME': 'django.contrib.auth.password_validation.'
        'NumericPasswordValidator'
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Hong_Kong'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/static/'
MEDIA_URL = '/static/media/'

MEDIA_ROOT = '/vol/web/media'
STATIC_ROOT = '/vol/web/static'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.User'

SIMPLE_JWT = {
    'AUTH_COOKIE': 'access_token',
     "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6379)],
        },
    },
}

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.'
    'pagination.PageNumberPagination',
    'PAGE_SIZE': 2,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'app.authentication.CookieJWTAuthentication',
    ],
    
}

X_FRAME_OPTIONS = 'SAMEORIGIN'

SPECTACULAR_SETTINGS = {
    'COMPONENT_SPLIT_REQUEST': True,
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "https://dolphin-app-yqjv9.ondigitalocean.app",
    "https://api-finance.oneapp.ph",
    "https://oog-finance.oneapp.ph"
]

CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "https://dolphin-app-yqjv9.ondigitalocean.app",
    "https://api-finance.oneapp.ph",
    "https://oog-finance.oneapp.ph"
]

CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
