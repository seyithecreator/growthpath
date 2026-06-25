"""
GrowthPath – Django 4.2 Settings
Personal Growth & Skill Development Decision-Support System
"""

import os
import dj_database_url
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production-please')

GROQ_API_KEY = config('GROQ_API_KEY', default='')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

# Allow Railway/Render domains automatically
_railway_domain = config('RAILWAY_PUBLIC_DOMAIN', default='')
if _railway_domain and _railway_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_railway_domain)

_render_domain = config('RENDER_EXTERNAL_HOSTNAME', default='')
if _render_domain and _render_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_domain)

CSRF_TRUSTED_ORIGINS = [
    f'https://{_railway_domain}' for _railway_domain in ALLOWED_HOSTS
    if _railway_domain not in ('localhost', '127.0.0.1')
]

# ─── Applications ────────────────────────────────────────────────────────────

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_extensions',

    # GrowthPath apps
    'apps.accounts',
    'apps.goals',
    'apps.skills',
    'apps.activities',
    'apps.recommendations',
    'apps.priorities',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'growthpath.urls'

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

WSGI_APPLICATION = 'growthpath.wsgi.application'

# ─── Database ────────────────────────────────────────────────────────────────

_database_url = config('DATABASE_URL', default='')
if _database_url:
    DATABASES = {'default': dj_database_url.parse(_database_url, conn_max_age=600)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='growthpath_db'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='postgres'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# ─── Auth & REST Framework ────────────────────────────────────────────────────

AUTH_USER_MODEL = 'accounts.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)
CORS_ALLOW_CREDENTIALS = True

# ─── Password Validation ─────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/goals/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# ─── Static & Media ──────────────────────────────────────────────────────────

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── Localisation ────────────────────────────────────────────────────────────

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Cache ───────────────────────────────────────────────────────────────────

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ─── Jazzmin Admin Theme ─────────────────────────────────────────────────────

JAZZMIN_SETTINGS = {
    'site_title': 'GrowthPath Admin',
    'site_header': 'GrowthPath',
    'site_brand': 'GrowthPath',
    'site_logo': None,
    'site_icon': None,
    'welcome_sign': 'Welcome to the GrowthPath Admin Panel',
    'copyright': 'GrowthPath',
    'search_model': ['accounts.User', 'goals.Goal'],
    'user_avatar': 'avatar',

    'topmenu_links': [
        {'name': 'Dashboard', 'url': '/goals/', 'new_window': False, 'icon': 'fas fa-home'},
        {'name': 'View Site', 'url': '/', 'new_window': True, 'icon': 'fas fa-globe'},
    ],

    'usermenu_links': [
        {'name': 'View Site', 'url': '/goals/', 'new_window': False, 'icon': 'fas fa-home'},
    ],

    'show_sidebar': True,
    'navigation_expanded': True,

    'order_with_respect_to': [
        'accounts', 'goals', 'skills', 'activities', 'recommendations', 'priorities',
    ],

    'icons': {
        'auth': 'fas fa-users-cog',
        'accounts.user': 'fas fa-user-graduate',
        'accounts.achievement': 'fas fa-trophy',
        'goals.goal': 'fas fa-bullseye',
        'goals.milestone': 'fas fa-flag-checkered',
        'skills.skilldomain': 'fas fa-layer-group',
        'skills.userskill': 'fas fa-brain',
        'skills.skillscorehistory': 'fas fa-chart-line',
        'activities.activitylog': 'fas fa-calendar-check',
        'activities.productivitysnapshot': 'fas fa-chart-bar',
        'recommendations.recommendation': 'fas fa-lightbulb',
        'priorities.priority': 'fas fa-sort-amount-down',
    },

    'default_icon_parents': 'fas fa-folder',
    'default_icon_children': 'fas fa-circle',

    'related_modal_active': True,
    'custom_css': None,
    'custom_js': 'js/admin_extras.js',
    'use_google_fonts_cdn': False,
    'show_ui_builder': False,

    'changeform_format': 'horizontal_tabs',
    'changeform_format_overrides': {
        'accounts.user': 'collapsible',
        'goals.goal': 'horizontal_tabs',
    },
}

JAZZMIN_UI_TWEAKS = {
    'navbar_small_text': False,
    'footer_small_text': False,
    'body_small_text': False,
    'brand_small_text': False,
    'brand_colour': 'navbar-purple',
    'accent': 'accent-purple',
    'navbar': 'navbar-dark',
    'no_navbar_border': True,
    'navbar_fixed': True,
    'layout_boxed': False,
    'footer_fixed': False,
    'sidebar_fixed': True,
    'sidebar': 'sidebar-dark-purple',
    'sidebar_nav_small_text': False,
    'sidebar_disable_expand': False,
    'sidebar_nav_child_indent': True,
    'sidebar_nav_compact_style': False,
    'sidebar_nav_legacy_style': False,
    'sidebar_nav_flat_style': False,
    'theme': 'darkly',
    'dark_mode_theme': 'darkly',
    'button_classes': {
        'primary': 'btn-primary',
        'secondary': 'btn-secondary',
        'info': 'btn-info',
        'warning': 'btn-warning',
        'danger': 'btn-danger',
        'success': 'btn-success',
    },
}

# ─── ML Engine Config ────────────────────────────────────────────────────────

RECOMMENDATION_ENGINE = {
    'MAX_RECOMMENDATIONS': 5,
    'PRIORITY_WEIGHTS': {
        'deadline_urgency': 0.40,
        'goal_importance': 0.35,
        'completion_rate': 0.25,
    },
    'MIN_ACTIVITY_LOGS': 3,   # min logs before personalised recs kick in
    'RETRAIN_INTERVAL_DAYS': 7,
}
