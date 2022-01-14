import requests
import time
import datetime
from datetime import date
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, to_email

url = 'https://mystreamspot.com'
values = {'username': '<username>',
          'password': '<password>'}
dashboard = url + "/dashboard"
mydate = date.today()
study_start_minute = "55"
study_end_minute = "35"
session = ""

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
        response = session.post(url + '/login', data=values, allow_redirects=True)
        time.sleep(30)
    else:
        #go to analytics page
        response = session.get(url + '/scheduler/add-single-broadcast')

      
    return response


      
def get_posting_date(posting_day):

    fri = mydate + datetime.timedelta( (4-mydate.weekday()) % 7) + datetime.timedelta(days=7)
    mon = mydate + datetime.timedelta( (0-mydate.weekday()) % 7) + datetime.timedelta(days=7)
    sun = mydate + datetime.timedelta( (6-mydate.weekday()) % 7) + datetime.timedelta(days=7)
    
    if posting_day == 'Friday':
        facts = {
            "study_start_hour" : "18",
            "study_end_hour" :"20",
            "study_title" : "Friday Night bible study",
            "study_date" : str(fri),}

    elif posting_day == 'Monday':
        facts = {
            "study_start_hour" : "18",
            "study_end_hour" : "20",
            "study_title" : "Monday Night bible study",
            "study_date" : str(mon),}
    elif posting_day == 'Sunday1':
        facts = {
             "study_start_hour" : "8",
             "study_end_hour" : "10",
             "study_title" : "Sunday Morning first service",
             "study_date" : str(sun),}
    elif posting_day == 'Sunday2':
        facts = {
             "study_start_hour" : "10",
             "study_end_hour" : "12",
             "study_title" : "Sunday Morning second service" ,
             "study_date" : str(sun),}

        
    return facts   

   
open_session() 

for studay in ['Friday', 'Monday', "Sunday1", "Sunday2"]:
    facts = get_posting_date(studay)
    payload = {"formattedStartDate": str(facts['study_date']), "formattedStartHour": str(facts['study_start_hour']), "formattedStartMinute":str(study_start_minute), "formattedEndDate":str(facts['study_date']),"formattedEndHour":str(facts['study_end_hour']), "formattedEndMinute":str(study_end_minute), "title":str(facts['study_title']), "catSelector":"none", "expiration":"30", "access":"0", "passcode":"", "excludeFromSchedule": "0", "facebookLive": "1", "facebookAccountId": "145193313314", "facebookPrivacy": "EVERYONE", "facebookTargeting": "everyone", "scheduledFacebook": "0", "Submit": "Add+Broadcast"}
    
    
    response = session.post("https://mystreamspot.com/scheduler/processSingleBroadcast", data=payload, allow_redirects=True)

    time.sleep(10)

    


if response.url == "https://mystreamspot.com/scheduler/?msg=1": 
    message = Mail(
    from_email='from@example.com',
    to_emails='to@example.com',
    subject='Streamspot script ran successfully',
    html_content='This email indicates that the scheduling script ran without errors. <p>There is no guarantee that it ran correctly.</p>'
    )

else:
    message = Mail(
    from_email='from@example.com',
    to_emails='to@example.com',
    subject='Streamspot script needs checking',
    html_content='This email indicates that the scheduling script did not run as expected. <p>Check to make sure future studies were scheduled on the site.</p>'
    )

sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
response = sg.send(message)


#TODO: try/catch