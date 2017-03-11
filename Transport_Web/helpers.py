# coding: utf-8
import os,xlrd,json,pickle,math,sys,datetime,pytz
from django.http import HttpResponse, JsonResponse
from Transport_Web.settings import BASE_DIR,STATIC_ROOT
from operator import itemgetter, attrgetter


MAXINT = 999999999
EPS = 0.000001
ERROR_EPS = 0.00008


#表示原始Excel中相应属性的索引
EXCEL_LNG_INDEX =  4
EXCEL_LAT_INDEX = 3
EXCEL_DATE_INDEX = 5

#表示data/input/road下的所有道路的json文件中道路边界点的经纬度的索引
ROAD_DATA_LNG_INDEX = 0
ROAD_DATA_LAT_INDEX = 1


#保存的数据相应字段的索引，文件包括pkl和js
LNG_INDEX = 0
LAT_INDEX = 1
DATE_TIME_INDEX = 2
DIRECTION_INDEX = 3

ROAD_DIR=BASE_DIR+ os.sep+'data'+ os.sep + 'input' + os.sep +'road'
POINT_OUTPUT_DIR = BASE_DIR+ os.sep+'data'+ os.sep + 'output'

def success_response(response=None):
    return JsonResponse({"code": 0, "message": response})

#从Excel中读取数据
#date_option表示是否读取日期，date_option=1表示读取日期，date_option=0表示不读取
#all_optioin表示是否将所有不同违章类型的点都保存在同一个List中，all_option=1表示将所有点都保存在同一个List中，all_option=0表示将不同类型的点保存在不同的List中

def data_read_and_store(excel_path,pickle_path,date_option = 0,all_option=1):
    out_pickle = open(pickle_path, 'wb')
    data = xlrd.open_workbook(excel_path)
    table_arr=[]
    sheet_length = len(data.sheets())
    for i in range(sheet_length):
        sheet_data=[]
        table = data.sheets()[i]  #获取第一个sheet
        nrows = table.nrows #表示当前excel表格的行数
        #ncols = table.ncols #表示当前excel表格的列数
        for i in range(1,nrows):
            try:
                str_lng = table.row(i)[EXCEL_LNG_INDEX].value
                str_lat = table.row(i)[EXCEL_LAT_INDEX].value
                date = 0
                if(date_option == 1):
                    date = xlrd.xldate_as_tuple(table.row(i)[EXCEL_DATE_INDEX].value, 0)
                if str_lat!="" and str_lng!="":
                    lat=float(str_lat.encode("utf-8"))
                    lng=float(str_lng.encode("utf-8"))
                    if(date_option ==1):
                        if(all_option==0):
                            sheet_data.append([lng,lat,date])
                        else:
                            table_arr.append([lng,lat,date])
                    else:
                        if(all_option==0):
                            sheet_data.append([lng,lat])
                        else:
                            table_arr.append([lng,lat])
            except Exception as e:
                print(e)
        if(all_option==0):
            sheet_data = sorted(sheet_data,key=itemgetter(LNG_INDEX,LAT_INDEX))  #将数据点先按照经度排序，然后再按照纬度排序
            table_arr.append(sheet_data)
    if(all_option==1):
        table_arr = sorted(table_arr,key=itemgetter(LNG_INDEX,LAT_INDEX)) #将数据点先按照经度排序，然后再按照纬度排序
    pickle.dump(table_arr,out_pickle,-1)
    out_pickle.close()

#读取道路的Json格式的文件
def road_read_and_store(road_dir,pickle_path):
    out_pickle = open(pickle_path, 'wb')
    roadset = []
    for root,dirnames,filenames in os.walk(road_dir):   # 三个参数：分别返回1.父目录 2.所有文件夹名字（不含路径） 3.所有文件名字
        for filename in filenames:  #遍历该目录下的所有存储path的json文件
            roadfile= open(road_dir + os.sep + filename,'r')
            text = roadfile.read()
            roaddata = json.loads(text)  #获取到道路的数据集
            minX,maxX,minY,maxY = MAXINT,0,MAXINT,0
            #给道路的json文件中添加道路最小x,最小y,最大x,最大y的值
            for road in roaddata['data']:
                minX,maxX = min(minX,road[ROAD_DATA_LNG_INDEX]),max(maxX,road[ROAD_DATA_LNG_INDEX])
                minY, maxY= min(minY,road[ROAD_DATA_LAT_INDEX]),max(maxY,road[ROAD_DATA_LAT_INDEX])
            roaddata['minX'],roaddata['maxX'] = minX,maxX
            roaddata['minY'],roaddata['maxY'] = minY,maxY
            roadfile = open(road_dir + os.sep + filename, 'w')
            jsondata = json.dumps(roaddata,sort_keys=True,indent=4)
            roadfile.write(jsondata)
            roadset.append(roaddata)
    pickle.dump(roadset, out_pickle, -1)
    roadfile.close()
    out_pickle.close()


