from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^region', views.region, name='region'),
    url(r'^$', views.index, name='index'),
]