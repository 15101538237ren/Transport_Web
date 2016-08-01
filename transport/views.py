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
from transport.json_handler import generate_option
from operator import itemgetter, attrgetter
IN_RECTANGLE_AREA = 0
IN_POLYGON_AREA = 1
# Create your views here.
def index(request):
    roads_set,roads_directions=get_all_paths()
    polyline_js_code=poly_line_js(roads_set,roads_directions)
    clockwise=direction(1,u"顺时针")
    anti_clockwise=direction(-1,u"逆时针")
    directions=[clockwise,anti_clockwise]
    noise_invisible=1
    return render(request, 'transport/test.html',locals())
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
    data_type = int(request.GET.get('data_type', -1))
    point_type = int(request.GET.get('point_type', 1))  #0:全部，1:应急车道，2，3，4...
    corr_types = request.GET.get('corr_types',-3)

    #单独的区域进行分析
    if corr_types == -3:
        area_list_str = request.GET.get('point_list', -2)
        points_info_dict = single_area_statistic(area_list_str, point_type, data_type)
        data_points_json = json.dumps(points_info_dict, sort_keys=True, indent=4)
        generate_option(point_type, **points_info_dict)
        print(data_points_json)
        addr = '/static/option/option1.json'
        return success_response(addr)
    else: #两个区域进行分析
        corr_types = corr_types.split(',')
        first_point_list = str(request.GET.get('first', ''))
        second_point_list = str(request.GET.get('second', ''))  #0:全部，1:应急车道，2，3，4...
        area_points_list = [first_point_list, second_point_list]

        points_info_list = multi_area_statistic(area_points_list, point_type, data_type)
        #下面是将要进行相关性分析的序列长度变成相同的
        typemin,typemax = 1,1
        if(point_type ==0):
            typemin,typemax = 1,4
        else:
            typemin,typemax = point_type,point_type

        corr_list = []
        # 如果只有一种违章type，外层i的循环相当于只进行一次
        for i in range(typemin,typemax+1):

            [pos_list1,pos_list2,neg_list1,neg_list2] = get_equal_length_lists(points_info_list,i)
            #下面是相关性分析的计算
            corr_list.append(calc_corr(pos_list1,pos_list2,neg_list1,neg_list2))

        data_points_json = json.dumps(points_info_list, indent=4)
        #print(data_points_json)
        addr = '/static/option/option1.json'
        response_info = {'addr':addr,'corr':corr_list}
        return success_response(response_info)

#将两个序列的长度变成相同的
def get_equal_length_lists(points_info_list,i):
    date_list1 = points_info_list[0]['date_list']
    datatime_list1 = points_info_list[0]['type' + str(i)]['datatime']
    pos_list1 = points_info_list[0]['type' + str(i)]['posNum']
    neg_list1 = points_info_list[0]['type' + str(i)]['negNum']
    date_list2 = points_info_list[1]['date_list']
    datatime_list2 = points_info_list[1]['type' + str(i)]['datatime']
    pos_list2 = points_info_list[1]['type' + str(i)]['posNum']
    neg_list2 = points_info_list[1]['type' + str(i)]['negNum']
    if (date_list1[0] < date_list2[0]):
        index = 0
        while (index < len(date_list1) and date_list1[index] != date_list2[0]):
            index += 1
        for j in range(index):
            date_list2.insert(j, date_list1[j])
            datatime_list2.insert(j, date_list1[j])
            pos_list2.insert(j, 0)
            neg_list2.insert(j, 0)
    else:
        index = 0
        while (index < len(date_list2) and date_list2[index] != date_list1[0]):
            index += 1
        for j in range(index):
            date_list1.insert(j, date_list2[j])
            datatime_list1.insert(j, date_list2[j])
            pos_list1.insert(j, 0)
            neg_list1.insert(j, 0)
    if (date_list1[len(date_list1) - 1] < date_list2[len(date_list2) - 1]):
        index = len(date_list2) - 1
        while (index >= 0 and date_list2[index] != date_list1[len(date_list1) - 1]):
            index -= 1
        for j in range(index + 1, len(date_list2)):
            date_list1.append(date_list2[j])
            datatime_list1.insert(j, date_list2[j])
            pos_list1.append(0)
            neg_list1.append(0)
    else:
        index = len(date_list1) - 1
        while (index >= 0 and date_list1[index] != date_list2[len(date_list2) - 1]):
            index -= 1
        for j in range(index + 1, len(date_list1)):
            date_list2.append(date_list1[j])
            datatime_list2.insert(j, date_list1[j])
            pos_list2.append(0)
            neg_list2.append(0)
    return [pos_list1,pos_list2,neg_list1,neg_list2]

