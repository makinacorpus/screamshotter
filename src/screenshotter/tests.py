import importlib
import os
import subprocess
import sys
from tempfile import TemporaryDirectory
import types
from unittest import skipIf
from unittest.mock import MagicMock, patch

from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
import magic
from PIL import Image
from rest_framework.serializers import Serializer
from rest_framework.test import APISimpleTestCase

from .exceptions import ScreenshotterException
from .puppeteer import _preexec_fn, _reap_zombies, take_screenshot
from .renderers import ScreamBrowsableAPIRenderer
from .serializer import ScreenshotSerializer
from .views import ScreenshotAPIView

temp_dir = TemporaryDirectory()


class CaptureTestCase(SimpleTestCase):
    @override_settings(MEDIA_ROOT=temp_dir.name)
    def test_capture_mime(self):
        png = take_screenshot('https://www.google.fr')

        cfile = ContentFile(content=png)
        default_storage.save(name='test_capture_mime.png', content=cfile)

        self.assertNotEqual(cfile.size, 0)
        mime = magic.from_buffer(default_storage.open('test_capture_mime.png').read(), mime=True)
        self.assertEqual(mime, "image/png", )

    @override_settings(MEDIA_ROOT=temp_dir.name)
    def test_capture_size(self):
        png = take_screenshot('https://www.google.fr', width=1280, height=720)

        cfile = ContentFile(content=png)
        default_storage.save(name='test_capture_size.png', content=cfile)

        image = Image.open(default_storage.path('test_capture_size.png'))

        self.assertEqual(image.width, 1280)
        self.assertEqual(image.height, 720)

    def test_bad_dns(self):
        with self.assertRaises(ScreenshotterException):
            take_screenshot('https://cccccc')

    def test_view_has_get_serializer(self):
        view = ScreenshotAPIView()

        self.assertTrue(hasattr(view, 'get_serializer'))
        self.assertTrue(isinstance(view.get_serializer(), Serializer))

    @override_settings(SCREENSHOTTER={'PUPPETEER_JAVASCRIPT_FILEPATH': 'none'})
    def test_bad_script_path(self):
        with self.assertRaises(ScreenshotterException):
            take_screenshot('https://www.google.fr')

    @skipIf(settings.TIMEOUT != 0.001, "skip if timeout is not 1ms")
    @override_settings(MEDIA_ROOT=temp_dir.name)
    def test_timeout_screenshot(self):
        # We show that we can change timeout value. It's so small, this takes more than 1ms to generate the screenshot.
        # => It fails
        with self.assertRaisesRegex(ScreenshotterException, 'TimeoutError: Navigation timeout of 1 ms exceeded'):
            take_screenshot('https://www.google.fr')

    @override_settings(SCREENSHOTTER={'BAD_SETTINGS': 'none'})
    def test_bad_settings(self):
        with self.assertRaises(AttributeError):
            from .settings import app_settings
            bool(app_settings.BAD_SETTINGS)


