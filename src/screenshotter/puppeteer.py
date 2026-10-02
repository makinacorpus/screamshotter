import json
import os
import signal
import subprocess
import time
from tempfile import NamedTemporaryFile

from screamshotter import __version__
from .exceptions import ScreenshotterException
from .settings import app_settings

from django.conf import settings


def _reap_zombies():
    try:
        while True:
            pid, _ = os.waitpid(-1, os.WNOHANG)
            if pid <= 0:
                break
    except (ChildProcessError, OSError):
        pass


def _preexec_fn():
    # Make child process group leader so entire group can be killed together
    os.setsid()
    try:
        import ctypes
        libc = ctypes.CDLL('libc.so.6')
        # PR_SET_PDEATHSIG = 1: deliver SIGTERM to child if parent process dies
        libc.prctl(1, signal.SIGTERM)
    except Exception:
        pass


def take_screenshot(url, width=1920, height=1080, waitfor='body', wait_selectors=(),
                    selector='body', wait_seconds=1, timeout=settings.TIMEOUT, forward_headers=None,
                    screamshotter_css_class='screamshot'):
    if forward_headers is None:
        forward_headers = dict()

    _reap_zombies()

    # Calculate overall subprocess timeout (giving Node time to finish its internal timeout first)
    try:
        timeout_val = float(timeout)
    except (TypeError, ValueError):
        timeout_val = 60.0
    node_timeout = max(timeout_val + 15.0, 5.0)

    # We send sentry informations and version : when we use screamshotter as a package, informations are in settings only
    with NamedTemporaryFile(suffix='.png') as screenshot_file:
        proc = subprocess.Popen([
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
            f'{int(timeout_val * 1000)}',
            '--screamshottercssclass',
            screamshotter_css_class,
            '--headers',
            json.dumps(forward_headers),
            '--external_puppeteer',
            f"{os.getenv('EXTERNAL_PUPPETEER', '')}"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ, preexec_fn=_preexec_fn)

        try:
            stdout, stderr = proc.communicate(timeout=node_timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                time.sleep(0.2)
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                proc.communicate(timeout=2)
            except Exception:
                pass
            raise ScreenshotterException(f"Screenshot process timed out after {node_timeout}s")
        except Exception:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                proc.communicate(timeout=1)
            except Exception:
                pass
            raise
        finally:
            _reap_zombies()

        if proc.returncode != 0:
            raise ScreenshotterException(stderr.decode('utf-8', errors='replace'))

        if not os.path.exists(screenshot_file.name) or os.path.getsize(screenshot_file.name) == 0:
            err_msg = stderr.decode('utf-8', errors='replace').strip()
            raise ScreenshotterException(err_msg or "Empty screenshot generated")

        return screenshot_file.read()
