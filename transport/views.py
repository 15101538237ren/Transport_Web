from django.shortcuts import render,render_to_response
from django.http import HttpResponse
from django.template import RequestContext
# Create your views here.
def index(request):
    name="harry"
    #return render_to_response('index.html', locals(), context_instance=RequestContext(request))
    return render(request, 'transport/index.html',locals())