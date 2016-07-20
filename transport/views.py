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
    data_points_json=get_points_in_region(table_arr,slat,slng,elat,elng)
    return success_response(data_points_json)

def get_points_in_region(table_arr,slat,slng,elat,elng):
    points_info_dict = {}
    length = len(table_arr)
    table_date = table_arr[0][0][2]
    date_hour_min = datetime.datetime(*tuple(table_date)[0:4])
    date_hour_max = datetime.datetime(*tuple(table_date)[0:4])

    for i in range(length):
        try:
            table = sorted(table_arr[i],key=itemgetter(0,1,2))  #得到一种违章类型的list,线按照纬度排序，然后按照经度排序,再按照时间排序
            min_lng_index = lower_bound_search(table,0,len(table),slng,0)
            max_lng_index = upper_bound_search(table,0,len(table),elng,0)
            min_index = lower_bound_search(table,min_lng_index,max_lng_index+1,elat,1)
            max_index = upper_bound_search(table,max_lng_index,max_lng_index+1,slat,1)
            posNum,negNum = 0,0
            data_list = []
            date_index = {}
            date_num=0
            print(table[min_index][0],table[min_index][1])
            print("-------")
            print(table[max_index][0],table[max_index][1])
            print(get_point_in_region(table,slat,slng,elat,elng))
            print(max_index-min_index+1)
            #for j in range(min_index,max_index+1):
            for j in range(len(table)):
                if(slng <=table[j][0] and table[j][0]<= elng and elat <= table[j][1] and table[j][1] <slat):
                    date = table[j][2]  #这是date的tuple
                    '''date_hour = datetime.datetime(*tuple(table[j][2])[:4])
                    if(date_hour<date_hour_min):
                        date_hour_min = date_hour
                    if(date_hour>date_hour_max):
                        date_hour_max = date_hour'''

                    str_day = str(date[0]) + str(date[1]) +str(date[2])+str(date[3])  #将日期存成字符串

                    day_index = date_index.get(str_day,-1)
                    if(day_index == -1): #表示data_index里面没有这个字段
                        date_index[str_day] = date_num;
                        day_info = {'datatime':table[j][2][:4],'posNum':0,'negNum':0}
                        if(table[j][3]==1):
                            day_info['posNum'] += 1
                        else:
                            day_info['negNum'] += 1
                        data_list.append(day_info)
                        date_num += 1
                    else:
                        day_info = data_list[day_index]
                        if (table[j][3] == 1):
                            day_info['posNum'] += 1
                        else:
                            day_info['negNum'] += 1

            data_list = sorted(data_list,key=itemgetter('datatime'))
            points_info_dict['type'+str(i+1)]= data_list

        except Exception as e:
            print(e)
    '''date_list = []
    d_minus = date_hour_max - date_hour_min

    hours = int((d_minus.days * 24 * 60 * 60 + d_minus.seconds) / 3600.0)
    time_min = date_hour_min.time()
    t_h = time_min.hour
    date_min = date_hour_min.date()
    date_time_min = datetime.datetime(date_min.year, date_min.month, date_min.day, t_h, 0, 0)
    for hour in range(hours+1):
        datetmp = date_time_min + datetime.timedelta(hours=hour)
        date_list.append([datetmp.year,datetmp.month,datetmp.day,datetmp.hour,datetmp.minute,datetmp.second])
    points_info_dict['date_list'] = date_list'''

    jsonstr = json.dumps(points_info_dict,sort_keys=True,indent=4)
    print(jsonstr)
    return jsonstr

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
    title="举报量"
    return render(request, 'transport/diffcolor.html',locals())
def echarts(request):
    return render(request, 'transport/echarts.html',locals())