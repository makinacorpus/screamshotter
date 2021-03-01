import logging

from rest_framework.response import Response
from rest_framework import status as http_status, renderers
from rest_framework.views import APIView

from .puppeteer import take_screenshot
from .renderers import PNGRenderer, Base64JSONRenderer
from .serializer import ScreenshotSerializer


class ScreenshotAPIView(APIView):
    serializer_class = ScreenshotSerializer
    renderer_classes = [PNGRenderer, Base64JSONRenderer, renderers.BrowsableAPIRenderer]

    def get_serializer(self, *args, **kwargs):
        """
        Keep this method to see json structure in API html view
        """
        return self.serializer_class()

    def serializer_invalid(self, serializer):
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

    def serializer_valid(self, serializer):
        try:
            response = take_screenshot(**serializer.validated_data)
            status = http_status.HTTP_200_OK
        except Exception as exc:
            logging.error(str(exc))
            response = {'errors': f'{exc}'}
            status = http_status.HTTP_500_INTERNAL_SERVER_ERROR
        return Response(response, status=status)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        return self.serializer_valid(serializer) \
            if serializer.is_valid() else self.serializer_invalid(serializer)

    def get(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.GET)
        return self.serializer_valid(serializer) \
            if serializer.is_valid() else self.serializer_invalid(serializer)
