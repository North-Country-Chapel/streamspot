import requests
import time
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


url = 'https://mystreamspot.com'
values = {'username': os.environ.get('STREAMSPOT_USERNAME'),
          'password': os.environ.get('STREAMSPOT_PASSWORD')}


class LoginError(Exception):
    """Raised when the login fails"""
    e = "Login failed"

class DeleteError(Exception):
    """Raised when the delete fails"""
    e = "Delete Failed"
    

def open_session():
    global session
    global url

    #open session
    session = requests.session()
    
 
    # log in
    try:
        time.sleep(30)
        response = session.post(url + '/login', data=values, allow_redirects=True)
        time.sleep(50)
        if response.url != "https://mystreamspot.com/dashboard":
            raise LoginError
        

    except:
        message = Mail(
            from_email='kristin@northcountrychapel.com',
            to_emails='kristin@northcountrychapel.com',
            subject='Streamspot delete archive script could not log in ',
            html_content='This email indicates that the delete archive script could not log in. <p>Check to make sure expired studies were deleted on the site.</p>'
        )

        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)


    response = session.get(url + '/archive/expired-archives')

    return response

open_session() 

time.sleep(10)


try:
    payload = {"confirm": "delete"}
    
    response = session.post("https://mystreamspot.com/archive/del-all-exp-archives", data=payload, allow_redirects=True)
    
    if response.status_code != "200":
        raise DeleteError

except:
        message = Mail(
            from_email='kristin@northcountrychapel.com',
            to_emails='kristin@northcountrychapel.com.com',
            subject='Streamspot delete archive script did not complete ',
            html_content='This email indicates that the delete archive script did not run as expected. <p>Check to make sure expired studies were deleted on the site.</p>'
        )

        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)