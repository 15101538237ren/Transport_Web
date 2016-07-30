# coding: utf-8
import os,json,datetime,math
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
def put_data_into_json(option_arg,title="title",legend_names=[],xAxisData=[],yAxisDictList=[],seriesDictList=[]):
    option=option_arg
    option["title"]={"text": title,"x":"center"}
    option["legend"]={"data":legend_names,"x": "left"}
    option["xAxis"]=[{"type" : 'category',"boundaryGap" : False,"data":xAxisData}]
    option["yAxis"]=yAxisDictList
    option["series"]=seriesDictList

    option_file=open(OPTION_ROOT_DIR+os.sep+"option1.json","w")
    print ("now writing option file")
    option_str=json.dumps(option, sort_keys=True, indent=4)
    option_file.write(option_str)
    option_file.close()
    print ("option file writed!")
if __name__ == '__main__':
    option=generate_option_template(title=True,tooltip=False,dataZoom=True,legend=True,toolbox=True,grid=True,xAxis=True,yAxis=True,series=True)

    option_json = json.dumps(option, sort_keys=True, indent=4)
    put_data_into_json(option)
    print(option_json)