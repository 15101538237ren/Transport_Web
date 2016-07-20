# coding: utf-8
import os,xlrd,json,pickle,math,sys,datetime,pytz
from django.http import HttpResponse, JsonResponse
from Transport_Web.settings import BASE_DIR,STATIC_ROOT
MAXINT = 999999999
EPS = 0.000001
ERROR_EPS = 0.00008
ROAD_DIR=BASE_DIR+ os.sep+'data'+ os.sep + 'input' + os.sep +'road'
POINT_OUTPUT_DIR = BASE_DIR+ os.sep+'data'+ os.sep + 'output'

def success_response(response=None):
    return JsonResponse({"code": 0, "message": response})
def data_read_and_store(excel_path,pickle_path):
    out_pickle = open(pickle_path, 'wb')
    data = xlrd.open_workbook(excel_path)
    table_arr=[]

    for i in range(len(data.sheets())):
        sheet_data=[]
        table = data.sheets()[i]  #获取第一个sheet
        nrows = table.nrows #表示当前excel表格的行数
        ncols = table.ncols #表示当前excel表格的列数
        #print(nrows)
        #print(type(table.row(1)[4].value))
        for i in range(1,nrows):
            try:
                str_lat=table.row(i)[4].value
                str_lon=table.row(i)[3].value
                if str_lat!="" and str_lon!="":
                    lat=float(str_lat.encode("utf-8"))
                    lon=float(str_lon.encode("utf-8"))
                    sheet_data.append([lat,lon])
            except Exception as e:
                print(e)
        table_arr.append(sheet_data)
    pickle.dump(table_arr,out_pickle,-1)
    out_pickle.close()


def data_time_read_and_store(excel_path,pickle_path):
    out_pickle = open(pickle_path, 'wb')
    data = xlrd.open_workbook(excel_path)
    table_arr=[]

    for i in range(len(data.sheets())):
        sheet_data=[]
        table = data.sheets()[i]  #获取第一个sheet
        nrows = table.nrows #表示当前excel表格的行数
        ncols = table.ncols #表示当前excel表格的列数
        #print(nrows)
        #print(type(table.row(1)[4].value))
        for i in range(1,nrows):
            try:
                str_lat=table.row(i)[4].value
                str_lon=table.row(i)[3].value
                date = xlrd.xldate_as_tuple(table.row(i)[5].value, 0)
                if str_lat!="" and str_lon!="":
                    lat=float(str_lat.encode("utf-8"))
                    lon=float(str_lon.encode("utf-8"))
                    sheet_data.append([lat,lon,date])
            except Exception as e:
                print(e)
        table_arr.append(sheet_data)
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
            for road in roaddata['data']:
                minX,maxX,minY,maxY=min(minX,road[0]),max(maxX,road[0]),min(minY,road[1]),max(maxY,road[1])
            roaddata['minX'],roaddata['maxX'],roaddata['minY'],roaddata['maxY'] = minX,maxX,minY,maxY
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


def get_point_in_region(data_list,slat,slng,elat,elng):
    point_list_ret=[]
    for lat_lng in data_list:
        now_lat=lat_lng[0]
        now_lng=lat_lng[1]
        if now_lat >= slat and now_lat <= elat and now_lng >= elng and now_lng <=slng:
            point_list_ret.append(lat_lng)
    #print "%d points in region!" % len(point_list_ret)
    #print("%d points in region!" % len(point_list_ret))
    return point_list_ret

