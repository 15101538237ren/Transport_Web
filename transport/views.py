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

IN_RECTANGLE_AREA = 0
IN_POLYGON_AREA = 1

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

def area_statistics(request):

    area_list_str = request.GET.get('point_list',-2)
    area_points_list,border_list = [],[]
    type = IN_POLYGON_AREA

    minX, maxX, minY, maxY = MAXINT, 0, MAXINT, 0

    if(area_list_str == -2):
        slat = float(request.GET.get("slat", -1))
        slng = float(request.GET.get("slng", -1))
        elat = float(request.GET.get("elat", -1))
        elng = float(request.GET.get("elng", -1))
        area_points_list = [[slng,slat],[slng,elat],[elng,elat],[elng,slat]]
        type = IN_RECTANGLE_AREA
        minX, maxX, minY, maxY = slng, elng, elat, slat
        border_list = [minX,maxX,minY,maxY]
    else:
        area_list = json.loads(area_list_str)
        for point in area_list:
            minX, maxX, minY, maxY = min(minX, point['lng']), max(maxX, point['lng']), min(minY, point['lat']), max(maxY, point['lat'])
            area_points_list.append([point['lng'], point['lat']])
        border_list = [minX, maxX, minY, maxY]
    table_arr=load_pickle_from(STATIC_ROOT + os.sep + 'labeledpoints.pkl')

    points_info_dict = {}
    table_arr_length = len(table_arr)
    points_info_dict['statistic'] = {}
    for i in range(table_arr_length):
        [data_list, stat_dict] = get_points_in_region(table_arr[i],area_points_list,border_list,2,type)
        points_info_dict['type' + str(i + 1)] = data_list
        points_info_dict['statistic']['type' + str(i + 1)] = stat_dict

    data_points_json = json.dumps(points_info_dict, sort_keys=True, indent=4)
    return success_response(data_points_json)

#判断点是否在矩形边界区域内
def is_in_border(border_list, point):
    return border_list[0] <= point[LNG_INDEX] and point[LNG_INDEX] <= border_list[1] \
           and border_list[2] <= point[LAT_INDEX] and point[LAT_INDEX] <= border_list[3]


#判断点是否在区域内
def point_is_in_area(area_points_list, border_list, point,type):
    if(type == IN_RECTANGLE_AREA):
        return is_in_border(border_list, point)
    elif(type == IN_POLYGON_AREA):
        if (is_in_border(border_list, point) and point[DIRECTION_INDEX] != 0):  # 这个数据点必须在道路上才行
            [status, dis] = check_point(area_points_list, point[LNG_INDEX], point[LAT_INDEX])
            if (status > 0):
                return True
        return False

