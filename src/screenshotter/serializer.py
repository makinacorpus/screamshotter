from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers


class ScreenshotSerializer(serializers.Serializer):
    url = serializers.URLField()
    viewport_width = serializers.IntegerField(required=False, initial=1920)
    viewport_height = serializers.IntegerField(required=False, initial=1080)
    selector = serializers.CharField(initial='body', required=False,
                                     help_text=_("CSS selector"))
    wait_selectors = serializers.ListField(child=serializers.CharField(allow_blank=False),
                                           required=False, initial=[],
                                           help_text=_("CSS selectors to wait before taking screenshot"))
    wait_seconds = serializers.IntegerField(required=False, initial=1,
                                            help_text=_("Force browser to wait before take screenshot"))
    forward_headers = serializers.JSONField(required=False, initial={},
                                            help_text=_("Add headers to browser request. in JSON form"))
