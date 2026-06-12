from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-cambiar-en-produccion')
DEBUG = os.getenv('DEBUG', 'True').lower() in ['true', '1', 'yes', 'y']
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
# Railway injects RAILWAY_PUBLIC_DOMAIN automatically
_railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN', '')
if _railway_domain and _railway_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_railway_domain)
# Custom domain (Cloudflare DNS → Railway)
for _custom in ['endonautas.cl', 'www.endonautas.cl']:
    if _custom not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_custom)

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
    'django.contrib.sitemaps',

    # Core Endonautas apps
    'accounts',
    'tokens',
    'psychometrics',
    'mirror',
    'practitioners',
    'reports',
    'birth',
    'sensorial',
    'community',

    # Editorial & Marketing apps
    'home',
    'blog',
    'search',
    'centro',
    'crm',
    'post_office',
    'django_celery_results',
    'django_celery_beat',

    # Wagtail CMS
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail.contrib.settings',
    'wagtail.contrib.sitemaps',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail',
    'modelcluster',
    'taggit',
    'wagtailseo',
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
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
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

MEDIA_ROOT = BASE_DIR / 'media'

# ── Configuración de Almacenamiento (Cloudflare R2 / Local fallback) ──
if os.getenv('AWS_ACCESS_KEY_ID'):
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "access_key": os.getenv("AWS_ACCESS_KEY_ID"),
                "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
                "bucket_name": os.getenv("AWS_STORAGE_BUCKET_NAME"),
                "endpoint_url": os.getenv("AWS_S3_ENDPOINT_URL"),
                "custom_domain": os.getenv("AWS_S3_CUSTOM_DOMAIN"),
                "region_name": "auto",  # R2 requiere "auto"
                "signature_version": "s3v4",
                "file_overwrite": False,
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    # En producción usando R2, los media apuntan al dominio público del CDN/R2
    MEDIA_URL = f"https://{os.getenv('AWS_S3_CUSTOM_DOMAIN')}/"
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    MEDIA_URL = '/media/'



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

EMAIL_BACKEND = 'post_office.EmailBackend'
BREVO_API_KEY = os.getenv('BREVO_API_KEY', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Endonautas <hola@endonautas.cl>')
PASSWORD_RESET_TIMEOUT = 3600  # 1 hora

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')

# ── Mercado Pago ───────────────────────────────────────────────────────────────
# Variables de entorno a configurar en Railway / .env:
#   MP_ACCESS_TOKEN    → Access Token de Mercado Pago (developers.mercadopago.com)
#   MP_PUBLIC_KEY      → Public Key (para el checkout en el frontend, si se usa)
#   MP_WEBHOOK_SECRET  → Secret para validar webhooks (opcional pero recomendado)
MP_ACCESS_TOKEN  = os.getenv('MP_ACCESS_TOKEN', '')
MP_PUBLIC_KEY    = os.getenv('MP_PUBLIC_KEY', '')
MP_WEBHOOK_SECRET = os.getenv('MP_WEBHOOK_SECRET', '')

# Packs de fractones: slug → {fractones, precio CLP, nombre}
# El slug se usa como referencia interna para identificar la compra
MP_PACKS = {
    'starter':    {'fractones': 10,  'price': 1990,  'name': 'Starter'},
    'explorador': {'fractones': 25,  'price': 3990,  'name': 'Explorador'},
    'viajero':    {'fractones': 60,  'price': 7990,  'name': 'Viajero'},
}

# ── PayPal ─────────────────────────────────────────────────────────────────────
# Variables de entorno a configurar en Railway / .env:
#   PAYPAL_CLIENT_ID     → Client ID de tu app en developer.paypal.com
#   PAYPAL_SECRET        → Secret de tu app
#   PAYPAL_WEBHOOK_ID    → ID del webhook configurado en PayPal
PAYPAL_CLIENT_ID  = os.getenv('PAYPAL_CLIENT_ID', '')
PAYPAL_SECRET     = os.getenv('PAYPAL_SECRET', '')
PAYPAL_WEBHOOK_ID = os.getenv('PAYPAL_WEBHOOK_ID', '')

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

# ── Dynamic Postgres Support ───────────────────────────────────────────────
if DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
    INSTALLED_APPS.append('django.contrib.postgres')

# ── Wagtail CMS settings ───────────────────────────────────────────────────
WAGTAIL_SITE_NAME = 'Endonautas'
WAGTAILADMIN_BASE_URL = os.getenv('WAGTAILADMIN_BASE_URL', 'https://endonautas.cl')
WAGTAILSEARCH_BACKENDS = {
    'default': {'BACKEND': 'wagtail.search.backends.database'}
}
WAGTAILDOCS_EXTENSIONS = ['csv', 'docx', 'pdf', 'pptx', 'txt', 'xlsx']
WAGTAILDOCS_MAX_UPLOAD_SIZE = 10 * 1024 * 1024

# ── django-post-office (Email queue manager) ───────────────────────────────
POST_OFFICE = {
    'BACKENDS': {
        'default': 'django.core.mail.backends.console.EmailBackend' if DEBUG else 'config.brevo_backend.BrevoEmailBackend',
    },
    'DEFAULT_PRIORITY': 'medium',
    'BATCH_SIZE': 20,
    'LOG_LEVEL': 1,
    'CELERY_ENABLED': True,
    'DEFAULT_FROM_EMAIL': DEFAULT_FROM_EMAIL,
}

# ── Hotmart Checkouts ──────────────────────────────────────────────────────
HOTMART_CHECKOUT_URLS = {
    'navegante':   os.getenv('HOTMART_CHECKOUT_NAVEGANTE', os.getenv('HOTMART_CHECKOUT_BASIC', '#')),
    'practicante': os.getenv('HOTMART_CHECKOUT_PRACTICANTE', os.getenv('HOTMART_CHECKOUT_SEED', '#')),
}

# ── Celery Config ──────────────────────────────────────────────────────────
CELERY_BROKER_URL = os.getenv("REDIS_URL", "django-db://")
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Santiago"
