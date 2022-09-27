import requests
from bs4 import BeautifulSoup
from lxml import etree
#import re
import time
#import os
#from sendgrid import SendGridAPIClient
#from sendgrid.helpers.mail import Mail, to_email
#from datetime import date

url = 'https://mystreamspot.com'
values = {'username': 'USERNAME',
          'password': 'PASSWORD'}
id_num = ""

def open_session():
    global response
    global url
    global session
    dashboard = "https://mystreamspot.com/dashboard"
    #open session
    session = requests.session()
    time.sleep(10)

    # log in
    response = session.post(url + '/login', data=values, allow_redirects=True)
    time.sleep(20)

    

    #test for actual login
    if str(response.url) != dashboard:
        time.sleep(10)
        open_session()
        time.sleep(30)
    else:
        #go to archive page
        response = session.get(url + '/archive')

      
    return response


def get_first_file_id():    
    global response
    global id_num
    
    # Get the class name of first row
    soup = BeautifulSoup(response.content, "html.parser")
    dom = etree.HTML(str(soup))
    id_num =  dom.xpath('/html/body/div/div/div/div[4]/div[1]/div[2]/div[2]/table/tbody/tr[1]')

    
    # Get the id_num of the latest study  
    if not id_num:
        time.sleep(30)
        get_first_file_id()
    
    
 
    return response, id_num

open_session()
get_first_file_id()

print(id_num)