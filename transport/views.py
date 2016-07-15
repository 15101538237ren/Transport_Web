from django.shortcuts import render,render_to_response
from django.http import HttpResponse
from django.template import RequestContext
# Create your views here.
def index(request):
    return render(request, 'transport/baidu.html',locals())
