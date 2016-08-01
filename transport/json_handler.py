# coding: utf-8
import os,json,datetime,math,re
from Transport_Web.settings import BASE_DIR
from os.path import normpath,join
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
if __name__ == '__main__':
    option=generate_option_template(title=True,tooltip=False,dataZoom=True,legend=True,toolbox=True,grid=True,xAxis=True,yAxis=True,series=True)

    option_json = json.dumps(option, sort_keys=True, indent=4)
    put_data_into_json(option)
    print(option_json)