# coding: utf-8
from django.shortcuts import render,render_to_response
from django.http import HttpResponse,HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from Transport_Web.helpers import *
from Transport_Web.settings import STATIC_ROOT
from django.views.decorators.http import require_GET, require_POST
from transport.direction import *
import pytz
from operator import itemgetter, attrgetter
# Create your views here.

def index(request):
    roads_set,roads_directions=get_all_paths()
    polyline_js_code=poly_line_js(roads_set,roads_directions)
    clockwise=direction(1,u"顺时针")
    anti_clockwise=direction(-1,u"逆时针")
    directions=[clockwise,anti_clockwise]
    return render(request, 'transport/baidu.html',locals())
def region(request):
    slat=float(request.GET.get("slat"))
    slng=float(request.GET.get("slng"))
    elat=float(request.GET.get("elat"))
    elng=float(request.GET.get("elng"))
    print(u"左上经纬度：" + str(slat) + u"," + str(slng) + u", 右下经纬度:" + str(elat) + u"," + str(elng))

    table_arr=load_pickle_from(STATIC_ROOT+os.sep+"WFJBXX_ORG.pkl")
    table_1=table_arr[0]
    data_points=get_point_in_region(table_1,slat,slng,elat,elng)
    return success_response(str(len(data_points)))
def region_statistics(request):
    slat=float(request.GET.get("slat"))
    slng=float(request.GET.get("slng"))
    elat=float(request.GET.get("elat"))
    elng=float(request.GET.get("elng"))
    print(u"左上经纬度：" + str(slat) + u"," + str(slng) + u", 右下经纬度:" + str(elat) + u"," + str(elng))
    table_arr=load_pickle_from(STATIC_ROOT + os.sep + 'labeledpoints.pkl')
    data_points=get_point_in_region(table_arr,slat,slng,elat,elng)
    return success_response(data_points)

def get_point_in_region(table_arr,slat,slng,elat,elng):
    points_info_list = []
    for i in range(len(table_arr)):
        table = sorted(table_arr[i],key=itemgetter(0,1,2))  #得到一种违章类型的list,线按照纬度排序，然后按照经度排序,再按照时间排序
        min_lat_index = lower_bound_search(table,0,len(table),elat,0)
        max_lat_index = upper_bound_search(table,0,len(table),slat,0)
        min_index = lower_bound_search(table,min_lat_index,max_lat_index+1,1)
        max_index = upper_bound_search(table,max_lat_index,max_lat_index+1,1)
        posNum,negNum = 0,0
        day_list = []
        date_index = {}
        date_num,hour_num=0,0
        for j in range(min_index,max_index+1):
            date = table[j][2]  #这是date的list
            str_day = str(date[0]) + str(date[1]) +str(date[2])  #将日期存成字符串
            hour = date[3]  #将小时存成字符串
            day_index = date_index.get(str_day,-1)
            if(day_index == -1): #表示data_index里面没有这个字段
                date_index[str_day] = date_num;
                day_info = {}
                day_info['day'] = [date[0],date[1],date[2]]
                for hour_index in range(0,24):
                    day_info['data'].append({'posNum':0,'negNum':0})
                if(table[j][3]==1):
                    day_info['data'][hour]['posNum'] += 1
                else:
                    day_info['data'][hour]['negNum'] += 1
                day_list.append(day_info)
                date_num += 1
            else:
                day_info = day_list[day_index]
                if (table[j][3] == 1):
                    day_info['data'][hour]['posNum'] += 1
                else:
                    day_info['data'][hour]['negNum'] += 1

        points_info_list.append(day_list)
    return json.dumps(points_info_list)

#type用来区分经度还是纬度，0表示纬度，1表示经度
def lower_bound_search(table,l,r,num,type):
    while(l<r):
        mid = l+(r-l)/2
        if(table[mid][type] >= num):
            r=mid
        else:
            l=mid+1
    return l

def upper_bound_search(table,l,r,num,type):
    while(l<r):
        mid=l+(r-l)/2
        if(table[mid][type]<=num):
            l=mid+1
        else:
            r=mid
    return l


@require_POST
def label_the_road(request):
    point_list_str=request.POST['point_list']
    direction=request.POST['direction']
    #print point_list_str+"\t"+direction
    point_list=json.loads(point_list_str)
    road_json=convert_point_list_to_path_file(point_list,direction)
    tz=pytz.timezone(pytz.country_timezones('cn')[0])
    now_str=datetime.datetime.now(tz).strftime('%Y_%m_%d_%H_%M_%S')+".json"
    road_file=open(ROAD_DIR+os.sep+now_str,"w")
    road_file.write(road_json)
    return HttpResponseRedirect(reverse('transport:index'))
def showpath(request):
    noise_invisible=int(request.GET.get("noise_invisible",0))

    file_names=os.listdir(BASE_DIR+os.sep+"static"+os.sep+"theme")
    theme_names=[]
    static_theme_url=[]
    for filename in file_names:
        theme_name=filename.split(".")[0]
        static_theme_url.append('/static/theme/'+theme_name)
        theme_names.append(theme_name)
    selected_index=5
    return render(request, 'transport/diffcolor.html',locals())
def echarts(request):
    return render(request, 'transport/echarts.html',locals())