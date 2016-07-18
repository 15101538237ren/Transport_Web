# coding: utf-8
import os,xlrd,json,pickle,math,sys,datetime
from django.http import HttpResponse, JsonResponse
from Transport_Web.settings import BASE_DIR,STATIC_ROOT
MAXINT = 999999999

def success_response(response=None):
	return JsonResponse({"code": 0, "message": response})
def data_read_and_store(excel_path,pickle_path):
	out_pickle = open(out_pickle_path, 'wb')
	data = xlrd.open_workbook(excel_path)
	table_arr=[]
	for i in range(4):
		sheet_data=[]
		table = data.sheets()[i]  #获取第一个sheet
		nrows = table.nrows #表示当前excel表格的行数
		ncols = table.ncols #表示当前excel表格的列数
		#print(nrows)
		#print(type(table.row(1)[4].value))
		for i in range(1,nrows):
			str_lat=table.row(i)[4].value
			str_lon=table.row(i)[3].value

			if str_lat!="" and str_lon!="":
				lat=float(str_lat.encode("utf-8"))
				lon=float(str_lon.encode("utf-8"))
				sheet_data.append([lat,lon])
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
            try:
                roaddata = json.loads(text)  #获取到道路的数据集
            except ValueError as e:
                print(e)
            roadset.append(roaddata)
    pickle.dump(roadset, out_pickle, 3)
    out_pickle.close()


def load_pickle_from(pickle_path=STATIC_ROOT+os.sep+'WFJBXX_ORG.pkl'):
    f = open(pickle_path, 'rb')
    #print "now loading data.pkl"
    # #print("now loading data.pkl")
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
def check_point(dataset,lng,lat):
    flag = False
    minDis =  MAXINT
    x0 = MAXINT
    y0 = lat
    count = 0
    length = len(dataset)
    j = length -1
    for i in range(0,length):
        #数据点正好和多边形路段边界点重合
        if (math.fabs(dataset[i][0]-lng) < 0.00001 and math.fabs(dataset[i][1]-lat) < 0.00001):
            flag = True
            break
        #数据点正好在多边形路段的边上，要求有一定容错能力
        #计算点到线段的距离
        #线段水平
        if (abs(dataset[i][1] - dataset[j][1]) < 0.00001):
            minX = min(dataset[i][0], dataset[j][0])
            maxX = max(dataset[i][0], dataset[j][0])
            if (minX <= lng and lng <= maxX):
                dis = lat-dataset[i][1]
                minDis= min(minDis, dis)
                #如果距离线段很近，则说明在线段上
                if (dis < 0.00001):
                    flag = True
                    break
             #因为要计算点引出的射线与线段的交点，所以线段水平时可以跳过
            j=i
            continue
        else:
            #线段非水平
            minY = min(dataset[i][1], dataset[j][1])
            maxY = max(dataset[i][1], dataset[j][1])
            if (minY <= lng and lng <= maxY):
                #向量a = (lng-xj, lat-yj)
                #向量b = (xi-xj, yi-yj)
                cross = (lng-dataset[j][0]) * (dataset[i][1]-dataset[j][1])-(dataset[i][0]-dataset[j][0]) * (lat-dataset[j][1])
                dis = math.fabs(cross / math.sqrt(math.pow(dataset[i][0]-dataset[j][0], 2)+math.pow(dataset[i][1]-dataset[j][1], 2)))
                minDis = min(minDis, dis);
                #如果距离线段很近，则说明在线段上
                if (dis < 0.00001):
                    flag = True
                    break

        #下面计算射线与线段的交点个数
        #经度相同时，相当于线段竖直
        if (math.fabs(dataset[i][0] - dataset[j][0]) < 0.00001):
            minY = min(dataset[i][1], dataset[j][1])
            maxY = max(dataset[i][1], dataset[j][1])
            if (minY <= lat and lat <= maxY):
                count +=1
        else:
            k = (dataset[j][1] - dataset[i][1]) / (dataset[j][0] - dataset[i][0])
            #y = k(x - xi) + yi与y = lat相交
            #k不会为0
            xPos = (lat - dataset[i][1]) / k + dataset[i][0]
            minX = min(dataset[i][0], dataset[j][0])
            maxX = max(dataset[i][0], dataset[j][0])
            minY = min(dataset[i][1], dataset[j][1])
            maxY = max(dataset[i][1], dataset[j][1])
            if (max(minX, lng) <= xPos and xPos <= maxX and minY <= lat and lat <= maxY):
                count +=1
        j = i

    if (count % 2 == 1):
        flag = True
    return flag



#标注所有点，将标注了方向的数据点保存在新的文件中
def label_points(data_path,road_path,out_data_path,out_newjsdata_path = STATIC_ROOT + os.sep + 'pathpoints.js'):
    datafile = open(data_path, 'rb')
    roadfile = open(road_path, 'rb')
    labeldatafile = open(out_data_path, 'wb')
    jsdatafile = open(out_newjsdata_path,'w')
    pathpoints = []
    dataset = pickle.load(datafile)  # 获取所有数据点的list
    roadset = pickle.load(roadfile)  # 获取到所有road的list
    for i in range(4):  #遍历excel数据中的4个sheet
        for point in dataset[i]:  # 遍历dataset中的每一个数据点
            flag = False
            for road in roadset:  # 遍历roadset中的每一条道路
                if (check_point(road['data'],point[0],point[1])):
                    flag = True
                    pathpoints.append([point[0],point[1],road['direction']])
                    break
            if(flag==False):
                pathpoints.append([point[0], point[1], 0])
    pickle.dump(pathpoints, labeldatafile, -1)
    try:
        pathpoints_str = json.dumps(pathpoints)
    except Exception as e:
        print(e)
    jsdata = 'var pathpoints={\"data\":'+ pathpoints_str + ',\"total\":' + str(len(pathpoints)) + ',\"rt_loc_cnt\":'+ str(len(pathpoints)) +\
     ',\"errorno\": 0,\"NearestTime\": \"2014-08-29 15:20:00\",\"userTime\": \"2014-08-29 15:32:11\"'
    jsdatafile.write(jsdata)
    datafile.close()
    roadfile.close()
    labeldatafile.close()
    jsdatafile.close()

def convert_point_list_to_path_file(point_lists,direction):
    split='\n\t'
    now_str=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    json_str='{'+split+'"data": ['+split

    points_str_list=[]
    for point in point_lists:
        points_str='['+str(point["lng"])+', '+str(point["lat"])+']'
        points_str_list.append(points_str)
    json_str=json_str+(","+split).join(points_str_list)+split
    json_str=json_str+'],'+split+'"total": '+str(len(point_lists))+','+split+'"rt_loc_cnt": '+str(len(point_lists))+','+split+'"errorno": 0,'+split+'"direction":'+str(direction)+','+split+'"NearestTime": "'+now_str+'",'+split+'"userTime": "'+now_str+'"'+'\n}'
    return json_str

if __name__ == '__main__':
    excel_path=STATIC_ROOT+os.sep+"WFJBXX_ORG.xls"
    road_dir=BASE_DIR+ os.sep+'data'+ os.sep + 'input' + os.sep +'road'
    out_pickle_path=STATIC_ROOT+os.sep+"WFJBXX_ORG.pkl"
    data_read_and_store(excel_path,out_pickle_path)
    #将road_path整个目录下的path都存储成pkl格式
    out_road_path=STATIC_ROOT+os.sep+'path.pkl'
    road_read_and_store(road_dir,out_road_path)
    out_newdata_path = STATIC_ROOT + os.sep + 'newdata.pkl'
    label_points(out_pickle_path, out_road_path, out_newdata_path)