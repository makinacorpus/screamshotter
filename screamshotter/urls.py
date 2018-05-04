from django.conf.urls import include, url


urlpatterns = [
    url(r'^$',  include('screamshot.urls', namespace='screamshot', app_name='screamshot')),
]
