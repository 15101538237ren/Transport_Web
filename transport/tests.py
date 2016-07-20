from django.test import TestCase

# Create your tests here.


def lower_bound_search(table,l,r,num):
    while(l<r):
        mid = l+(r-l)/2
        if(table[mid]>= num):
            r=mid
        else:
            l=mid+1
    return l

def lower_bound_search1(table,l,r,num):
    while(l<r):
        mid = l+(r-l)/2
        if(table[mid]> num):
            r=mid
        else:
            l=mid+1
    return l


#返回比num大的数字中最小数字的下标
def upper_bound_search(table,l,r,num):
    while(l<r):
        mid=l+(r-l)/2
        print('l=' + str(l) + ' r=' + str(r) + ' mid=' + str(mid))
        if(table[mid]<=num):
            l=mid+1
        else:
            r=mid
    print('---------')
    return l


def upper_bound_search1(table,l,r,num):
    while(l<r):
        mid=l+(r-l)/2
        print('l=' + str(l) + ' r=' + str(r) + ' mid=' + str(mid))
        if(table[mid]<num):
            l=mid+1
        else:
            r=mid
    return l


table = [1,2,3,3,3,3,3,4,5,6,6,6,6,7,8]

num = 3

print(lower_bound_search(table,0,len(table),num))
print(lower_bound_search1(table,0,len(table),num))
print(upper_bound_search(table,0,len(table),num))
print(upper_bound_search1(table,0,len(table),num))