class CaptureApiTestCase(APISimpleTestCase):
    def test_api_good_request_json(self):
        serializer = ScreenshotSerializer()
        data = serializer.data
        data['url'] = "https://www.google.fr"

        response = self.client.post(reverse('screenshotter:screenshot') + '?format=json', data=data)
        data = response.json()
        self.assertEqual(response.status_code, 200, data)
        self.assertIn('base64', data)

    def test_api_good_get_request_json(self):
        response = self.client.get(reverse('screenshotter:screenshot') + '?format=json&url=https://www.google.fr')
        data = response.json()
        self.assertEqual(response.status_code, 200, data)
        self.assertIn('base64', data)

    def test_api_bad_request(self):
        serializer = ScreenshotSerializer()
        response = self.client.post(reverse('screenshotter:screenshot') + '?format=json', data=serializer.data)
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertIn('url', data)
        self.assertEqual(['This field may not be blank.'], data['url'])

    def test_api_bad_get_request(self):
        response = self.client.get(reverse('screenshotter:screenshot') + '?format=json')
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertIn('url', data)
        self.assertEqual(['This field is required.'], data['url'])

    def test_api_wrong_response(self):
        serializer = ScreenshotSerializer()
        data = serializer.data
        data['url'] = "https://dodo.kiik"
        response = self.client.post(reverse('screenshotter:screenshot') + '?format=json', data=data)
        self.assertEqual(response.status_code, 500, response.json())

    def test_api_browsable(self):
        serializer = ScreenshotSerializer()
        data = serializer.data
        data['url'] = "https://www.google.fr"

        response = self.client.post(reverse('screenshotter:screenshot') + '?format=api', data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<html>', response.content)
        # check default renderer is json in browsable api (response in "base64": "xxx" format)
        self.assertIn(b'&quot;base64&quot;', response.content)

    def test_png_default(self):
        serializer = ScreenshotSerializer()
        data = serializer.data
        data['url'] = "https://www.google.fr"

        response = self.client.post(reverse('screenshotter:screenshot'), data=data)
        self.assertEqual(response.status_code, 200)
        mime = magic.from_buffer(response.content, mime=True)
        self.assertEqual(mime, "image/png")


class WebPageTestCase(APISimpleTestCase):
    def test_web_page_get_empty_form(self):
        response = self.client.get(reverse('screenshotter:screenshot'), HTTP_ACCEPT='text/html')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Take a Screenshot', response.content)
        self.assertIn(b'name="url"', response.content)
        self.assertIn(b'name="width"', response.content)
        self.assertIn(b'name="height"', response.content)
        self.assertNotIn(b'This field is required.', response.content)

    def test_web_page_get_format_api(self):
        response = self.client.get(reverse('screenshotter:screenshot') + '?format=api')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Take a Screenshot', response.content)
        self.assertIn(b'name="url"', response.content)
        self.assertNotIn(b'This field is required.', response.content)

    def test_web_page_test_endpoint(self):
        response = self.client.get(reverse('screenshotter:screenshot-test'), HTTP_ACCEPT='text/html')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Take a Screenshot', response.content)
        self.assertIn(b'name="url"', response.content)

    def test_web_page_post_success_displays_image(self):
        with patch('screenshotter.views.take_screenshot', return_value=b'test-fake-png-content'):
            response = self.client.post(
                reverse('screenshotter:screenshot') + '?format=api',
                data={'url': 'https://www.google.fr'}
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Captured Screenshot', response.content)
            self.assertIn(b'data:image/png;base64,', response.content)
            # base64 of 'test-fake-png-content' is 'dGVzdC1mYWtlLXBuZy1jb250ZW50'
            self.assertIn(b'dGVzdC1mYWtlLXBuZy1jb250ZW50', response.content)
            self.assertIn(b'download="screenshot.png"', response.content)

    def test_web_page_get_with_url_displays_image(self):
        with patch('screenshotter.views.take_screenshot', return_value=b'test-fake-png-content'):
            response = self.client.get(
                reverse('screenshotter:screenshot') + '?format=api&url=https://www.google.fr'
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Captured Screenshot', response.content)
            self.assertIn(b'data:image/png;base64,', response.content)
            self.assertIn(b'dGVzdC1mYWtlLXBuZy1jb250ZW50', response.content)

    def test_web_page_post_validation_error(self):
        response = self.client.post(
            reverse('screenshotter:screenshot') + '?format=api',
            data={'url': ''}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Take a Screenshot', response.content)
        self.assertIn(b'This field may not be blank.', response.content)
        self.assertNotIn(b'Captured Screenshot', response.content)

    def test_web_page_post_capture_error(self):
        with patch('screenshotter.views.take_screenshot', side_effect=Exception('Custom Puppeteer failure')):
            response = self.client.post(
                reverse('screenshotter:screenshot') + '?format=api',
                data={'url': 'https://www.google.fr'}
            )
            self.assertEqual(response.status_code, 500)
            self.assertIn(b'Screenshot generation failed', response.content)
            self.assertIn(b'Custom Puppeteer failure', response.content)

    def test_renderer_get_context_dict_base64(self):
        renderer = ScreamBrowsableAPIRenderer()
        resp = type('Response', (), {'status_code': 200, 'status_text': 'OK', 'items': lambda self: []})()
        view = ScreenshotAPIView()
        request = self.client.get('/?format=api').wsgi_request
        drf_request = view.initialize_request(request)
        view.setup(drf_request)
        renderer.accepted_media_type = 'text/html'
        renderer.renderer_context = {'view': view, 'request': drf_request, 'response': resp}

        context = renderer.get_context({'base64': 'custom-base64-string'}, 'text/html', renderer.renderer_context)
        self.assertEqual(context.get('image_base64'), 'custom-base64-string')

    def test_renderer_get_context_dict_errors(self):
        renderer = ScreamBrowsableAPIRenderer()
        resp = type('Response', (), {'status_code': 500, 'status_text': 'Internal Server Error', 'items': lambda self: []})()
        view = ScreenshotAPIView()
        request = self.client.get('/?format=api').wsgi_request
        drf_request = view.initialize_request(request)
        view.setup(drf_request)
        renderer.accepted_media_type = 'text/html'
        renderer.renderer_context = {'view': view, 'request': drf_request, 'response': resp}

        context = renderer.get_context({'errors': 'custom-error-string'}, 'text/html', renderer.renderer_context)
        self.assertEqual(context.get('capture_errors'), 'custom-error-string')

    def test_view_get_serializer_unbound(self):
        view = ScreenshotAPIView()
        serializer = view.get_serializer()
        self.assertFalse(hasattr(serializer, 'initial_data'))

    def test_view_get_serializer_with_explicit_data(self):
        view = ScreenshotAPIView()
        serializer = view.get_serializer(data={'url': 'https://explicit.com'})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['url'], 'https://explicit.com')


class ProcessManagementTestCase(SimpleTestCase):
    def test_reap_zombies_normal(self):
        with patch('os.waitpid', side_effect=[(1234, 0), (0, 0)]):
            _reap_zombies()

    def test_reap_zombies_child_process_error(self):
        with patch('os.waitpid', side_effect=ChildProcessError):
            _reap_zombies()

    def test_reap_zombies_os_error(self):
        with patch('os.waitpid', side_effect=OSError):
            _reap_zombies()

    def test_preexec_fn(self):
        with patch('os.setsid') as mock_setsid, patch('ctypes.CDLL') as mock_cdll:
            _preexec_fn()
            mock_setsid.assert_called_once()
            mock_cdll.assert_called_once_with('libc.so.6')

    def test_preexec_fn_exception(self):
        with patch('os.setsid'), patch('ctypes.CDLL', side_effect=Exception("libc error")):
            _preexec_fn()

    def test_apps_ready(self):
        config = apps.get_app_config('screenshotter')
        with patch('ctypes.CDLL') as mock_cdll:
            config.ready()
            mock_cdll.assert_called_once_with('libc.so.6')

    def test_apps_ready_exception(self):
        config = apps.get_app_config('screenshotter')
        with patch('ctypes.CDLL', side_effect=Exception("error")):
            config.ready()

    def test_take_screenshot_invalid_timeout(self):
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = MagicMock()
            mock_proc.returncode = 0

            def fake_communicate(*args, **kwargs):
                cmd_args = mock_popen.call_args[0][0]
                path_idx = cmd_args.index('--path') + 1
                with open(cmd_args[path_idx], 'wb') as f:
                    f.write(b"fake-png")
                return (b"", b"")

            mock_proc.communicate.side_effect = fake_communicate
            mock_popen.return_value = mock_proc
            png = take_screenshot('https://www.google.fr', timeout='invalid')
            self.assertEqual(png, b"fake-png")

    def test_take_screenshot_timeout_expired(self):
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 9999
            mock_proc.communicate.side_effect = subprocess.TimeoutExpired(cmd='node', timeout=1)
            mock_popen.return_value = mock_proc
            with patch('os.killpg') as mock_killpg:
                with self.assertRaisesRegex(ScreenshotterException, 'Screenshot process timed out'):
                    take_screenshot('https://www.google.fr', timeout=1)
                self.assertTrue(mock_killpg.called)

    def test_take_screenshot_timeout_expired_lookup_error(self):
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 9999
            mock_proc.communicate.side_effect = subprocess.TimeoutExpired(cmd='node', timeout=1)
            mock_popen.return_value = mock_proc
            with patch('os.killpg', side_effect=ProcessLookupError):
                with self.assertRaisesRegex(ScreenshotterException, 'Screenshot process timed out'):
                    take_screenshot('https://www.google.fr', timeout=1)

    def test_take_screenshot_unexpected_exception(self):
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 9999
            mock_proc.communicate.side_effect = RuntimeError("Crash")
            mock_popen.return_value = mock_proc
            with patch('os.killpg') as mock_killpg:
                with self.assertRaises(RuntimeError):
                    take_screenshot('https://www.google.fr')
                self.assertTrue(mock_killpg.called)

    def test_take_screenshot_unexpected_exception_lookup_error(self):
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 9999
            mock_proc.communicate.side_effect = RuntimeError("Crash")
            mock_popen.return_value = mock_proc
            with patch('os.killpg', side_effect=ProcessLookupError):
                with self.assertRaises(RuntimeError):
                    take_screenshot('https://www.google.fr')

    def test_take_screenshot_empty_file(self):
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate.return_value = (b"", b"Warning")
            mock_popen.return_value = mock_proc
            with patch('os.path.exists', return_value=True), patch('os.path.getsize', return_value=0):
                with self.assertRaises(ScreenshotterException):
                    take_screenshot('https://www.google.fr')

    def test_urls_debug_toolbar(self):
        import screamshotter.urls
        with patch.dict(os.environ, {'DJANGO_SETTINGS_MODULE': 'screamshotter.settings.dev'}), override_settings(DEBUG=True):
            mock_dt = types.ModuleType('debug_toolbar')
            mock_dt_urls = types.ModuleType('debug_toolbar.urls')
            mock_dt_urls.urlpatterns = []
            mock_dt.urls = mock_dt_urls
            with patch.dict(sys.modules, {'debug_toolbar': mock_dt, 'debug_toolbar.urls': mock_dt_urls}):
                importlib.reload(screamshotter.urls)
        importlib.reload(screamshotter.urls)