#计算相关性的值
def calc_corr(pos_list1,pos_list2,neg_list1,neg_list2):
    pos_list1_avg, neg_list1_avg, pos_list2_avg, neg_list2_avg = 0.0, 0.0, 0.0, 0.0
    for j in range(len(pos_list1)):
        pos_list1_avg += pos_list1[j]
        pos_list2_avg += pos_list2[j]
        neg_list1_avg += neg_list1[j]
        neg_list2_avg += neg_list2[j]
    pos_list1_avg /= len(pos_list1)
    pos_list2_avg /= len(pos_list1)
    neg_list1_avg /= len(pos_list1)
    neg_list2_avg /= len(pos_list1)
    sum_pos_xy, sum_neg_xy, sum_pos_x2, sum_pos_y2, sum_neg_x2, sum_neg_y2 = 0, 0, 0, 0, 0, 0
    for j in range(len(pos_list1)):
        sum_pos_xy += (pos_list1[j] - pos_list1_avg) * (pos_list2[j] - pos_list2_avg)
        sum_pos_x2 += pow(pos_list1[j] - pos_list1_avg, 2)
        sum_pos_y2 += pow(pos_list2[j] - pos_list2_avg, 2)
        sum_neg_xy += (neg_list1[j] - neg_list1_avg) * (neg_list2[j] - neg_list2_avg)
        sum_neg_x2 += pow(neg_list1[j] - neg_list1_avg, 2)
        sum_neg_y2 += pow(neg_list2[j] - neg_list2_avg, 2)
    r_pos_xy = sum_pos_xy / math.sqrt(sum_pos_x2 * sum_pos_y2)
    r_neg_xy = sum_neg_xy / math.sqrt(sum_neg_x2 * sum_pos_y2)
    return [r_pos_xy,r_neg_xy]

#返回table_arr的list和对应的type_list
def get_table_from_type(point_type):
    table_arr = load_pickle_from(STATIC_ROOT + os.sep + 'labeledpoints.pkl')
    tmp_table_arr = []
    type_index_list = []
    if (point_type == 0):
        tmp_table_arr = table_arr
        type_index_list = range(1, len(table_arr) + 1)
    else:
        tmp_table_arr.append(table_arr[point_type - 1])
        type_index_list = [point_type]
    return [tmp_table_arr, type_index_list]

def single_area_statistic(area_list_str, point_type, data_type):
    area_points_list, border_list = [], []
    minX, maxX, minY, maxY = MAXINT, 0, MAXINT, 0
    area_list = json.loads(area_list_str)
    for point in area_list:
        minX, maxX, minY, maxY = min(minX, point['lng']), max(maxX, point['lng']), min(minY, point['lat']), max(maxY, point['lat'])
        area_points_list.append([point['lng'], point['lat']])
    border_list = [minX, maxX, minY, maxY]
    if len(area_list) > 2:
        area_type = IN_POLYGON_AREA
    elif len(area_list) == 2:
        area_type = IN_RECTANGLE_AREA

    [tmp_table_arr, type_index_list] = get_table_from_type(point_type)

    points_info_dict = get_points_in_region(tmp_table_arr, type_index_list, area_points_list, border_list, area_type, data_type)

    return points_info_dict

def multi_area_statistic(area_points_list, point_type, data_type):

    points_info_list = []
    for area_list_str in area_points_list:   #遍历每一个区域的坐标点
        area_list = json.loads(area_list_str)
        single_points_list, border_list = [], []
        minX, maxX, minY, maxY = MAXINT, 0, MAXINT, 0
        for point in area_list:
            minX, maxX, minY, maxY = min(minX, point['lng']), max(maxX, point['lng']), min(minY, point['lat']), max(maxY, point['lat'])
            single_points_list.append([point['lng'], point['lat']])
        border_list = [minX, maxX, minY, maxY]
        if len(area_list) > 2:
            area_type = IN_POLYGON_AREA
        elif len(area_list) == 2:
            area_type = IN_RECTANGLE_AREA

        [tmp_table_arr, type_index_list] = get_table_from_type(point_type)
        points_info_dict = get_points_in_region(tmp_table_arr, type_index_list, single_points_list, border_list, area_type, data_type)
        points_info_list.append(points_info_dict)

    return points_info_list


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


