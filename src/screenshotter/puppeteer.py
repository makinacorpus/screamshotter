import json
import subprocess
from tempfile import NamedTemporaryFile

from .exceptions import ScreenshotterException
from .settings import app_settings


def take_screenshot(url, viewport_width=1920, viewport_height=1080, wait_selectors=(),
                    selector='body', wait_seconds=1, forward_headers=None):
    if forward_headers is None:
        forward_headers = dict()

    screenshot_file = NamedTemporaryFile(suffix='.png')

    with open(screenshot_file.name, 'w+b'):
        command = subprocess.run([
            'node',
            app_settings.PUPPETEER_JAVASCRIPT_FILEPATH,
            '--url',
            url,
            '--path',
            screenshot_file.name,
            '--selector',
            selector,
            '--vwidth',
            f'{viewport_width}',
            '--vheight',
            f'{viewport_height}',
            '--waitseconds',
            f'{wait_seconds * 1000}',
            '--waitselectors',
            json.dumps(wait_selectors),
            '--headers',
            json.dumps(forward_headers),
        ], stderr=subprocess.PIPE)

        if command.stderr:
            raise ScreenshotterException(command.stderr.decode())

    with open(screenshot_file.name, 'rb') as screenshot_data:
        return screenshot_data.read()
