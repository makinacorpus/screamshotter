import os
from pathlib import Path

SECRET_KEY = os.getenv('SECRET_KEY', 'booh!')
ALLOWED_HOSTS = [os.getenv('ALLOWED_HOSTS', '*')]

DEBUG = False

ROOT_URLCONF = 'screamshotter.urls'

INSTALLED_APPS = (
    'screamshot',
)

DISK_CACHE_SIZE = 50 * 1000

SCREAMSHOT_CONFIG = {
    'CLI_ARGS': ['--ssl-protocol=any',
                 '--disk-cache=true',
                 '--max-disk-cache-size=%s' % DISK_CACHE_SIZE],
    'TIMEOUT': os.getenv('SCREAMSHOT_TIMEOUT', 5000),
}

LOGGING = {
    'version': 1,
    'formatters': {
        'simple': {'format': '%(levelname)s %(asctime)s %(name)s %(message)s'},
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.getenv('LOG_FILE', 'screamshotter.log'),
        },
    },
    'loggers': {
        'screamshot': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

# Override with custom settings
custom_settings_file = Path('/opt/screamshotter/etc/local_settings.py')
if custom_settings_file.is_file():
    with custom_settings_file.open() as f:
        exec(f.read())
