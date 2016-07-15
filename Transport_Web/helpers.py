# coding: utf-8
import os,xlrd,pickle
from django.http import HttpResponse, JsonResponse
from Transport_Web.settings import BASE_DIR,STATIC_ROOT
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
		print(nrows)
		print(type(table.row(1)[4].value))
		for i in range(1,nrows):
			str_lat=table.row(i)[4].value.encode("utf-8")
			str_lon=table.row(i)[3].value.encode("utf-8")

			if str_lat!="" and str_lon!="":
				lat=float(str_lat)
				lon=float(str_lon)
				sheet_data.append([lat,lon])
		table_arr.append(sheet_data)
	pickle.dump(table_arr,out_pickle,-1)
	out_pickle.close()
def load_pickle_from(pickle_path=STATIC_ROOT+os.sep+'WFJBXX_ORG.pkl'):
	f = open(pickle_path, 'rb')
	print "now loading data.pkl"
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
	print "%d points in region!" % len(point_list_ret)
	return point_list_ret
if __name__ == '__main__':
	excel_path=STATIC_ROOT+os.sep+"WFJBXX_ORG.xls"
	out_pickle_path=STATIC_ROOT+os.sep+"WFJBXX_ORG.pkl"
	data_read_and_store(excel_path,out_pickle_path)