#获取在矩形区域内的所有数据点
#通过max_index来选择需要返回哪些数据
#通过type来判断是否在矩形区域内，或多边形区域内，type==0表示矩形，type==1表示多边形
def get_points_in_region(table,area_points_list,border_list,MAX_INDEX,type):

    #得到一种违章类型的list,之前在helper中处理数据时就已经按照先经度，后纬度的顺序排好序了
    min_lng_index = lower_bound_search(table, 0, len(table), border_list[0], LNG_INDEX)
    max_lng_index = upper_bound_search(table, 0, len(table), border_list[1], LNG_INDEX)-1  #upper_bound函数求出来的是小于这个数字的最大数
    sub_table = sorted(table[min_lng_index:max_lng_index+1],key=itemgetter(LAT_INDEX))  #将在经度范围内的数据再次按照纬度重新排序

    min_final_index = lower_bound_search(sub_table, 0, len(sub_table), border_list[2], LAT_INDEX)
    max_final_index = upper_bound_search(sub_table, 0, len(sub_table), border_list[3], LAT_INDEX)-1

    data_list,date_index,date_num = [],{},0
    '''count = 0
    test_list = []
    for i in range(len(table)):

        if(slng <= table[i][LNG_INDEX] and table[i][LNG_INDEX] <= elng and elat <= table[i][LAT_INDEX] and table[i][LAT_INDEX] <= slat):
            count += 1
            test_list.append([table[i][LNG_INDEX],table[i][LAT_INDEX]])
    print(count)
    print(max_final_index-min_final_index+1)
    test_list = sorted(test_list,key = itemgetter(LNG_INDEX,LAT_INDEX))
    test2_list = []'''

    posSum, negSum = 0,0

    for i in range(min_final_index,max_final_index+1):
        #test2_list.append([sub_table[i][LNG_INDEX],sub_table[i][LAT_INDEX]])

        is_in_area = point_is_in_area(area_points_list, border_list, sub_table[i], type)

        if(not is_in_area):
            continue
        if(MAX_INDEX >= DATE_TIME_INDEX):

            date = sub_table[i][DATE_TIME_INDEX]  # 这是date的tuple
            #date这个tuple中date[0]表示年，date[1]表示月，date[2]表示日，date[3]表示小时
            str_day = str(date[0]) + str(date[1]) +str(date[2])+str(date[3])  #将日期存成字符串
            day_index = date_index.get(str_day,-1)
            if(day_index == -1): #表示data_index里面没有这个字段
                date_index[str_day] = date_num
                #获取时间数据只到小时级别
                day_info = {'datatime':sub_table[i][DATE_TIME_INDEX][:4],'posNum':0,'negNum':0}
                if(sub_table[i][DIRECTION_INDEX]==1):
                    day_info['posNum'] += 1
                    posSum += 1
                elif(sub_table[i][DIRECTION_INDEX]==-1):
                    day_info['negNum'] += 1
                    negSum += 1
                data_list.append(day_info)
                date_num += 1
            else:
                day_info = data_list[day_index]
                if (sub_table[i][DIRECTION_INDEX] == 1):
                    day_info['posNum'] += 1
                    posSum += 1
                elif(sub_table[i][DIRECTION_INDEX] == -1):
                    day_info['negNum'] += 1
                    negSum += 1
        elif(MAX_INDEX == LAT_INDEX):
            data_list.append([sub_table[i][LNG_INDEX],sub_table[i][LAT_INDEX]])
    '''test2_list = sorted(test2_list,key = itemgetter(LNG_INDEX,LAT_INDEX))
    count2 = 0
    for i in range(len(test_list)):
        if(test_list[i][LNG_INDEX] == test2_list[i][LNG_INDEX] and test_list[i][LAT_INDEX] == test2_list[i][LAT_INDEX]):
            count2 += 1
    if(count2 == len(test_list)):
        print("YES")
    else:
        print("NO")'''

    if (MAX_INDEX >= DATE_TIME_INDEX):
        data_list = sorted(data_list,key=itemgetter('datatime'))

    stat_dict = {'pos':{'sum':posSum},'neg':{'sum':negSum}}

    return data_list, stat_dict


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



    table_arr = load_pickle_from(STATIC_ROOT + os.sep + 'labeledpoints.pkl')



    points_info_dict = {}

    table_arr_length = len(table_arr)
    for i in range(table_arr_length):
        data_list = get_points_in_region(table_arr[i], minX, maxX, minY, maxY, 2, IN_POLYGON_AREA)
        points_info_dict['type' + str(i + 1)] = data_list

    data_points_json = json.dumps(points_info_dict, sort_keys=True, indent=4)


    for i in range(table_arr_length):

        table = table_arr[i]

        min_lng_index = lower_bound_search(table, 0, len(table), minX, LNG_INDEX)
        max_lng_index = upper_bound_search(table, 0, len(table), maxX, LNG_INDEX) - 1  # upper_bound函数求出来的是小于这个数字的最大数
        sub_table = sorted(table[min_lng_index:max_lng_index + 1], key=itemgetter(LAT_INDEX))  # 将在经度范围内的数据再次按照纬度重新排序

        min_final_index = lower_bound_search(sub_table, 0, len(sub_table), minY, LAT_INDEX)
        max_final_index = upper_bound_search(sub_table, 0, len(sub_table), maxY, LAT_INDEX) - 1

        type_list = []
        subb_table = sub_table[min_final_index: max_final_index + 1]
        for j in range(min_final_index, max_final_index + 1):
            point = sub_table[j]

        in_area_points.append(type_list)
    json_str = json.dumps(in_area_points)
    return success_response(json_str)



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