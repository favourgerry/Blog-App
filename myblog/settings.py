"""
Django settings for myblog project.
"""

from pathlib import Path
import os
from datetime import timedelta # Needed for session settings

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ✅ Use environment variables
# SECRET_KEY is crucial for security. Use a good default for local development.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key-for-dev-only')
# DEBUG should be False in production
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# ✅ Allow all hosts temporarily, or set via environment variable
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# ------------------------------------
# Application definition
# ------------------------------------
INSTALLED_APPS = [
    # 1. JAZZMIN MUST BE FIRST
    'jazzmin',
    
    # 2. Django's core admin app
    'django.contrib.admin',
    
    # Standard Django apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Your project apps
    'main',  # Contains your Client, Project, Task, Invoice, etc. models
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise must be right after SecurityMiddleware
    'whitenoise.middleware.WhiteNoiseMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'myblog.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # optional global templates folder
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

WSGI_APPLICATION = 'myblog.wsgi.application'

# Database
# Use a production database like Postgres via an environment variable in production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ------------------------------------
# Internationalization & Time
# ------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ------------------------------------
# Static files (for production deployment)
# ------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------------------------
# JAZZMIN SETTINGS
# ------------------------------------
JAZZMIN_SETTINGS = {
    # Title of the window tab
    "site_title": "PMS Admin", 

    # Header on the login screen and dashboard
    "site_header": "Project Management System",

    # Logo, etc.
    "site_logo_classes": "img-circle",
    "welcome_sign": "Welcome to the PMS Admin Interface",

    # Sidebar menu configuration for your models
    "navigation_expanded": True, # Keep the menu open by default
    "show_sidebar": True,
    "sidebars": {
        "Clients & Projects": [
            "main.Client",
            "main.Project",
        ],
        "Project Management": [
            "main.Task",
            "main.Note",
            "main.ProjectFile",
        ],
        "Financials": [
            "main.Invoice",
            "main.Payment",
            "main.Expense",
        ],
        "Access & Users": [
            "auth.User",
            "auth.Group",
        ]
    },
    
    # Optional: Light/Dark Mode toggle
    "body_classes": "sidebar-mini",
    "usermenu_links": [
        {"name": "Support", "url": "https://github.com/farridav/django-jazzmin/issues", "new_window": True},
    ],
    "show_ui_builder": False, # Set to True if you want to allow users to customize theme locally
}

# ------------------------------------
# JAZZMIN UI Theme
# ------------------------------------
JAZZMIN_UI_TWEAKS = {
    "theme": "united", # A modern, professional theme
    "navbar_fixed": True,
    "sidebar_fixed": True,
}
