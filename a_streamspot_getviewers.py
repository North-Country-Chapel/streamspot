import requests
import re
import time
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, to_email
from datetime import date

url = 'https://mystreamspot.com'
values = {'username': 'USERNAME',
          'password': 'PASSWORD'}
id_num = ""
mydate = date.today()

def open_session():
    global session
    global response
    global session
    global url
    dashboard = "https://mystreamspot.com/dashboard"
    #open session
    session = requests.session()

    # log in
    response = session.post(url + '/login', data=values, allow_redirects=True)
    

    #test for actual login
    if str(response.url) != dashboard:
        time.sleep(10)
        response = session.post(url + '/login', data=values, allow_redirects=True)
        time.sleep(30)
    else:
        #go to analytics page
        response = session.get(url + '/analytics')
        
    return response


def get_first_file_id():    
    global response
    global id_num

   
    id_num = str(re.search(r"=([A-Z])\w+==", response.text))
    id_num = id_num[46:59]    
    
    #get the id_num of the latest study  
    if not id_num:
        time.sleep(30)
        id_num = str(re.search(r"=([A-Z])\w+==", response.text))
        id_num = id_num[46:59]
 
    return response, id_num


def download_file():
    global url
    global response
    global id_num

    #switch to file download page
    link = (url + '/analytics/export-event-uniques?id' + id_num)
    response = session.get(link, allow_redirects=True)


    #get filename from header
    dictionary = response.headers
    data = str(dictionary.get("Content-Disposition"))
    data = data[22:-2]

    #download with header filename 
    with open(data, 'wb') as file:
        file.write(response.content)
        file.close()

    return response




#get the second newest study for Sunday 1st service
if mydate.strftime('%w') == '1': 
    open_session()
    #get the id_num_num of the latest study 
    id_num = re.finditer(r"=([A-Z])\w+==", response.text)
    array = []
    for match in id_num:
        array.append(match.group())
    id_num = array[1]  

     
    if not id_num:
        time.sleep(30)
        id_num = re.finditer(r"=([A-Z])\w+==", response.text)
        for match in id_num:
            array.append(match.group())
        id_num = array[1]  

    download_file()



open_session()
get_first_file_id()
download_file()

message = Mail(
    from_email='from@email.com',
    to_emails='to@email.com',
    subject='Streamspot script ran successfully',
    html_content='This email indicates that the script ran without errors. <p>There is no guarantee that it ran correctly.</p>'
)

sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
response = sg.send(message)  #https://docs.sendgrid.com/for-developers/sending-email/v3-python-code-example


#TODO: try/catch