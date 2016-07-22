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
    #print(u"左上经纬度：" + str(slng) + u"," + str(slat) + u", 右下经纬度:" + str(elng) + u"," + str(elat))

    table_arr=load_pickle_from(STATIC_ROOT+os.sep+"WFJBXX_ORG.pkl")
    table_1=table_arr[0]
    data_points=get_points_in_region(table_1,slat,slng,elat,elng)
    return success_response(str(len(data_points)))

def region_statistics(request):
    slat=float(request.GET.get("slat"))
    slng=float(request.GET.get("slng"))
    elat=float(request.GET.get("elat"))
    elng=float(request.GET.get("elng"))
    #print(u"左上经纬度：" + str(slng) + u"," + str(slat) + u", 右下经纬度:" + str(elng) + u"," + str(elat))
    table_arr=load_pickle_from(STATIC_ROOT + os.sep + 'labeledpoints.pkl')

    points_info_dict = {}
    for i in range(len(table_arr)):
        data_list = get_points_in_region(table_arr[i],slat,slng,elat,elng,2)
        points_info_dict['type' + str(i + 1)] = data_list

    data_points_json = json.dumps(points_info_dict, sort_keys=True, indent=4)
    return success_response(data_points_json)


#获取在矩形区域内的所有数据点
#通过max_index来选择需要返回哪些数据
def get_points_in_region(table,slat,slng,elat,elng,MAX_INDEX):

    table = sorted(table,key=itemgetter(LNG_INDEX))  #得到一种违章类型的list,先按照经度排序
    min_lng_index = lower_bound_search(table,0,len(table),slng,LNG_INDEX)
    max_lng_index = upper_bound_search(table,0,len(table),elng,LNG_INDEX)-1  #upper_bound函数求出来的是小于这个数字的最大数
    sub_table = sorted(table[min_lng_index:max_lng_index+1],key=itemgetter(LAT_INDEX))  #将在经度范围内的数据再次按照纬度重新排序

    min_final_index = lower_bound_search(sub_table,0,len(sub_table),elat,LAT_INDEX)
    max_final_index = upper_bound_search(sub_table,0,len(sub_table),slat,LAT_INDEX)-1

    data_list,date_index,date_num = [],{},0

    for i in range(min_final_index,max_final_index+1):

        if(MAX_INDEX >= DATE_TIME_INDEX):
            date = table[i][DATE_TIME_INDEX]  # 这是date的tuple
            #date这个tuple中date[0]表示年，date[1]表示月，date[2]表示日，date[3]表示小时
            str_day = str(date[0]) + str(date[1]) +str(date[2])+str(date[3])  #将日期存成字符串
            day_index = date_index.get(str_day,-1)
            if(day_index == -1): #表示data_index里面没有这个字段
                date_index[str_day] = date_num;
                #获取时间数据只到小时级别
                day_info = {'datatime':table[i][DATE_TIME_INDEX][:4],'posNum':0,'negNum':0}
                if(table[i][DIRECTION_INDEX]==1):
                    day_info['posNum'] += 1
                elif(table[i][DIRECTION_INDEX]==-1):
                    day_info['negNum'] += 1
                data_list.append(day_info)
                date_num += 1
            else:
                day_info = data_list[day_index]
                if (table[i][DIRECTION_INDEX] == 1):
                    day_info['posNum'] += 1
                elif(table[i][DIRECTION_INDEX] == -1):
                    day_info['negNum'] += 1
        elif(MAX_INDEX == LAT_INDEX):
            data_list.append([table[i][LNG_INDEX],table[i][LAT_INDEX]])

    if (MAX_INDEX >= DATE_TIME_INDEX):
        data_list = sorted(data_list,key=itemgetter('datatime'))

    return data_list


#type用来区分经度还是纬度，0表示经度，1表示纬度
def lower_bound_search(table,l,r,num,type):
    while(l<r):
        mid = l+(r-l)//2
        if(table[mid][type] >= num):
            r=mid
        else:
            l=mid+1
    return l

def upper_bound_search(table,l,r,num,type):
    while(l<r):
        mid=l+(r-l)//2
        if(table[mid][type] <= num):
            l=mid+1
        else:
            r=mid
    return l
def polyline_statistics(request):
    point_list_str=request.GET['point_list']

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
    data_type=int(request.GET.get("data_type",0))
    return render(request, 'transport/diffcolor.html',locals())
def echarts(request):
    return render(request, 'transport/echarts.html',locals())