#检查一个点是否在道路的多边形区域内
#如果在多边形内，返回值为1
#如果在多边形外，但是离多边形的某条边很近(在误差允许范围内)，返回值为2
#如果在多边形外，而且离多边形很远，返回值为0
def check_point(dataset,lng,lat):
    flag,minDis,x0,y0,count,length,j = 0,MAXINT,MAXINT,lat,0,len(dataset),len(dataset)-1
    for i in range(0,length):
        #数据点正好和多边形路段边界点重合
        if (math.fabs(dataset[i][0]-lng) < EPS and math.fabs(dataset[i][1]-lat) < EPS):
            flag = 1
            break
        #下面计算射线与线段的交点个数，判断点是否在多边形内
        #经度相同时，相当于线段竖直
        if (math.fabs(dataset[i][0] - dataset[j][0]) < EPS):
            minY = min(dataset[i][1], dataset[j][1])
            maxY = max(dataset[i][1], dataset[j][1])
            if (minY <= lat and lat <= maxY):
                dis = math.fabs(lng - dataset[i][0])
                minDis = min(minDis, dis)
                if(dataset[i][0]>=lng):  #保证射线是向右的，所以这里求交点的时候，交点不能在数据点左侧
                    count +=1
        else:
            #线段平行
            if(math.fabs(dataset[i][1]-dataset[j][1])<EPS):
                minX = min(dataset[i][0], dataset[j][0])
                maxX = max(dataset[i][0], dataset[j][0])
                if (minX <= lng and lng <= maxX):
                    dis = math.fabs(lat - dataset[i][1])
                    minDis = min(minDis, dis)
                    continue
            else:
                kij = (dataset[j][1] - dataset[i][1]) / (dataset[j][0] - dataset[i][0])
                #yij = k(x - xi) + yi与y = lat相交求点引出的射线与多边形边的交点
                #k不会为0

                #求点到直线的距离
                # yij= kij*(x-dataset[i][0])+dataset[i][1]
                # ypj=-1/kij*(x-lng)+lat
                x0 = (kij * dataset[i][0] - dataset[i][1] + lng / kij + lat) / (kij + 1 / kij)
                y0 = -1 / kij * (x0 - lng) + lat
                xPos = (lat - dataset[i][1]) / kij + dataset[i][0]
                minX = min(dataset[i][0], dataset[j][0])
                maxX = max(dataset[i][0], dataset[j][0])
                minY = min(dataset[i][1], dataset[j][1])
                maxY = max(dataset[i][1], dataset[j][1])
                if (minX <= x0 and x0 <= maxX and minY <= y0 and y0 <= maxY):
                    # 向量a = (lng-xj, lat-yj)
                    # 向量b = (xi-xj, yi-yj)
                    cross = (lng - dataset[j][0]) * (dataset[i][1] - dataset[j][1]) - (dataset[i][0] - dataset[j][0]) * (lat - dataset[j][1])
                    dis = math.fabs(cross / math.sqrt(math.pow(dataset[i][0] - dataset[j][0], 2) + math.pow(dataset[i][1] - dataset[j][1], 2)))
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
def label_points(data_path,road_path,out_data_path,out_newjsdata_path = POINT_OUTPUT_DIR + os.sep + 'pathpoints.js'):
    datafile = open(data_path, 'rb')
    roadfile = open(road_path, 'rb')
    labeldatafile = open(out_data_path, 'wb')
    jsdatafile = open(out_newjsdata_path,'w')
    pathpoints = []
    dataset = pickle.load(datafile)  # 获取所有数据点的list
    roadset = pickle.load(roadfile)  # 获取到所有road的list
    for i in range(len(dataset)):  #遍历excel数据中的len(dataset)个sheet
        for point in dataset[i]:  # 遍历dataset中的每一个数据点
            flag,minDis,pos = 0,MAXINT,0
            #pos用来记录与这个点离的最近的道路的index
            for j in range(len(roadset)):  # 遍历roadset中的每一条道路
                if (not (roadset[j]['minX'] <= point[0] and point[0] <= roadset[j]['maxX'] and roadset[j]['minY'] <=
                    point[1] and point[1] <= roadset[j]['maxY'])):
                    continue
                [status,dis] = check_point(roadset[j]['data'],point[0],point[1])
                if(status==1):
                    flag = 1
                    pathpoints.append([point[0],point[1],point[2],roadset[j]['direction']])
                    break
                elif(status==2):
                    if(dis<minDis):
                        flag,pos,minDis = 2,j,min(minDis,dis)

            if(flag==0):
                pathpoints.append([point[0], point[1], point[2],0])
            elif(flag==2):
                pathpoints.append([point[0],point[1],point[2],roadset[pos]['direction']])
    pickle.dump(pathpoints, labeldatafile, -1)
    pathpoints_str = json.dumps(pathpoints)
    jsdata = 'var pathpoints={\"data\":'+ pathpoints_str + ',\"total\":' + str(len(pathpoints)) + ',\"rt_loc_cnt\":'+ str(len(pathpoints)) +\
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
    #data_read_and_store(excel_path,out_pickle_path)
    data_time_read_and_store(excel_path,out_pickle_path)

    #
    # excel_exception_path = STATIC_ROOT+os.sep+"exception.xlsx"
    # out_exception_pickle_path = STATIC_ROOT + os.sep + "Exception.pkl"
    # #data_read_and_store(excel_exception_path, out_exception_pickle_path)
    #
    # #将road_path整个目录下的path都存储成pkl格式
    out_road_path=STATIC_ROOT+os.sep+'path.pkl'
    road_read_and_store(ROAD_DIR,out_road_path)
    out_labeled_points_path = STATIC_ROOT + os.sep + 'labeledpoints.pkl'
    label_points(out_pickle_path, out_road_path, out_labeled_points_path)
    #
    #
    # out_exception_data_path = STATIC_ROOT + os.sep + 'exceptiondata.pkl'
    # out_exception_js_path = STATIC_ROOT + os.sep + 'exceptionpoints.js'
    # #label_points(out_exception_pickle_path, out_road_path, out_exception_data_path,out_exception_js_path)
    #roads_set,roads_directions=get_all_paths()
    #poly_line_js(roads_set,roads_directions)
