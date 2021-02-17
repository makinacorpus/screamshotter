from . import *  # NOQA

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-dev-dev-dev-dev')

DEBUG = True

ALLOWED_HOSTS = [
    '*',
]

INSTALLED_APPS.append('debug_toolbar')
MIDDLEWARE += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

INTERNAL_IPS = type(str('c'), (), {'__contains__': lambda *a: True})()
