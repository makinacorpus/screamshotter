from django.urls import path

from . import views

app_name = "screenshotter"

urlpatterns = [
    path("", views.ScreenshotAPIView.as_view(), name="screenshot"),
    path("test/", views.ScreenshotAPIView.as_view(), name="screenshot-test"),
]
