import json
import os
import signal
import subprocess
from tempfile import NamedTemporaryFile

from screamshotter import __version__
from .exceptions import ScreenshotterException
from .settings import app_settings

from django.conf import settings


def take_screenshot(url, width=1920, height=1080, waitfor='body', wait_selectors=(),
                    selector='body', wait_seconds=1, timeout=settings.TIMEOUT, forward_headers=None,
                    screamshotter_css_class='screamshot'):
    if forward_headers is None:
        forward_headers = dict()

    # We send sentry informations and version : when we use screamshotter as a package, informations are in settings only
    with NamedTemporaryFile(suffix='.png') as screenshot_file:
        command = subprocess.run([
            os.getenv('NODE_BIN_PATH', 'node'),
            app_settings.PUPPETEER_JAVASCRIPT_FILEPATH,
            '--version',
            __version__,
            '--sentrydsn',
            settings.SENTRY_DSN or "",
            '--sentryenv',
            settings.SENTRY_ENVIRONMENT or "",
            '--sentrytracerate',
            f'{settings.SENTRY_TRACE_SAMPLE}',
            '--url',
            url,
            '--path',
            screenshot_file.name,
            '--selector',
            selector,
            '--vwidth',
            f'{width}',
            '--vheight',
            f'{height}',
            '--waitseconds',
            f'{wait_seconds * 1000}',
            '--waitselectors',
            json.dumps(wait_selectors),
            '--waitfor',
            waitfor,
            '--timeout',
            f'{timeout * 1000}',
            '--screamshottercssclass',
            screamshotter_css_class,
            '--headers',
            json.dumps(forward_headers),
        ], stderr=subprocess.PIPE, env=os.environ, preexec_fn=os.setsid)

        if command.stderr:
            raise ScreenshotterException(command.stderr.decode())

        os.killpg(os.getpgid(command.pid), signal.SIGTERM)
        return screenshot_file.read()
