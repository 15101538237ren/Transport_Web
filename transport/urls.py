from django.conf.urls import url

from transport import views

urlpatterns = [
    url(r'^region', views.region, name='region'),
    url(r'^region_statistics', views.region_statistics, name='region_statistics'),
    url(r'^label_the_road', views.label_the_road, name='label_the_road'),
    url(r'^showpath', views.showpath, name='showpath'),
    url(r'^$', views.index, name='index'),
]