def load_pickle_from(pickle_path=STATIC_ROOT+os.sep+'WFJBXX_ORG.pkl'):
    f = open(pickle_path, 'rb')
    #print "now loading data.pkl"
    table_arr=pickle.load(f)
    f.close()
    return table_arr


#检查一个点是否在道路的多边形区域内
#如果在多边形内，返回值为1
#如果在多边形外，但是离多边形的某条边很近(在误差允许范围内)，返回值为2
#如果在多边形外，而且离多边形很远，返回值为0


def check_point(dataset,lng,lat):
    flag,minDis,x0,y0,count,length,j = 0,MAXINT,MAXINT,lat,0,len(dataset),len(dataset)-1
    for i in range(0,length):
        #数据点正好和多边形路段边界点重合
        if (math.fabs(dataset[i][LNG_INDEX]-lng) < EPS and math.fabs(dataset[i][LAT_INDEX]-lat) < EPS):
            flag = 1
            break
        #下面计算射线与线段的交点个数，判断点是否在多边形内
        #经度相同时，相当于线段竖直
        if (math.fabs(dataset[i][LNG_INDEX] - dataset[j][LNG_INDEX]) < EPS):
            minY = min(dataset[i][LAT_INDEX], dataset[j][LAT_INDEX])
            maxY = max(dataset[i][LAT_INDEX], dataset[j][LAT_INDEX])
            if (minY <= lat and lat <= maxY):
                dis = math.fabs(lng - dataset[i][LNG_INDEX])
                minDis = min(minDis, dis)
                if(dataset[i][LNG_INDEX]>=lng):  #保证射线是向右的，所以这里求交点的时候，交点不能在数据点左侧
                    count +=1
        else:
            #线段平行
            if(math.fabs(dataset[i][LAT_INDEX]-dataset[j][LAT_INDEX])<EPS):
                minX = min(dataset[i][LNG_INDEX], dataset[j][LNG_INDEX])
                maxX = max(dataset[i][LNG_INDEX], dataset[j][LNG_INDEX])
                if (minX <= lng and lng <= maxX):
                    dis = math.fabs(lat - dataset[i][LAT_INDEX])
                    minDis = min(minDis, dis)
                    continue
            else:
                kij = (dataset[j][LAT_INDEX] - dataset[i][LAT_INDEX]) / (dataset[j][LNG_INDEX] - dataset[i][LNG_INDEX])
                #yij = k(x - xi) + yi与y = lat相交求点引出的射线与多边形边的交点
                #k不会为0

                #求点到直线的距离
                # yij= kij*(x-dataset[i][0])+dataset[i][1]
                # ypj=-1/kij*(x-lng)+lat
                x0 = (kij * dataset[i][LNG_INDEX] - dataset[i][LAT_INDEX] + lng / kij + lat) / (kij + 1 / kij)
                y0 = -1 / kij * (x0 - lng) + lat
                xPos = (lat - dataset[i][LAT_INDEX]) / kij + dataset[i][LNG_INDEX]
                minX = min(dataset[i][LNG_INDEX], dataset[j][LNG_INDEX])
                maxX = max(dataset[i][LNG_INDEX], dataset[j][LNG_INDEX])
                minY = min(dataset[i][LAT_INDEX], dataset[j][LAT_INDEX])
                maxY = max(dataset[i][LAT_INDEX], dataset[j][LAT_INDEX])
                if (minX <= x0 and x0 <= maxX and minY <= y0 and y0 <= maxY):
                    # 向量a = (lng-xj, lat-yj)
                    # 向量b = (xi-xj, yi-yj)
                    cross = (lng - dataset[j][LNG_INDEX]) * (dataset[i][LAT_INDEX] - dataset[j][LAT_INDEX]) - (dataset[i][LNG_INDEX] - dataset[j][LNG_INDEX]) * (lat - dataset[j][LAT_INDEX])
                    dis = math.fabs(cross / math.sqrt(math.pow(dataset[i][LNG_INDEX] - dataset[j][LNG_INDEX], 2) + math.pow(dataset[i][LAT_INDEX] - dataset[j][LAT_INDEX], 2)))
                    minDis = min(minDis, dis)

                if (max(minX, lng) <= xPos and xPos <= maxX and minY <= lat and lat <= maxY):
                    count +=1
        j = i

    if (count % 2 == 1):
        flag = 1
    else:
        #只有在判断出来点在多边形外的时候才会判断这个点离多边形的所有边的最近距离，这时候使用EPS来控制对误差的容忍度
        if(minDis<ERROR_EPS):
            flag = 2

    return [flag,minDis]



