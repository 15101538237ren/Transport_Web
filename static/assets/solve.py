import re
try:
    data = open("pathpoints2.js","r+")
    text = data.read()
    result, number = re.subn("\(index\)\:\d+ ","", text)
    print(result)
    data.close()
    data = open("pathpoints2.js","w+")
   # data.truncate()
    #data.seek(0,0)
    data.write(result)
    #data.write("123")
    data.close()
except Exception as e:
    print(e)