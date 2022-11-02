import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from lxml import etree
#import re
import time
#import os
#from sendgrid import SendGridAPIClient
#from sendgrid.helpers.mail import Mail, to_email
#from datetime import date

load_dotenv()
url = 'https://mystreamspot.com'
values = {'username': os.getenv('SP_USER'),
          'password': os.getenv('SP_PASSWORD')}
id_num = ""



def open_session():
    global response
    global url
    global session
    dashboard = "https://mystreamspot.com/dashboard"

    #open session
    session = requests.session()
        

    # log in
    response = session.post(url + '/login', data=values, allow_redirects=True)
    
    

    #test for actual login
    if str(response.url) != dashboard:
        time.sleep(10)
        open_session()
        
    else:
        #go to archive page
        response = session.get(url + '/archive')

    print(response.url) 
    return response


def get_first_file_id():    
    global response
    global id_num
    
    # Get the class name of first row
    soup = BeautifulSoup(response.content, "html.parser")
    print(soup)
    # id_num = soup.select_one('tr.video:nth-child(1)')
    # print(id_num)
    # id_num = (id_num[0].attrib['class']) 
    
    
    # Get the id_num of the latest study  
    # if not id_num:
    #     time.sleep(30)
    #     get_first_file_id()
    
    
 
    return id_num

open_session()
get_first_file_id()