def get_time_data_list(sub_table, min_final_index, max_final_index, area_points_list, border_list, area_type):
    data_list, day_list, day_dict, day_hour_dict, day_num, date_num = [], [], {}, {}, 0, 0
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

    posSum, negSum, maxNum = 0, 0, 0
    num_type1, num_type2 = 'posNum', 'negNum'
    table_date = sub_table[0][DATE_TIME_INDEX]
    date_hour_min = datetime.datetime(*tuple(table_date)[0:4])
    date_hour_max = datetime.datetime(*tuple(table_date)[0:4])


    for j in range(min_final_index, max_final_index + 1):
        # test2_list.append([sub_table[i][LNG_INDEX],sub_table[i][LAT_INDEX]])
        is_in_area = point_is_in_area(area_points_list, border_list, sub_table[j], area_type)
        if (not is_in_area):
            continue
        date = sub_table[j][DATE_TIME_INDEX]  # 这是date的tuple
        # date这个tuple中date[0]表示年，date[1]表示月，date[2]表示日，date[3]表示小时
        date_hour = datetime.datetime(*tuple(sub_table[j][2])[:4])
        if(date_hour<date_hour_min):
            date_hour_min = date_hour
        if(date_hour>date_hour_max):
            date_hour_max = date_hour

        str_day = str(date[0]) + str(date[1]) + str(date[2])   #将日期存成字符串
        day_index = day_dict.get(str_day, -1)
        if(day_index == -1):  #这一天在字典中不存在，则将这一天所有24小时的数据插入到list中
            day_dict[str_day] = day_num
            for i in range(24):
                str_day_hour = str_day + str(i)
                day_hour_dict[str_day_hour] = date_num
                date_time = (date[0],date[1],date[2],i)
                day_info = {'datatime': date_time, num_type1: 0, num_type2: 0}
                data_list.append(day_info)
                date_num += 1
            day_list.append([date[0], date[1], date[2]])  #日期list
            day_num +=1

        str_day_hour = str_day + str(date[3])  # 将日期+小时存成字符串
        day_hour_index = day_hour_dict.get(str_day_hour, -1)
        '''if (day_hour_index == -1):  # 表示data_index里面没有这个字段
            day_hour_dict[str_day_hour] = date_num
            # 获取时间数据只到小时级别
            day_info = {'datatime': date[:4], 'posNum': 0, 'negNum': 0}
            if (sub_table[j][DIRECTION_INDEX] == 1):
                day_info['posNum'] += 1
                posSum += 1
            elif (sub_table[j][DIRECTION_INDEX] == -1):
                day_info['negNum'] += 1
                negSum += 1
            data_list.append(day_info)
            date_num += 1
        else:'''
        day_info = data_list[day_hour_index]
        if (sub_table[j][DIRECTION_INDEX] == 1):
            if(day_info[num_type1] == '-'):
                day_info[num_type1] = 1
            else:
                day_info[num_type1] += 1
            maxNum = max(maxNum, day_info[num_type1])
            posSum += 1
        elif (sub_table[j][DIRECTION_INDEX] == -1):
            if (day_info[num_type2] == '-'):
                day_info[num_type2] = 1
            else:
                day_info[num_type2] += 1
            maxNum = max(maxNum, day_info[num_type2])
            negSum += 1

    '''test2_list = sorted(test2_list,key = itemgetter(LNG_INDEX,LAT_INDEX))
    count2 = 0
    for i in range(len(test_list)):
        if(test_list[i][LNG_INDEX] == test2_list[i][LNG_INDEX] and test_list[i][LAT_INDEX] == test2_list[i][LAT_INDEX]):
            count2 += 1
    if(count2 == len(test_list)):
        print("YES")
    else:
        print("NO")'''
    data_list = sorted(data_list, key=itemgetter('datatime'))
    stat_dict = {'pos': {'sum': posSum}, 'neg': {'sum': negSum}}
    return [data_list, stat_dict, [date_hour_min,date_hour_max], maxNum, day_list]