#标注所有点，将标注了方向的数据点保存在新的文件中
#type为0表示js文件中存储所有类型的数据点，type为1表示js文件中分不同类型存储数据点
def label_points(data_path,road_path,out_data_path,type,out_newjsdata_path = POINT_OUTPUT_DIR + os.sep + 'pathpoints.js'):
    datafile = open(data_path, 'rb')
    roadfile = open(road_path, 'rb')
    labeldatafile = open(out_data_path, 'wb')
    jsdatafile = open(out_newjsdata_path,'w')
    pathpoints,pathpoints_js = [],[]

    dataset = pickle.load(datafile)  # 获取所有数据点的list
    roadset = pickle.load(roadfile)  # 获取到所有road的list
    dataset_length = len(dataset)  #提前计算好List的长度，提高效率
    for i in range(dataset_length):  #遍历excel数据中的len(dataset)个sheet
        typepoints = []
        for point in dataset[i]:  # 遍历dataset中的每一个数据点
            flag,minDis,pos = 0,MAXINT,0
            #pos用来记录与这个点离的最近的道路的index
            roadset_length = len(roadset)   #提前计算好List的长度，提高效率
            for j in range(roadset_length):  # 遍历roadset中的每一条道路
                if (not (roadset[j]['minX'] <= point[LNG_INDEX] and point[LNG_INDEX] <= roadset[j]['maxX'] and
                    roadset[j]['minY'] <=point[LAT_INDEX] and point[LAT_INDEX] <= roadset[j]['maxY'])):
                    continue

                [status,dis] = check_point(roadset[j]['data'],point[LNG_INDEX],point[LAT_INDEX])
                point_info = [point[LNG_INDEX],point[LAT_INDEX],point[DATE_TIME_INDEX],roadset[j]['direction']]
                if(status==1):
                    flag = 1
                    #如果找到这个点属于某个多边形，则提前break跳出循环
                    typepoints.append(point_info)
                    if(type==0):
                        pathpoints_js.append(point_info)
                    break
                elif(status==2):
                    if(dis<minDis):
                        flag,pos,minDis = 2,j,min(minDis,dis)
            point_info = [point[LNG_INDEX], point[LAT_INDEX], point[DATE_TIME_INDEX]]
            if(flag==0):
                point_info.append(0)
                typepoints.append(point_info)
                if(type==0):
                    pathpoints_js.append(point_info)
            elif(flag==2):
                point_info.append(roadset[pos]['direction'])
                typepoints.append(point_info)
                if(type==0):
                    pathpoints_js.append(point_info)
        typepoints = sorted(typepoints, key = itemgetter(LNG_INDEX,LAT_INDEX))
        pathpoints.append(typepoints)
    pickle.dump(pathpoints, labeldatafile, -1)

    if(type==0):
        pathpoints_js = sorted(pathpoints_js, key = itemgetter(LNG_INDEX,LAT_INDEX))  #提前按照先经度，后纬度的顺序排序，便于后续处理
        pathpoints_str = json.dumps(pathpoints_js)
    else:
        pathpoints_str = json.dumps(pathpoints)
    jsdata = 'var pathpoints={\"data\":'+ pathpoints_str + ',\"total\":' + str(len(pathpoints_js)) + ',\"rt_loc_cnt\":'+ str(len(pathpoints_js)) +\
     ',\"errorno\": 0,\"nearestTime\": \"2014-08-29 15:20:00\",\"userTime\": \"2014-08-29 15:32:11\"}'
    jsdatafile.write(jsdata)
    datafile.close()
    roadfile.close()
    labeldatafile.close()
    jsdatafile.close()

def convert_point_list_to_path_file(point_lists,direction):
    split='\n\t'
    tz=pytz.timezone(pytz.country_timezones('cn')[0])
    now_str=datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    json_str='{'+split+'"data": ['+split

    points_str_list=[]
    for point in point_lists:
        points_str='['+str(point["lng"])+', '+str(point["lat"])+']'
        points_str_list.append(points_str)
    json_str=json_str+(","+split).join(points_str_list)+split
    json_str=json_str+'],'+split+'"total": '+str(len(point_lists))+','+split+'"rt_loc_cnt": '+str(len(point_lists))+','+split+'"errorno": 0,'+split+'"direction":'+str(direction)+','+split+'"nearestTime": "'+now_str+'",'+split+'"userTime": "'+now_str+'"'+'\n}'
    return json_str

