from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-cambiar-en-produccion')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
# Railway injects RAILWAY_PUBLIC_DOMAIN automatically
_railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN', '')
if _railway_domain and _railway_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_railway_domain)

CSRF_TRUSTED_ORIGINS = [
    f'https://{h}' for h in ALLOWED_HOSTS if h not in ('localhost', '127.0.0.1', 'testserver', '')
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'tokens',
    'psychometrics',
    'mirror',
    'practitioners',
    'reports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/db.sqlite3')
DATABASES = {'default': dj_database_url.parse(DATABASE_URL)}

AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend']

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Production security (applied when DEBUG=False)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = False  # Railway/Cloudflare ya terminan SSL externamente
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')

# ── Hotmart ────────────────────────────────────────────────────────────────────
# Set these in Railway / .env after creating the products in Hotmart.
# HOTMART_WEBHOOK_TOKEN  → "Seguridad del webhook" en Hotmart > Herramientas > Webhook
# HOTMART_PRODUCT_ID_*  → ID numérico del producto en Hotmart
HOTMART_WEBHOOK_TOKEN = os.getenv('HOTMART_WEBHOOK_TOKEN', '')
# Offer codes (off=xxxx en la URL de checkout) → plan interno
HOTMART_OFFER_PLAN_MAP = {
    os.getenv('HOTMART_OFFER_BASIC', ''):  'navegante',
    os.getenv('HOTMART_OFFER_SEED', ''): 'practicante',
}
# Checkout URLs
HOTMART_CHECKOUT_URLS = {
    'navegante':   os.getenv('HOTMART_CHECKOUT_BASIC', '#'),
    'practicante': os.getenv('HOTMART_CHECKOUT_SEED', '#'),
}
DEEPSEEK_BASE_URL = 'https://api.deepseek.com'
DEEPSEEK_MODEL = 'deepseek-chat'

TOKEN_PLANS = {
    'free':        {'monthly_tokens': 50,  'client_profiles': 0,  'tokens_per_client': 0},
    'navegante':   {'monthly_tokens': 400, 'client_profiles': 0,  'tokens_per_client': 0},
    'practicante': {'monthly_tokens': 600, 'client_profiles': 10, 'tokens_per_client': 150},
    'empresa':     {'monthly_tokens': 9999,'client_profiles': 999,'tokens_per_client': 300},
}

TOKEN_COSTS = {
    'psychometric_test': 0,
    'ai_analysis':       5,
    'mirror_session':    10,
    'journey_session':   15,
    'cnv_roleplay':      8,
    'report_generate':   3,
}