def get_sum_data_list(sub_table, min_final_index, max_final_index, area_points_list, border_list, area_type):

    data_list, hour_dict, hour_num, date_dict, date_num = [], {}, 0, {}, 0
    posSum, negSum = 0, 0

    #time_date_dict = {}
    table_date = sub_table[0][DATE_TIME_INDEX]
    date_hour_min = datetime.datetime(*tuple(table_date)[0:4])
    date_hour_max = datetime.datetime(*tuple(table_date)[0:4])

    for j in range(min_final_index, max_final_index + 1):
        # test2_list.append([sub_table[i][LNG_INDEX],sub_table[i][LAT_INDEX]])
        is_in_area = point_is_in_area(area_points_list, border_list, sub_table[j], area_type)
        if (not is_in_area):
            continue
        date = sub_table[j][DATE_TIME_INDEX]  # 这是date的tuple
        # date这个tuple中date[0]表示年，date[1]表示月，date[2]表示日，date[3]表示小时
        str_day = str(date[0]) + str(date[1]) + str(date[2])  # 将日期存成字符串

        str_time_date = str(date[3]) +  ':' + str(date[4]) + '\n' + str(date[1]) + '/' + str(date[2])

        #time_date_index = time_date_dict.get(str_time_date, -1)

        #if(time_date_index == -1):
         #   time_date_dict[str_time_date] = str(date[1])+str(date[2])+str(date[3])+str(date[4])
        date_hour = datetime.datetime(*tuple(sub_table[j][2])[:4])
        if(date_hour<date_hour_min):
            date_hour_min = date_hour
        if(date_hour>date_hour_max):
            date_hour_max = date_hour
        day_index = date_dict.get(str_day, -1)
        if (day_index == -1):  # 表示data_index里面没有这个字段
            date_dict[str_day] = date_num
            date_num += 1

        str_hour = str(date[3])  # 将日期存成字符串
        hour_index = hour_dict.get(str_hour, -1)

        if (hour_index == -1):  # 表示data_index里面没有这个字段
            hour_dict[str_hour] = hour_num
            # 获取时间数据只到小时级别

            hour_info = {'datatime': (2016,6,1,date[3]), 'posNum': 0, 'negNum': 0}
            if (sub_table[j][DIRECTION_INDEX] == 1):
                hour_info['posNum'] += 1
                posSum += 1
            elif (sub_table[j][DIRECTION_INDEX] == -1):
                hour_info['negNum'] += 1
                negSum += 1
            data_list.append(hour_info)
            hour_num += 1
        else:
            hour_info = data_list[hour_index]
            if (sub_table[j][DIRECTION_INDEX] == 1):
                hour_info['posNum'] += 1
                posSum += 1
            elif (sub_table[j][DIRECTION_INDEX] == -1):
                hour_info['negNum'] += 1
                negSum += 1

    '''test2_list = sorted(test2_list,key = itemgetter(LNG_INDEX,LAT_INDEX))
    count2 = 0
    for i in range(len(test_list)):
        if(test_list[i][LNG_INDEX] == test2_list[i][LNG_INDEX] and test_list[i][LAT_INDEX] == test2_list[i][LAT_INDEX]):
            count2 += 1
    if(count2 == len(test_list)):
        print("YES")
    else:
        print("NO")'''
    data_list = sorted(data_list, key=itemgetter('datatime'))
    # for data in data_list:
    #     data['posNum'] = data['posNum'] / date_num
    #     data['negNum'] = data['negNum'] / date_num

    stat_dict = {'pos': {'sum': posSum}, 'neg': {'sum': negSum}}
    return [data_list, stat_dict, [date_hour_min, date_hour_max]]



