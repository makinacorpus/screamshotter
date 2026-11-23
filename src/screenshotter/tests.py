import importlib
import os
import sys
import types
from tempfile import TemporaryDirectory
from unittest import skipIf
from unittest.mock import MagicMock, patch

import magic
from django.apps import apps
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from PIL import Image
from rest_framework.serializers import Serializer
from rest_framework.test import APISimpleTestCase

from .exceptions import ScreenshotterException
from .playwright import _dismiss_dialog, _reap_zombies, take_screenshot
from .renderers import ScreamBrowsableAPIRenderer
from .serializer import ScreenshotSerializer
from .views import ScreenshotAPIView

temp_dir = TemporaryDirectory()


class CaptureTestCase(SimpleTestCase):
    @override_settings(MEDIA_ROOT=temp_dir.name)
    def test_capture_mime(self):
        png = take_screenshot("https://www.google.fr")

        cfile = ContentFile(content=png)
        default_storage.save(name="test_capture_mime.png", content=cfile)

        self.assertNotEqual(cfile.size, 0)
        mime = magic.from_buffer(
            default_storage.open("test_capture_mime.png").read(), mime=True
        )
        self.assertEqual(
            mime,
            "image/png",
        )

    @override_settings(MEDIA_ROOT=temp_dir.name)
    def test_capture_size(self):
        png = take_screenshot("https://www.google.fr", width=1280, height=720)

        cfile = ContentFile(content=png)
        default_storage.save(name="test_capture_size.png", content=cfile)

        image = Image.open(default_storage.path("test_capture_size.png"))

        self.assertEqual(image.width, 1280)
        self.assertEqual(image.height, 720)

    def test_bad_dns(self):
        with self.assertRaises(ScreenshotterException):
            take_screenshot("https://cccccc")

    def test_view_has_get_serializer(self):
        view = ScreenshotAPIView()

        self.assertTrue(hasattr(view, "get_serializer"))
        self.assertTrue(isinstance(view.get_serializer(), Serializer))

    @override_settings(
        SCREENSHOTTER={"CHROMIUM_BROWSER_FILEPATH": "/nonexistent/chrome"}
    )
    def test_bad_browser_path(self):
        with self.assertRaises(ScreenshotterException):
            take_screenshot("https://www.google.fr")

    @skipIf(settings.TIMEOUT != 0.001, "skip if timeout is not 1ms")
    @override_settings(MEDIA_ROOT=temp_dir.name)
    def test_timeout_screenshot(self):
        # We show that we can change timeout value. It's so small, this takes more than 1ms to generate the screenshot.
        # => It fails
        with self.assertRaisesRegex(
            ScreenshotterException, r"Timeout 1(\.0)?ms exceeded"
        ):
            take_screenshot("https://www.google.fr")

    @override_settings(SCREENSHOTTER={"BAD_SETTINGS": "none"})
    def test_bad_settings(self):
        with self.assertRaises(AttributeError):
            from .settings import app_settings

            bool(app_settings.BAD_SETTINGS)


