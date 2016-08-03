# coding: utf-8
import os,json,datetime,math,re
from Transport_Web.settings import BASE_DIR
from os.path import normpath,join
DATA_TYPE_DICT = {0:"全部类型数据",1:"应急车道",2:"违反指示标线",3:"非机动车道",4:"公交车道"}
LEGEND_NAMES=["顺时针道路","逆时针道路"]
LEGEND_NAMES_SHORT=["顺","逆"]
DATA_TYPE_LIST=["posNum","negNum"]
OPTION_ROOT_DIR=normpath(join(BASE_DIR,'static','option'))
def generate_option_template(title=True,tooltip=True,dataZoom=True,legend=True,toolbox=True,grid=True,xAxis=True,yAxis=True,series=True):
    option={}
    if title:
        option["title"]={}
    if tooltip:
        option["tooltip"]={}
    if dataZoom:
        option["dataZoom"]={}
    if legend:
        option["legend"]={}
    if toolbox:
        option["toolbox"]={}
    if grid:
        option["grid"]={}
    if xAxis:
        option["xAxis"]={}
    if yAxis:
        option["yAxis"]={}
    if series:
        option["series"]={}
    return option
def put_data_into_json(option_arg,out_file_path,title="title",legend_names=[],xAxisData=[],seriesDictList=[]):
    option=option_arg
    option["title"]["text"]=title
    option["legend"]["data"]=legend_names
    if len(xAxisData):
        option["xAxis"][0]["data"]=xAxisData
    option["series"]=seriesDictList

    option_file=open(out_file_path,"w")
    print ("now writing option file")
    option_str=json.dumps(option, sort_keys=True, indent=4)
    option_file.write(option_str)
    option_file.close()
    print ("option file writed!")
def get_json_template_from(file_path):
    fp=open(file_path,"r")
    json_str = json.loads(json.dumps(fp.read()))
    json_obj = json.loads(json_str)
    fp.close()
    return json_obj
def generate_series_dict(point_type,legend_names,data_type_list,type_of_series,datelist_data,**series_dict):
    ret_arr=[]
    #单个的情况

    if point_type!=0:

        for i in range(len(legend_names)):
            item={}
            item["name"]=legend_names[i]
            item["type"]=type_of_series
            item["data"]=series_dict["type"+str(point_type)][data_type_list[i]]
            mark_point={}
            mark_point["data"]=[{"type": "max", "name": "最大值"}]
            item["markPoint"]=mark_point
            ret_arr.append(item)
    else:
        for i in range(1,5):
            for j in range(2):
                idx=2*i+j-2
                item={}
                item["name"]=legend_names[idx]
                item["type"]=type_of_series
                item["data"]=series_dict["type"+str(i)][data_type_list[j]]
                ret_arr.append(item)
    return ret_arr
def generate_multi_series_dict(point_type,legend_names,type_of_series,**corr_dict):
    ret_arr=[]
    #单个的情况

    if point_type!=0:
        for i in range(len(legend_names)):
            item={}
            item["name"]=legend_names[i]
            item["type"]=type_of_series
            offset = i%2
            item["data"]=corr_dict["type"+str(point_type)][offset]
            ret_arr.append(item)
    else:
        for i in range(1,5):
            for j in range(2):
                idx=2*i+j-2
                item={}
                item["name"]=legend_names[idx]
                item["type"]=type_of_series
                item["data"]=corr_dict["type"+str(i)][j]
                ret_arr.append(item)
    return ret_arr
def generate_multi_option(point_type,json_file_name,plot_type,**corr_dict):
    option_origin_path = OPTION_ROOT_DIR + os.sep + "option_multi_corr.json"
    option = get_json_template_from(option_origin_path)
    out_option_file_path = OPTION_ROOT_DIR + os.sep +json_file_name
    data_type_name = DATA_TYPE_DICT[point_type]
    title_name = data_type_name + "_多区域相关性结果"
    if point_type == 0:
        legend_names = []
        for i_tmp in range(1, 5):
            for j_tmp in range(len(LEGEND_NAMES)):
                tmp_str = DATA_TYPE_DICT[i_tmp] + "_" + LEGEND_NAMES_SHORT[j_tmp]
                legend_names.append(tmp_str)
    else:
        legend_names = LEGEND_NAMES
    seriesDictList = generate_multi_series_dict(point_type, legend_names,plot_type,**corr_dict)
    put_data_into_json(option, out_option_file_path, title=title_name, legend_names=legend_names, seriesDictList=seriesDictList)
