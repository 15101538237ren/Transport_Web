# coding: utf-8
from django.shortcuts import render,render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from Transport_Web.helpers import *
from Transport_Web.settings import STATIC_ROOT
# Create your views here.

def index(request):
    return render(request, 'transport/baidu.html',locals())
def region(request):
    slat=float(request.GET.get("slat"))
    slng=float(request.GET.get("slng"))
    elat=float(request.GET.get("elat"))
    elng=float(request.GET.get("elng"))
    #print u"左下经纬度："+ unicode(slat)+u"," + unicode(slng) + u", 右上经纬度:"+unicode(elat)+u","+unicode(elng)
    print(u"左下经纬度：" + str(slat) + u"," + str(slng) + u", 右上经纬度:" + str(elat) + u"," + str(elng))

    table_arr=load_pickle_from(STATIC_ROOT+os.sep+"WFJBXX_ORG.pkl")
    table_1=table_arr[0]
    data_points=get_point_in_region(table_1,slat,slng,elat,elng)
    return success_response(str(len(data_points)))
def showpath(request):
    return render(request, 'transport/diffcolor.html',locals())