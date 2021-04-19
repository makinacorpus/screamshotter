import os

from django.conf import settings
from django.urls import path, include
from rest_framework.renderers import JSONOpenAPIRenderer, BrowsableAPIRenderer
from rest_framework.schemas import get_schema_view

schema_view = get_schema_view(
    title='Screamshotter API',
    description='Pupeteer Chromium Headless based API to get advanced screenshots from dynamic web pages',
    url='https://github.com/makinacorpus/screamshotter',
    renderer_classes=[
        JSONOpenAPIRenderer,
        BrowsableAPIRenderer
    ],
    public=False,

)

urlpatterns = [
    path('schema/', schema_view, name='schema'),
    path('', include('screenshotter.urls')),
]

if settings.DEBUG and os.getenv('DJANGO_SETTINGS_MODULE') == 'screamshotter.settings.dev':
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
