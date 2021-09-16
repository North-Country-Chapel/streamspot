import requests
import re
import time
from datetime import date

url = 'https://mystreamspot.com'
values = {'username': '<lol>',
          'password': '<no>'}
id_num = ""
dashboard = "https://mystreamspot.com/dashboard"
mydate = date.today()

#open session
session = requests.session()

def get_first_file_id():    
    global response
    global id_num

    print(id_num)
      
    id_num = str(re.search(r"=([A-Z])\w+==", response.text))
    id_num = id_num[46:59]    
    print(id_num)
    #get the id_num of the latest study  
    if not id_num:
        time.sleep(30)
        id_num = str(re.search(r"=([A-Z])\w+==", response.text))
        id_num = id_num[46:59]
        print("nested " + id_num)

    return response, id_num


def download_file():
    
    global url
    global response
    global id_num

    #switch to file download page
    url = (url + '/analytics/export-event-uniques?id' + id_num)
    response = session.get(url, allow_redirects=True)


    #get filename from header
    dictionary = response.headers
    data = str(dictionary.get("Content-Disposition"))
    data = data[22:-2]

    #download with header filename 
    with open(data, 'wb') as file:
        file.write(response.content)
        file.close()


# log in
response = session.post(url + '/login', data=values, allow_redirects=True)

#test for actual login
if str(response.url) != dashboard:
    time.sleep(30)
    response = session.post(url + '/login', data=values, allow_redirects=True)
    
else:
    #go to analytics page
    response = session.get(url + '/analytics')


get_first_file_id()
download_file()

if mydate.strftime('%w') == '1': 

    id_num = re.finditer(r"=([A-Z])\w+==", response.text)
    array = []
    for match in id_num:
        array.append(match.group())
    id_num = array[1]  
    print(id_num) 

    #get the id_num_num of the latest study  
    if not id_num:
        time.sleep(30)
        id_num = re.finditer(r"=([A-Z])\w+==", response.text)
        for match in id_num:
            array.append(match.group())
        id_num = array[1]

    download_file()
