from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Development-specific settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Enable Django Debug Toolbar for development
if DEBUG:
    INTERNAL_IPS = ['127.0.0.1']