def get_all_paths(from_dir_path=ROAD_DIR):
    roads_set = []
    roads_directions=[]
    for root,dirnames,filenames in os.walk(from_dir_path):   # 三个参数：分别返回1.父目录 2.所有文件夹名字（不含路径） 3.所有文件名字
        for filename in filenames:  #遍历该目录下的所有存储path的json文件
            roadfile= open(from_dir_path + os.sep + filename,'r')
            text = roadfile.read()
            roaddata = json.loads(text)  #获取到道路的数据集
            roads_set.append(roaddata["data"])
            roads_directions.append(roaddata["direction"])
    return roads_set,roads_directions


def poly_line_js(roads_set,roads_directions):
    roads_set_str=json.dumps(roads_set)
    road_directions_str=json.dumps(roads_directions)
    js_code='var point_set='+roads_set_str+';\n'
    js_code=js_code+'var roads_directions='+road_directions_str+';\n'
    js_code=js_code+'for (var i = 0; i < point_set.length; i++) {\n'
    js_code=js_code+'   var points_i=[];\n'
    js_code=js_code+'   for (var j = 0; j < point_set[i].length; j++)\n'
    js_code=js_code+'   { \n'
    js_code=js_code+'       var point_to_add=new BMap.Point(point_set[i][j][0], point_set[i][j][1]);\n'
    js_code=js_code+'       points_i.push(point_to_add);\n'
    js_code=js_code+'   }\n'
    js_code=js_code+'   if (roads_directions[i]=="1")\n'
    js_code=js_code+'   {\n'
    js_code=js_code+'       var color="red";\n'
    js_code=js_code+'   }\n'
    js_code=js_code+'   else\n'
    js_code=js_code+'   {\n'
    js_code=js_code+'       var color="blue";\n'
    js_code=js_code+'   }\n'
    js_code=js_code+'   var polyline = new BMap.Polyline(points_i,{strokeColor:color, strokeWeight:3, strokeOpacity:1.0});\n'
    js_code=js_code+'   polyline.addEventListener("click", function(e) {\n'
    js_code=js_code+'   alert("单击点的坐标为：" + e.point.lng + "," + e.point.lat);\n'
    js_code=js_code+'   });\n'
    js_code=js_code+'   map.addOverlay(polyline); \n' \
                    '}'
    return js_code




if __name__ == '__main__':

    excel_path=STATIC_ROOT+os.sep+"WFJBXX_ORG.xls"
    out_pickle_path=STATIC_ROOT+os.sep+"WFJBXX_ORG.pkl"
    out_pickle_path_all = STATIC_ROOT+os.sep+"WFJBXX_ORG_ALL.pkl"
    #data_read_and_store(excel_path,out_pickle_path)
    #data_read_and_store(excel_path,out_pickle_path,1,0)
    #data_read_and_store(excel_path, out_pickle_path_all, 1, 1)
    # data_file=open(out_pickle_path,"rb")
    # dataset = pickle.load(data_file)  # 获取所有数据点的list
    # data_file.close()

    #
    # excel_exception_path = STATIC_ROOT+os.sep+"exception.xlsx"
    # out_exception_pickle_path = STATIC_ROOT + os.sep + "Exception.pkl"
    # #data_read_and_store(excel_exception_path, out_exception_pickle_path)
    #
    #将road_path整个目录下的path都存储成pkl格式
    out_road_path=STATIC_ROOT+os.sep+'path.pkl'
    #road_read_and_store(ROAD_DIR,out_road_path)
    out_labeled_points_path = STATIC_ROOT + os.sep + 'labeledpoints.pkl'
    label_points(out_pickle_path, out_road_path, out_labeled_points_path,1)
    # label_points(out_pickle_path, out_road_path, out_labeled_points_path,0,POINT_OUTPUT_DIR + os.sep + 'pathpoints_all.js')
    #
    #
    # out_exception_data_path = STATIC_ROOT + os.sep + 'exceptiondata.pkl'
    # out_exception_js_path = STATIC_ROOT + os.sep + 'exceptionpoints.js'
    # #label_points(out_exception_pickle_path, out_road_path, out_exception_data_path,0,out_exception_js_path)
    #roads_set,roads_directions=get_all_paths()
    #poly_line_js(roads_set,roads_directions)
