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
    'birth',
    'sensorial',
    'community',
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
                'accounts.context_processors.map_aesthetic',
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

EMAIL_BACKEND = 'config.brevo_backend.BrevoEmailBackend'
BREVO_API_KEY = os.getenv('BREVO_API_KEY', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Endonautas <hola@endonautas.cl>')
PASSWORD_RESET_TIMEOUT = 3600  # 1 hora

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')

# ── Hotmart ────────────────────────────────────────────────────────────────────
# Variables de entorno a configurar en Railway / .env:
#   HOTMART_WEBHOOK_TOKEN       → "Seguridad del webhook" en Hotmart > Herramientas
#   HOTMART_OFFER_BASIC         → offer code del plan Navegante
#   HOTMART_OFFER_SEED          → offer code del plan Practicante
#   HOTMART_PACK_200/600/2000   → offer codes de los packs de fractones
HOTMART_WEBHOOK_TOKEN = os.getenv('HOTMART_WEBHOOK_TOKEN', '')

# Suscripciones: offer_code → plan interno
HOTMART_OFFER_PLAN_MAP = {
    os.getenv('HOTMART_OFFER_BASIC', ''):  'navegante',
    os.getenv('HOTMART_OFFER_SEED',  ''):  'practicante',
}

# Packs de fractones (pago único): offer_code → cantidad de fractones
HOTMART_PACK_MAP = {
    os.getenv('HOTMART_PACK_200',  ''): 200,
    os.getenv('HOTMART_PACK_600',  ''): 600,
    os.getenv('HOTMART_PACK_2000', ''): 2000,
}

# URLs de checkout
HOTMART_CHECKOUT_URLS = {
    'navegante':   os.getenv('HOTMART_CHECKOUT_BASIC',    '#'),
    'practicante': os.getenv('HOTMART_CHECKOUT_SEED',     '#'),
    'pack_200':    os.getenv('HOTMART_CHECKOUT_PACK_200',  '#'),
    'pack_600':    os.getenv('HOTMART_CHECKOUT_PACK_600',  '#'),
    'pack_2000':   os.getenv('HOTMART_CHECKOUT_PACK_2000', '#'),
}

DEEPSEEK_BASE_URL = 'https://api.deepseek.com'
DEEPSEEK_MODEL    = 'deepseek-chat'

# Blog de endonautas.cl — API para postulaciones desde mirrorwork
BLOG_PLATFORM_URL  = os.getenv('BLOG_PLATFORM_URL', 'https://endonautas.cl')
BLOG_SUBMIT_TOKEN  = os.getenv('BLOG_SUBMIT_TOKEN', '')

# Fractones mensuales por plan (se reemplazan cada ciclo, expiran)
TOKEN_PLANS = {
    'free':        {'monthly_fractones': 100,  'client_profiles': 0},
    'navegante':   {'monthly_fractones': 600,  'client_profiles': 0},
    'practicante': {'monthly_fractones': 3000, 'client_profiles': 10},
    'empresa':     {'monthly_fractones': 9999, 'client_profiles': 999},
}

# Costo en fractones por acción (0 = gratuito)
TOKEN_COSTS = {
    'espejo_exchange': 4,   # 1 mensaje + respuesta con Espejo
    'ai_insight':      20,  # insight IA tras completar test
    'report':          30,  # reporte agregado
}

# Fractones ganados por evento (se acumulan, nunca expiran)
FRACTON_REWARDS = {
    'test_completed':      8,
    'dimension_completed': 25,
    'streak_weekly':       15,
}
