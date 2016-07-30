# coding: utf-8
import os,json,datetime,math
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

if __name__ == '__main__':
    option=generate_option_template(title=True,tooltip=False,dataZoom=True,legend=True,toolbox=True,grid=True,xAxis=True,yAxis=True,series=True)

    option_json = json.dumps(option, sort_keys=True, indent=4)
    print(option_json)