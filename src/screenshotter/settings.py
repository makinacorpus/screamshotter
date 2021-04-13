import os

from django.conf import settings
from django.test.signals import setting_changed


DEFAULTS = {
    'PUPPETEER_JAVASCRIPT_FILEPATH': os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                                  'js', 'index.js'),
    'CHROMIUM_BROWSER_FILEPATH': 'chromium-browser',
    'NODE_BIN_PATH': 'node'
}


class APPSettings(object):
    """
    A settings object, that allows API settings to be accessed as properties.
    For example:
        from screenshotter.settings import app_settings
        print(app_settings.PUPPETEER_JAVASCRIPT_FILEPATH)
    """
    def __init__(self, defaults=None):
        self.defaults = defaults or DEFAULTS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        self._user_settings = getattr(settings, 'SCREENSHOTTER', {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid APP setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, '_user_settings'):
            delattr(self, '_user_settings')


app_settings = APPSettings(DEFAULTS)


def reload_app_settings(*args, **kwargs):
    setting = kwargs['setting']
    if setting == 'SCREENSHOTTER':
        app_settings.reload()


setting_changed.connect(reload_app_settings)