class CaptureApiTestCase(APISimpleTestCase):
    def test_api_good_request_json(self):
        serializer = ScreenshotSerializer()
        data = serializer.data
        data["url"] = "https://www.google.fr"

        response = self.client.post(
            reverse("screenshotter:screenshot") + "?format=json", data=data
        )
        data = response.json()
        self.assertEqual(response.status_code, 200, data)
        self.assertIn("base64", data)

    def test_api_good_get_request_json(self):
        response = self.client.get(
            reverse("screenshotter:screenshot")
            + "?format=json&url=https://www.google.fr"
        )
        data = response.json()
        self.assertEqual(response.status_code, 200, data)
        self.assertIn("base64", data)

    def test_api_bad_request(self):
        serializer = ScreenshotSerializer()
        response = self.client.post(
            reverse("screenshotter:screenshot") + "?format=json", data=serializer.data
        )
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertIn("url", data)
        self.assertEqual(["This field may not be blank."], data["url"])

    def test_api_bad_get_request(self):
        response = self.client.get(reverse("screenshotter:screenshot") + "?format=json")
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertIn("url", data)
        self.assertEqual(["This field is required."], data["url"])

    def test_api_wrong_response(self):
        serializer = ScreenshotSerializer()
        data = serializer.data
        data["url"] = "https://dodo.kiik"
        response = self.client.post(
            reverse("screenshotter:screenshot") + "?format=json", data=data
        )
        self.assertEqual(response.status_code, 500, response.json())

    def test_api_browsable(self):
        serializer = ScreenshotSerializer()
        data = serializer.data
        data["url"] = "https://www.google.fr"

        response = self.client.post(
            reverse("screenshotter:screenshot") + "?format=api", data=data
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<html>", response.content)
        # check default renderer is json in browsable api (response in "base64": "xxx" format)
        self.assertIn(b"&quot;base64&quot;", response.content)

    def test_png_default(self):
        serializer = ScreenshotSerializer()
        data = serializer.data
        data["url"] = "https://www.google.fr"

        response = self.client.post(reverse("screenshotter:screenshot"), data=data)
        self.assertEqual(response.status_code, 200)
        mime = magic.from_buffer(response.content, mime=True)
        self.assertEqual(mime, "image/png")


class WebPageTestCase(APISimpleTestCase):
    def test_web_page_get_empty_form(self):
        response = self.client.get(
            reverse("screenshotter:screenshot"), HTTP_ACCEPT="text/html"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Take a Screenshot", response.content)
        self.assertIn(b'name="url"', response.content)
        self.assertIn(b'name="width"', response.content)
        self.assertIn(b'name="height"', response.content)
        self.assertNotIn(b"This field is required.", response.content)

    def test_web_page_get_format_api(self):
        response = self.client.get(reverse("screenshotter:screenshot") + "?format=api")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Take a Screenshot", response.content)
        self.assertIn(b'name="url"', response.content)
        self.assertNotIn(b"This field is required.", response.content)

    def test_web_page_test_endpoint(self):
        response = self.client.get(
            reverse("screenshotter:screenshot-test"), HTTP_ACCEPT="text/html"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Take a Screenshot", response.content)
        self.assertIn(b'name="url"', response.content)

    def test_web_page_post_success_displays_image(self):
        with patch(
            "screenshotter.views.take_screenshot", return_value=b"test-fake-png-content"
        ):
            response = self.client.post(
                reverse("screenshotter:screenshot") + "?format=api",
                data={"url": "https://www.google.fr"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Captured Screenshot", response.content)
            self.assertIn(b"data:image/png;base64,", response.content)
            # base64 of 'test-fake-png-content' is 'dGVzdC1mYWtlLXBuZy1jb250ZW50'
            self.assertIn(b"dGVzdC1mYWtlLXBuZy1jb250ZW50", response.content)
            self.assertIn(b'download="screenshot.png"', response.content)

    def test_web_page_get_with_url_displays_image(self):
        with patch(
            "screenshotter.views.take_screenshot", return_value=b"test-fake-png-content"
        ):
            response = self.client.get(
                reverse("screenshotter:screenshot")
                + "?format=api&url=https://www.google.fr"
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Captured Screenshot", response.content)
            self.assertIn(b"data:image/png;base64,", response.content)
            self.assertIn(b"dGVzdC1mYWtlLXBuZy1jb250ZW50", response.content)

    def test_web_page_post_validation_error(self):
        response = self.client.post(
            reverse("screenshotter:screenshot") + "?format=api", data={"url": ""}
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Take a Screenshot", response.content)
        self.assertIn(b"This field may not be blank.", response.content)
        self.assertNotIn(b"Captured Screenshot", response.content)

    def test_web_page_post_capture_error(self):
        with patch(
            "screenshotter.views.take_screenshot",
            side_effect=Exception("Custom Playwright failure"),
        ):
            response = self.client.post(
                reverse("screenshotter:screenshot") + "?format=api",
                data={"url": "https://www.google.fr"},
            )
            self.assertEqual(response.status_code, 500)
            self.assertIn(b"Screenshot generation failed", response.content)
            self.assertIn(b"Custom Playwright failure", response.content)

    def test_renderer_get_context_dict_base64(self):
        renderer = ScreamBrowsableAPIRenderer()
        resp = type(
            "Response",
            (),
            {"status_code": 200, "status_text": "OK", "items": lambda self: []},
        )()
        view = ScreenshotAPIView()
        request = self.client.get("/?format=api").wsgi_request
        drf_request = view.initialize_request(request)
        view.setup(drf_request)
        renderer.accepted_media_type = "text/html"
        renderer.renderer_context = {
            "view": view,
            "request": drf_request,
            "response": resp,
        }

        context = renderer.get_context(
            {"base64": "custom-base64-string"}, "text/html", renderer.renderer_context
        )
        self.assertEqual(context.get("image_base64"), "custom-base64-string")

    def test_renderer_get_context_dict_errors(self):
        renderer = ScreamBrowsableAPIRenderer()
        resp = type(
            "Response",
            (),
            {
                "status_code": 500,
                "status_text": "Internal Server Error",
                "items": lambda self: [],
            },
        )()
        view = ScreenshotAPIView()
        request = self.client.get("/?format=api").wsgi_request
        drf_request = view.initialize_request(request)
        view.setup(drf_request)
        renderer.accepted_media_type = "text/html"
        renderer.renderer_context = {
            "view": view,
            "request": drf_request,
            "response": resp,
        }

        context = renderer.get_context(
            {"errors": "custom-error-string"}, "text/html", renderer.renderer_context
        )
        self.assertEqual(context.get("capture_errors"), "custom-error-string")

    def test_view_get_serializer_unbound(self):
        view = ScreenshotAPIView()
        serializer = view.get_serializer()
        self.assertFalse(hasattr(serializer, "initial_data"))

    def test_view_get_serializer_with_explicit_data(self):
        view = ScreenshotAPIView()
        serializer = view.get_serializer(data={"url": "https://explicit.com"})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["url"], "https://explicit.com")


class ProcessManagementTestCase(SimpleTestCase):
    def test_reap_zombies_normal(self):
        with patch("os.waitpid", side_effect=[(1234, 0), (0, 0)]):
            _reap_zombies()

    def test_reap_zombies_child_process_error(self):
        with patch("os.waitpid", side_effect=ChildProcessError):
            _reap_zombies()

    def test_reap_zombies_os_error(self):
        with patch("os.waitpid", side_effect=OSError):
            _reap_zombies()

    def test_dismiss_dialog(self):
        dialog = MagicMock()
        _dismiss_dialog(dialog)
        dialog.dismiss.assert_called_once()

    def test_dismiss_dialog_exception(self):
        dialog = MagicMock()
        dialog.dismiss.side_effect = RuntimeError("closed")
        _dismiss_dialog(dialog)

    def test_apps_ready(self):
        config = apps.get_app_config("screenshotter")
        with patch("ctypes.CDLL") as mock_cdll:
            config.ready()
            mock_cdll.assert_called_once_with("libc.so.6")

    def test_apps_ready_exception(self):
        config = apps.get_app_config("screenshotter")
        with patch("ctypes.CDLL", side_effect=Exception("error")):
            config.ready()

    def _mock_playwright(self):
        mock_page = MagicMock()
        mock_page.evaluate.return_value = {
            "left": 0,
            "top": 0,
            "width": 1280,
            "height": 720,
        }
        mock_page.screenshot.return_value = b"fake-png"

        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page

        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context

        mock_p = MagicMock()
        mock_p.chromium.launch.return_value = mock_browser
        mock_p.chromium.connect_over_cdp.return_value = mock_browser

        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_p
        mock_cm.__exit__.return_value = False
        return mock_cm, mock_p, mock_browser, mock_context, mock_page

    def test_take_screenshot_invalid_timeout(self):
        mock_cm, _, _, _, mock_page = self._mock_playwright()
        with patch("screenshotter.playwright.sync_playwright", return_value=mock_cm):
            png = take_screenshot(
                "https://www.google.fr",
                timeout="invalid",
                wait_selectors=[".ready"],
                wait_seconds=1,
                forward_headers={"X-Test": "1"},
            )
            self.assertEqual(png, b"fake-png")
            mock_page.set_default_timeout.assert_called_once_with(60000.0)
            mock_page.wait_for_selector.assert_any_call(".ready", timeout=60000.0)
            mock_page.wait_for_timeout.assert_called_once_with(1000)

    def test_take_screenshot_external_playwright(self):
        mock_cm, mock_p, _, _, _ = self._mock_playwright()
        with (
            patch("screenshotter.playwright.sync_playwright", return_value=mock_cm),
            patch.dict(os.environ, {"EXTERNAL_PLAYWRIGHT": "wss://remote:3000"}),
        ):
            png = take_screenshot("https://www.google.fr")
            self.assertEqual(png, b"fake-png")
            mock_p.chromium.connect_over_cdp.assert_called_once_with(
                "wss://remote:3000"
            )
            mock_p.chromium.launch.assert_not_called()

    def test_take_screenshot_selector_not_found(self):
        mock_cm, _, _, _, mock_page = self._mock_playwright()
        mock_page.evaluate.side_effect = [
            {"error": "Selector #missing not found"},
            "<body>empty</body>",
        ]
        with patch("screenshotter.playwright.sync_playwright", return_value=mock_cm):
            with self.assertRaisesRegex(
                ScreenshotterException, "Selector #missing not found"
            ):
                take_screenshot("https://www.google.fr", selector="#missing")

    def test_take_screenshot_empty_file(self):
        mock_cm, _, _, _, mock_page = self._mock_playwright()
        mock_page.screenshot.return_value = b""
        with patch("screenshotter.playwright.sync_playwright", return_value=mock_cm):
            with self.assertRaisesRegex(
                ScreenshotterException, "Empty screenshot generated"
            ):
                take_screenshot("https://www.google.fr")

    def test_take_screenshot_unexpected_exception(self):
        mock_cm, _, mock_browser, _, mock_page = self._mock_playwright()
        mock_page.goto.side_effect = RuntimeError("Crash")
        with patch("screenshotter.playwright.sync_playwright", return_value=mock_cm):
            with self.assertRaisesRegex(ScreenshotterException, "Crash"):
                take_screenshot("https://www.google.fr")
            mock_browser.close.assert_called_once()

    def test_urls_debug_toolbar(self):
        import screamshotter.urls

        with (
            patch.dict(
                os.environ, {"DJANGO_SETTINGS_MODULE": "screamshotter.settings.dev"}
            ),
            override_settings(DEBUG=True),
        ):
            mock_dt = types.ModuleType("debug_toolbar")
            mock_dt_urls = types.ModuleType("debug_toolbar.urls")
            mock_dt_urls.urlpatterns = []
            mock_dt.urls = mock_dt_urls
            with patch.dict(
                sys.modules,
                {"debug_toolbar": mock_dt, "debug_toolbar.urls": mock_dt_urls},
            ):
                importlib.reload(screamshotter.urls)
        importlib.reload(screamshotter.urls)
