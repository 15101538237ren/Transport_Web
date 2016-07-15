from django.conf.urls import url

from transport import views

urlpatterns = [
    url(r'^region', views.region, name='region'),
    url(r'^showpath', views.showpath, name='showpath'),
    url(r'^$', views.index, name='index'),
]