from django.conf.urls import url

from transport import views

urlpatterns = [
    url(r'^area_statistics', views.area_statistics, name='area_statistics'),
    url(r'^region', views.region, name='region'),
    url(r'^echarts', views.echarts, name='echarts'),
    url(r'^label_the_road', views.label_the_road, name='label_the_road'),
    url(r'^showpath', views.showpath, name='showpath'),
    url(r'^heatmap', views.heatmap, name='heatmap'),
    url(r'^violation_statistics', views.violation_statistics, name='heaviolation_statisticstmap'),

    url(r'^$', views.index, name='index'),
]