def generate_delay_option(point_type,json_file_name,plot_type,**corr_dict):
    option_origin_path = OPTION_ROOT_DIR + os.sep + "option_delay_corr.json"

    option = get_json_template_from(option_origin_path)
    out_option_file_path = OPTION_ROOT_DIR + os.sep +json_file_name
    data_type_name = DATA_TYPE_DICT[point_type]
    title_name = data_type_name + "_相关性与延时的关系"
    if point_type == 0:
        legend_names = []
        for i_tmp in range(1, 5):
            for j_tmp in range(len(LEGEND_NAMES)):
                tmp_str = DATA_TYPE_DICT[i_tmp] + "_" + LEGEND_NAMES_SHORT[j_tmp]
                legend_names.append(tmp_str)
    else:
        legend_names = LEGEND_NAMES
    seriesDictList = generate_delay_series_dict(point_type, legend_names,plot_type,**corr_dict)
    put_data_into_json(option, out_option_file_path, title=title_name, legend_names=legend_names, seriesDictList=seriesDictList)
def generate_delay_series_dict(point_type,legend_names,type_of_series,**series_dict):
    ret_arr=[]
    #单个的情况
    if point_type!=0:
        type_dict=series_dict["type"+str(point_type)]
        type_dict_sorted= sorted(type_dict.iteritems(), key=lambda d:d[0])
        data_list_for_use=[]
        for (delay_time,corr_list_tmp) in type_dict_sorted.items():
            for tmp_i in range(len(corr_list_tmp)):
                while len(data_list_for_use)<len(corr_list_tmp):
                    data_list_for_use.append([])
                data_list_for_use[tmp_i].append([delay_time,corr_list_tmp[tmp_i]])
        for i in range(len(legend_names)):
            item={}
            item["name"]=legend_names[i]
            item["type"]=type_of_series
            item["data"]=data_list_for_use[i]
            ret_arr.append(item)
    #所有类型点
    else:
        data_list_for_use=[]
        for i in range(1,5):

            type_dict=series_dict["type"+str(i)]
            type_dict_sorted= sorted(type_dict.iteritems(), key=lambda d:d[0])
            for (delay_time,corr_list_tmp) in type_dict_sorted:
                for tmp_i in range(len(corr_list_tmp)):
                    while len(data_list_for_use)< (2*(i-1)+len(corr_list_tmp)):
                        data_list_for_use.append([])
                    idx_now=2*(i-1)+tmp_i
                    data_list_for_use[idx_now].append([delay_time,corr_list_tmp[tmp_i]])
            for j in range(1,3):
                idx=2*i+(j-1)-2
                item={}
                item["name"]=legend_names[idx]
                item["type"]=type_of_series
                now_idx=2*i+(j-1)-2
                item["data"]=data_list_for_use[now_idx]
                ret_arr.append(item)
    return ret_arr
def generate_option(point_type,json_file_name,plot_type,**points_info_dict):
    option_origin_path = OPTION_ROOT_DIR + os.sep + "option1_origin.json"
    option = get_json_template_from(option_origin_path)
    out_option_file_path = OPTION_ROOT_DIR + os.sep + json_file_name
    data_type_name = DATA_TYPE_DICT[point_type]
    title_name = data_type_name + "举报量与时间的关系"
    if point_type == 0:
        datelist_data = points_info_dict["date_list"]
        legend_names = []
        for i_tmp in range(1, 5):
            for j_tmp in range(len(LEGEND_NAMES)):
                tmp_str = DATA_TYPE_DICT[i_tmp] + "_" + LEGEND_NAMES_SHORT[j_tmp]
                legend_names.append(tmp_str)
    else:
        datelist_data = points_info_dict["type" + str(point_type)]["datatime"]
        legend_names = LEGEND_NAMES
    seriesDictList = generate_series_dict(point_type, legend_names, DATA_TYPE_LIST,plot_type, datelist_data,
                                          **points_info_dict)
    put_data_into_json(option, out_option_file_path, title=title_name, legend_names=legend_names,
                       xAxisData=datelist_data, seriesDictList=seriesDictList)
if __name__ == '__main__':
    option=generate_option_template(title=True,tooltip=False,dataZoom=True,legend=True,toolbox=True,grid=True,xAxis=True,yAxis=True,series=True)

    option_json = json.dumps(option, sort_keys=True, indent=4)
    put_data_into_json(option)
    print(option_json)