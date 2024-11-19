from tempfile import TemporaryDirectory
from unittest import skipIf

import magic
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from rest_framework.serializers import Serializer
from rest_framework.test import APISimpleTestCase

from .exceptions import ScreenshotterException
from .puppeteer import take_screenshot
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

    def test_api_bad_request(self):
        serializer = ScreenshotSerializer()
        response = self.client.post(reverse('screenshotter:screenshot') + '?format=json', data=serializer.data)
        data = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertIn('url', data)
        self.assertEqual(['This field may not be blank.'], data['url'])

    def test_api_wrong_response(self):
        serializer = ScreenshotSerializer()
        data = serializer.data
        data['url'] = "https://kikou.com"
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
