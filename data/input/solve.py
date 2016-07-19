import re
try:
    data = open("path7.json","r+")
    text = data.read()
    result, number = re.subn("\(index\)\:\d+ ","", text)
    print(result)
    data.close()
    data = open("path7.json","w+")
   # data.truncate()
    #data.seek(0,0)
    data.write(result)
    #data.write("123")
    data.close()
except Exception as e:
    print(e)