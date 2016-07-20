from django.test import TestCase

# Create your tests here.

import xlrd,datetime

date = "2016-7-16 16:21:02"
date_time = datetime.datetime.strptime(date,'%Y-%m-%d %H:%M:%S')
print(xlrd.xldate.xldate_as_datetime(date_time,0))