#获取在矩形区域内的所有数据点
#通过max_index来选择需要返回哪些数据
#通过area_type来判断是否在矩形区域内，或多边形区域内，area_type==0表示矩形，area_type==1表示多边形
#通过data_type来返回不同类型的Json格式
def get_points_in_region(table_arr,type_index_list,area_points_list,border_list,area_type,data_type):
    points_info_dict = {}
    table_arr_length = len(table_arr)
    points_info_dict['statistic'] = {}
    points_info_dict['date_list'] = []
    points_date_dict = {}

    table_date = table_arr[0][0][DATE_TIME_INDEX]
    date_hour_min = datetime.datetime(*tuple(table_date)[0:4])
    date_hour_max = datetime.datetime(*tuple(table_date)[0:4])
    max_num, day_dict, day_num, day_list = 0, {}, 0, []

    for i in range(table_arr_length):
        table = table_arr[i]
        #得到一种违章类型的list,之前在helper中处理数据时就已经按照先经度，后纬度的顺序排好序了
        min_lng_index = lower_bound_search(table, 0, len(table), border_list[0], LNG_INDEX)
        max_lng_index = upper_bound_search(table, 0, len(table), border_list[1], LNG_INDEX)-1  #upper_bound函数求出来的是小于这个数字的最大数
        sub_table = sorted(table[min_lng_index:max_lng_index+1], key=itemgetter(LAT_INDEX))  #将在经度范围内的数据再次按照纬度重新排序

        min_final_index = lower_bound_search(sub_table, 0, len(sub_table), border_list[2], LAT_INDEX)
        max_final_index = upper_bound_search(sub_table, 0, len(sub_table), border_list[3], LAT_INDEX)-1

        data_list, stat_dict, date_hour_list, tmp_num, tmp_day_list = [], {}, {}, 0, 0
        if (data_type == 0):
            pass
        elif (data_type == 1):
            [data_list, stat_dict, date_hour_list, tmp_num, tmp_day_list] = get_time_data_list(sub_table, min_final_index, max_final_index, area_points_list, border_list, area_type)
        elif (data_type == 2):
            [data_list, stat_dict, date_hour_list] = get_sum_data_list(sub_table, min_final_index, max_final_index, area_points_list, border_list, area_type)
        if(date_hour_list[0] < date_hour_min):
            date_hour_min = date_hour_list[0]
        if(date_hour_list[1] > date_hour_max):
            date_hour_max = date_hour_list[1]
        max_num = max(max_num, tmp_num)
        for day in tmp_day_list:
            str_day = str(day[0]) + str(day[1]) +str(day[2])
            day_index = day_dict.get(str_day, -1)
            if(day_index == -1):
                day_dict[str_day] = day_num
                day_list.append(day)
                day_num += 1
        #for key,value in date_dict.items():
            #if(points_date_dict.get(key,-1) == -1):
               # points_date_dict[key] = value
        points_info_dict['type' + str(type_index_list[i]) ] = data_list
        points_info_dict['statistic']['type' + str(type_index_list[i]) ] = stat_dict

    day_list = sorted(day_list)
    for i in range(len(day_list)):
        day_info =day_list[i]
        str_day = str(day_info[0]) +str(day_info[1]) +str(day_info[2])
        day_dict[str_day] = i
    day_list_len = len(day_list)
    for i in range(day_list_len):
        day = day_list[i]
        day_list[i] = [day[0], day[1], day[2], 0]

    for i in range(table_arr_length):
        table = points_info_dict['type' + str(type_index_list[i])]
        data_time_list = table[0]['datatime']
        str_day = str(data_time_list[0])+str(data_time_list[1]) + str(data_time_list[2])
        day_index = day_dict.get(str_day,0)
        for j in range(day_index):
            for k in range(24):  #插入24小时空余数据
                day_info = day_list[j]
                tmp_day_dict = {'datatime':(day_info[0],day_info[1],day_info[2],k),'posNum':0,'negNum':0}
                table.insert(j*24+k, tmp_day_dict)


    '''max_index = len(day_list) - 1
    date_day = day_list[max_index]
    date_last_day = datetime.datetime(date_day[0], date_day[1], date_day[2], 0)
    date_last_day = date_last_day + datetime.timedelta(days = 1)
    day_list.append([date_last_day.year, date_last_day.month, date_last_day.day, 0])'''



    tmp_list = []
    for key, value in points_date_dict.items():
        tmp_list.append([key,value])
    tmp_list = sorted(tmp_list, key = itemgetter(1))


    date_list = []

    d_minus = date_hour_max - date_hour_min

    hours = int((d_minus.days * 24 * 60 * 60 + d_minus.seconds) / 3600.0)
    time_min = date_hour_min.time()
    t_h = time_min.hour
    date_min = date_hour_min.date()
    date_time_min = datetime.datetime(date_min.year, date_min.month, date_min.day, t_h, 0, 0)
    date_dict, date_info_num = {}, 0

    for hour in range(hours+1):
        datetmp = date_time_min + datetime.timedelta(hours=hour)
        #str_date_info = str(datetmp.hour) + ':' + str(0) + '\n' + str(datetmp.month) + '/' + str(datetmp.day)
        str_date_info = str(datetmp.month) + '/' + str(datetmp.day) + '\n' + str(datetmp.hour) + ':00'
        date_list.append(str_date_info)
        date_dict[str_date_info] = date_info_num
        date_info_num += 1
    #points_info_dict = convert_points_info(points_info_dict, table_arr_length)

    points_info_dict = get_three_list(points_info_dict, date_dict, type_index_list)

    points_info_dict['day_list'] = day_list
    points_info_dict['max_num'] = max_num

    points_info_dict['date_list'] = date_list

    return points_info_dict


