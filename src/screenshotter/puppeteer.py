import json
import os
import subprocess
from tempfile import NamedTemporaryFile

from .exceptions import ScreenshotterException
from .settings import app_settings


def take_screenshot(url, width=1920, height=1080, waitfor='body', wait_selectors=(),
                    selector='body', wait_seconds=1, forward_headers=None):
    if forward_headers is None:
        forward_headers = dict()

    with NamedTemporaryFile(suffix='.png') as screenshot_file:
        command = subprocess.run([
            os.getenv('NODE_BIN_PATH', 'node'),
            app_settings.PUPPETEER_JAVASCRIPT_FILEPATH,
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
            '--headers',
            json.dumps(forward_headers),
        ], stderr=subprocess.PIPE, env=os.environ)

        if command.stderr:
            raise ScreenshotterException(command.stderr.decode())

        return screenshot_file.read()
