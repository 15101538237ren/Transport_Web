# -*- coding:utf-8 -*-
import math,random,re,os
import datetime,json
from Transport_Web.settings import BASE_DIR
from os.path import normpath,join

x_list = []  #表示出现违章的序列
y_list = []  #表示拥堵指数 y[i]在0~1之间，0表示不拥堵，1表示非常拥堵。将y0置为0.2
t_list = []  #表示时间序列,/s
g_list = []  #表示周期性的拥堵情况
Fx_list = []
dy_dt_list = []

def load_param_from_file(param_file_path):
    param_file=open(param_file_path,"r")

    line = param_file.readline()
    param_hash={}
    while line:
        line_arr=re.split("=|\n",line)
        param_hash[line_arr[0]]=line_arr[1]
        line = param_file.readline()
    param_file.close()
    return param_hash


def calc_evacuation_rate(police_number):
    evacuation_rate_a = 0.06
    evacuation_rate_b = 0.032
    return evacuation_rate_a - evacuation_rate_a / math.exp(evacuation_rate_b * police_number)

def calc_rate_accord(y,police_number):
    rate_accord_a = 0.2
    rate_accord_b = 0.3
    rate_accord_c = 2.11
    rate_accord_d = 0.69
    police_evacuation_val = rate_accord_a - rate_accord_a / math.exp(rate_accord_b * police_number)
    congestion_index_val = rate_accord_c - rate_accord_c / math.exp(rate_accord_d * y)
    rate_accord = congestion_index_val - police_evacuation_val
    return rate_accord

def calc_Fx(x):
    Fx_a = 0.0023
    Fx_b = 0.12
    Fx = Fx_a - Fx_a / math.exp(Fx_b * x)
    return Fx

def x_integration(index,x_stat_start,x_stat_end):
    sum = 0
    idx_start = max(0, index-x_stat_start)
    idx_end = max(0,index-x_stat_end)+1
    for i in range(idx_start, idx_end):
        sum += x_list[i]
    return sum



def calc_dy_dt(police_number,index,x_stat_start,x_stat_end):
    sum_x = x_integration(index,x_stat_start,x_stat_end)
    y_last = y_list[max(0,index-1)]
    g_last = g_list[max(0,index-1)]
    Fx_value = calc_Fx(sum_x)
    Fx_list.insert(index,Fx_value)
    dg_value = g_list[index] - g_last
    if(dg_value>0.01):
        dg_value = 0.0015
    print('index=%d'% index)
    if(index >= 6*60 and index <= 19*60):
        evacuation_rate = calc_evacuation_rate(police_number)
        evacuation_value = evacuation_rate * y_last
        return Fx_value + dg_value - evacuation_value
    return Fx_value + dg_value

def calc_y(y_list,x_list,police_num,index,x_stat_start,x_stat_end):
    dy_dt = calc_dy_dt(police_num,index,x_stat_start,x_stat_end)
    dy_dt_list.insert(index,dy_dt)
    y_last = y_list[max(0,index-1)]
    y_val = abs(y_last + dy_dt)
    return y_val

def calc_Func(A, index, mu,sigma):

    num = -math.pow(index-mu, 2)/sigma
    Fx = A*math.exp(num)
    return Fx

def init():

    sigma1 = 0.0001
    sigma2 = 0.0002

    mid = (6*60 + 10*60) / 2
    mid = mid + random.randrange(-60, 90)
    print(mid)
    st = int(mid - 120)
    ed = int(mid + 120)
    print('st='+str(st))
    print('ed='+str(ed))
    g_list.insert(0, random.gauss(0, sigma2))
    for i in range(1,3*60):
        num = g_list[i - 1] + random.gauss(-0.00025, 0.0002)
        g_list.insert(i, num)
    for i in range(3*60, st):
        num = g_list[i-1] + random.gauss(0.0001, 0.0002)
        g_list.insert(i, num)

    for i in range(st,ed):
        num = calc_Func(0.35,i,mid,4000) + random.gauss(0,sigma1)
        #num = calc_Func(i,mid)
        g_list.insert(i,num)

    mid = (16*60 + 20*60) / 2
    mid = mid + random.randrange(-60, 90)

    print(mid)

    '''for i in range(ed,ed+30):
        num = g_list[i-1] - 0.015 + random.gauss(0, sigma2)
        g_list.insert(i, num)

    ed += 30'''
    for i in range(ed, int(mid-120)):
        num = g_list[i-1] + random.gauss(0, sigma2)
        g_list.insert(i, num)

    st = int(mid - 120)
    ed = int(mid + 120)

    for i in range(st, ed):
        num = calc_Func(0.35, i, mid, 4000) + random.gauss(0, sigma1)
        #num = calc_Func(i, mid)
        g_list.insert(i, num)

    '''for i in range(ed, ed + 30):
        num = g_list[i-1] -0.008 + random.gauss(0, sigma1)
        g_list.insert(i, num)

    ed += 30'''

    st = ed
    ed = 24 * 60
    for i in range(st, ed):
        num = g_list[i-1] + random.gauss(-0.0003, sigma2)
        g_list.insert(i, num)
    print(len(g_list))
    f = open('g_list.txt', 'w')
    for i in range(len(g_list)):
        f.write(str(g_list[i]) + '\n')
    f.close()

