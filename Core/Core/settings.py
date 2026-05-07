"""
Django settings for Core project.
"""

import os
from datetime import timedelta
from pathlib import Path

from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent
EXAMINER_MODE = config('FITTRACK_EXAMINER_MODE', default=False, cast=bool)
DATA_DIR = Path(config('FITTRACK_DATA_DIR', default=str(BASE_DIR))).resolve()
STATIC_ROOT = DATA_DIR / 'staticfiles'


def env_or_default(name, default=''):
    return config(name, default=default)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env_or_default('DJANGO_SECRET_KEY', 'fittrack-examiner-secret-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DJANGO_DEBUG', default=EXAMINER_MODE, cast=bool)

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
if EXAMINER_MODE:
    ALLOWED_HOSTS.append('0.0.0.0')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    #my apps
    'users',
    'exercises',
    'nutrition',
    #django socials
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

SITE_ID=1

#AUTHENTICATION SETTINGS
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIALACCOUNT_LOGIN_ON_GET = True
LOGIN_URL = 'login_user'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT = 'login_user'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES':(
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication'#for browsable API/tests
    ),
    'DEFAULT_PERMISSION_CLASSES':(
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
}

SIMPLE_JWT={
    'ACCESS_TOKEN_LIFETIME':timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME':timedelta(days=7),
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'Core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR/ 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

if EXAMINER_MODE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': DATA_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': env_or_default('MYSQL_DATABASE', 'fitness'),
            'USER': env_or_default('MYSQL_USER', 'root'),
            'PASSWORD': env_or_default('MYSQL_PASSWORD', 'password'),
            'HOST': env_or_default('MYSQL_HOST', 'localhost'),
            'PORT': env_or_default('MYSQL_PORT', '3306'),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = DATA_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

google_client_id = env_or_default('GOOGLE_CLIENT_ID')
google_client_secret = env_or_default('GOOGLE_CLIENT_SECRET')
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
            'prompt': 'select_account'
        },
        'APP': {
            'client_id': google_client_id,
            'secret': google_client_secret,
            'key': ''
        }
    }
}

if not EXAMINER_MODE:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_ACCESS_KEY_ID = env_or_default("CLOUDFLARE_R2_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env_or_default("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env_or_default("CLOUDFLARE_R2_BUCKET_NAME")
    cloudflare_account_id = env_or_default('CLOUDFLARE_R2_ACCOUNT_ID')
    AWS_S3_ENDPOINT_URL = (
        f"https://{cloudflare_account_id}.r2.cloudflarestorage.com"
        if cloudflare_account_id else ''
    )
else:
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    AWS_ACCESS_KEY_ID = ''
    AWS_SECRET_ACCESS_KEY = ''
    AWS_STORAGE_BUCKET_NAME = ''
    AWS_S3_ENDPOINT_URL = ''

R2_PUBLIC_BASE_URL = env_or_default(
    "CLOUDFLARE_R2_PUBLIC_BASE_URL",
    "https://pub-a3e3770ca86b453197bf4160321b1b0a.r2.dev"
).rstrip("/")
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=86400",
}

USDA_API_KEY = env_or_default("USDA_API_KEY")
USDA_BASE_URL = 'https://api.nal.usda.gov/fdc/v1'
