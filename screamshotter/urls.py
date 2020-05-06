from django.urls import path, include


urlpatterns = [
    path(r'',  include('screamshot.urls'), name='screamshot'),
]
