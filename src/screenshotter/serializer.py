from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class ScreenshotSerializer(serializers.Serializer):
    url = serializers.URLField()
    width = serializers.IntegerField(required=False, initial=1920)
    height = serializers.IntegerField(required=False, initial=1080)
    selector = serializers.CharField(initial='body', required=False,
                                     help_text=_("CSS selector"))
    wait_selectors = serializers.ListField(child=serializers.CharField(allow_blank=False),
                                           required=False, initial=[],
                                           help_text=_("CSS selectors to wait before taking screenshot"))
    waitfor = serializers.CharField(required=False,
                                    initial='body',
                                    help_text=_("CSS selectors to wait before taking screenshot"))
    screamshotter_css_class = serializers.CharField(required=False, initial='screamshot',
                                                    help_text=_("CSS class to inject in body for customization"))
    wait_seconds = serializers.IntegerField(required=False, initial=0,
                                            help_text=_("Force browser to wait before take screenshot"))
    timeout = serializers.IntegerField(required=False, initial=settings.TIMEOUT,
                                       help_text=_("Force browser to timeout after this amount (in second)"))
    forward_headers = serializers.JSONField(required=False, initial={},
                                            help_text=_("Add headers to browser request. in JSON form"))
