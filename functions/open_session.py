"""
Open a session for the streamspot scripts. 
Outlook Desktop application MUST be open for the email verification to work. 

"""

import requests
import time
import os
from getEmailLink import verifyEmail
import logging


url = "https://mystreamspot.com"
values = {
    "username": os.environ.get("STREAMSPOT_USERNAME"),
    "password": os.environ.get("STREAMSPOT_PASSWORD"),
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="streamspot.log",
)


def open_session():
    global session
    global response
    global url

    # open session
    session = requests.session()

    # log in
    response = session.post(url + "/login", data=values, allow_redirects=True)
    logging.info(response.url)
    time.sleep(10)
    logging.info("Checking for email verification")
    verifylink = verifyEmail()
    response = session.get(verifylink, allow_redirects=True)
    logging.info(response.url)
    logging.info(response.headers)
    print(response.status_code)
    print(response.cookies)

    # go to analytics page
    response = session.get(url + "/analytics/")

    logging.info("Response code: " + str(response.status_code))

    logging.info("Leaving open_session()")
    return response, session


# open_session()