def addEntityToList(dict1,key,date_index,dict2,def_type):
    if(date_index + 1 > len(dict1[key])):
        for i in range(max(0,len(dict1[key])-1),date_index+1):
            dict1[key].append(def_type)
    if(def_type!=0 and dict2.get(key,def_type) == def_type):
        print('YES')
    dict1[key][date_index] = dict2.get(key,def_type)

def get_three_list(point_dict, date_dict, type_index_list):
    point_info_dict = {}
    for i in type_index_list:
        table = point_dict['type' + str(i)]
        table_len = len(table)
        table_info_dict = {'datatime':[], 'posNum':[], 'negNum':[]}
        for j in range(table_len):
            tmplist = table[j]['datatime']
            table[j]['datatime'] = str(tmplist[1]) + '/' + str(tmplist[2]) + '\n' + str(tmplist[3]) + ':00'
            date_index = date_dict.get(table[j]['datatime'], -1)
            if(date_index != -1):
                addEntityToList(table_info_dict, 'datatime', date_index, table[j], [])
                addEntityToList(table_info_dict, 'posNum', date_index, table[j], 0)
                addEntityToList(table_info_dict, 'negNum', date_index, table[j], 0)
        j = 0
        while(j< len(table_info_dict['datatime']) and len(table_info_dict['datatime'][j]) == 0):
            j += 1

        for k in range(j):
            table_info_dict['datatime'].pop(0)
            table_info_dict['posNum'].pop(0)
            table_info_dict['negNum'].pop(0)

        point_info_dict['type' + str(i)] = table_info_dict
    return point_info_dict

def convert_points_info(points_info_dict, type_length):
    date_time_dict = {}
    date_list = points_info_dict['date_list']
    date_list_length = len(date_list)

    for i in range(date_list_length):
        date = date_list[i]
        date_time_dict[date] = i

    for i in range(type_length):
        type_points_list = points_info_dict['type'+str(i+1)]
        type_points_list_length = len(type_points_list)
        date_points_list = []
        for j in range(date_list_length):
            date_points_list.append({'posNum': 0, 'negNum': 0})

        for j in range(type_points_list_length):
            type_point = type_points_list[j]

            date = type_point['datatime']

            str_date = str(date[3]) + ':' + str(0) + '\n' + str(date[1]) + '/' + str(date[2])

            date_time_index = date_time_dict.get(str_date, -1)
            point = date_points_list[date_time_index]
            point['posNum'] += type_point['posNum']
            point['negNum'] += type_point['negNum']
        points_info_dict['type'+str(i+1)] = date_points_list
    return points_info_dict



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
    split_show = int(request.GET.get("split_show", 0))

    file_names=os.listdir(BASE_DIR+os.sep+"static"+os.sep+"theme")
    theme_names=[]
    static_theme_url=[]
    for filename in file_names:
        theme_name=filename.split(".")[0]
        static_theme_url.append('/static/theme/'+theme_name)
        theme_names.append(theme_name)
    selected_index=5
    data_type=int(request.GET.get("data_type",0))
    if split_show==1:
        return render(request, 'transport/diffcolor_split.html',locals())
    else:
        return render(request, 'transport/diffcolor3.html', locals())
def echarts(request):
    return render(request, 'transport/echarts.html',locals())