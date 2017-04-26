# coding utf-8
import os,csv,json

pinyin_hash = {"dongcheng" : 1, "xicheng" : 2, "chaoyang":5, "haidian":6,"fengtai":7,"daxing":8,"shijingshan":9}
if __name__ == '__main__':
    out_file_path = "/Users/Ren/PycharmProjects/Police_Index_Framework/data/data.js"
    boundary_dir = "/Users/Ren/PycharmProjects/Police_Index_Framework/data/boundary"
    out_file = open(out_file_path,"w")
    pre = "var data={"
    lt = []
    geo_center = "var geocenter = "
    geo_lt = {}
    for k,v in pinyin_hash.iteritems():
        file_path = boundary_dir + os.sep + k +".txt"
        file = open(file_path,"r")
        line = file.readline()
        points = []
        while line:
             cord_arr = line.split(";")
             for item in cord_arr:
                 lon,lat = item.split(",")
                 lon = float(lon)
                 lat = float(lat)
                 points.append([lon,lat])
             line= file.readline()
        json_str = json.dumps(points)
        lt.append("\""+ str(v) +"\":" + json_str)
        sum_lon = 0.0
        sum_lat = 0.0
        for it in range(len(points)-1):
            sum_lon += points[it][0]
            sum_lat += points[it][1]
        mean_lon = sum_lon/(len(points)-1)
        mean_lat = sum_lat/(len(points)-1)
        geo_lt[v]=[mean_lon,mean_lat]
    ltw = ",".join(lt)
    post = "};\n"
    tot = pre + ltw + post
    out_file.write(tot)

    geo_lt_str = json.dumps(geo_lt)
    out_file.write(geo_center+geo_lt_str)
    out_file.close()