def simulation(out_put_file_name,**param_hash):
    time_unit=str(param_hash.get('time_unit')).replace('\"','')
    initial_x=int(param_hash.get('initial_x'))
    initial_y=float(param_hash.get('initial_y'))
    initial_time = float(param_hash.get('initial_time'))
    initial_police_num = int(param_hash.get('initial_police_num'))

    max_iteration_time=int(param_hash.get('max_iteration_time'))
    max_cars_on_the_road=int(param_hash.get('max_cars_on_the_road'))
    rand_times = int(param_hash.get('rand_times'))
    delta_t = int(param_hash.get('delta_t'))
    x_stat_start = int(param_hash.get('x_stat_start'))
    x_stat_end = int(param_hash.get('x_stat_end'))

    x_list.insert(0,initial_x)
    y_list.insert(0,initial_y)
    t_list.insert(0,initial_time)
    Fx_list.insert(0,0)
    dy_dt_list.insert(0,0)
    init()

    curr_time = initial_time
    now_police_num = initial_police_num

    for t in range(1,max_iteration_time+1):

        curr_time += delta_t
        y_now=calc_y(y_list,x_list,now_police_num,t,x_stat_start,x_stat_end)
        if(t>300 and y_now > 0.21):
            #now_police_num = 10
            print(y_list[t-1])
            print(str(x_list[t-1])+' '+str(x_list[t-2]) + ' ' + str(x_list[t-3]) + ' ' + str(x_list[t-4]))
            #print('t='+ str(t))
        if(t>300 and y_now < 0.2):
            print(y_list[t - 1])
            print(str(x_list[t - 1]) + ' ' + str(x_list[t - 2]) + ' ' + str(x_list[t - 3]) + ' ' + str(x_list[t - 4]))
            #print('t=' + str(t))
        y_list.insert(t, y_now)
        t_list.insert(t,curr_time)
        if t<6*60 or t>19*60:
            attempt_times=math.ceil(max_cars_on_the_road*(y_now*0.1))
        else:
            attempt_times = math.ceil(max_cars_on_the_road * (y_now))
        record_num = 0
        rate_of_break_rule = calc_rate_accord(y_now, now_police_num)
        for i in range(rand_times):
            record_num_tmp = 0
            for atm in range(1,attempt_times):

                #每次举报尝试
                random.seed(datetime.datetime.now())
                rand_num = random.random()
                if rand_num < rate_of_break_rule:
                    #当前时间点的举报量+1,并进行记录
                    record_num_tmp += 1
            record_num += record_num_tmp
        record_num = int(record_num*0.15/rand_times)
        x_list.insert(t, record_num)
    print('YES')


def get_date_list():
    date = datetime.datetime(2016, 6, 1, 0, 0, 0)
    date_list = []
    for i in range(1440):
        datetmp = date + datetime.timedelta(minutes=i)
        str = datetmp.strftime("%Y-%m-%d %H:%M")
        pos = str.find(' ')
        #print(str[pos + 1:])
        date_list.append(str[pos + 1:])
    return date_list

if __name__ == '__main__':
    param_file_path="in_param.txt"
    param_hash=load_param_from_file(param_file_path)
    out_put_file_path="out.pkl"
    date_list = get_date_list()
    simulation(out_put_file_path,**param_hash)
    f = open('x_list.txt','w')
    for i in range(len(x_list)):
        f.write(str(x_list[i])+'\n')
    f.close()
    f = open('y_list.txt', 'w')
    for i in range(len(y_list)):
        f.write(str(y_list[i])+'\n')
    f.close()
    f = open('date_list.txt','w')
    for i in range(len(date_list)):
        f.write(str(date_list[i]) + '\n')
    f.close()
    f = open('Fx_list.txt', 'w')
    for i in range(len(Fx_list)):
        f.write(str(Fx_list[i]) + '\n')
    f.close()
    f = open('dy_dt_list.txt', 'w')
    for i in range(len(dy_dt_list)):
        f.write(str(dy_dt_list[i]) + '\n')
    f.close()
    data_dict = {}
    data_dict['datatime'] = date_list
    data_dict['type0'] = x_list
    data_dict['type1'] = y_list
    data_dict['type2'] = g_list
    jsonret = json.dumps(data_dict, sort_keys=True, indent=4)
    data_path = normpath(join(BASE_DIR,'static','option')) + os.sep + "data.json"
    f = open(data_path, 'w')
    f.write(jsonret)
    f.close()
    print('YES')

