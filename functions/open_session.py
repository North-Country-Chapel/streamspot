"""
Open a session for the streamspot scripts. 
Outlook Desktop application MUST be open for the email verification to work. 

"""

import requests
import time
import os
from functions.getEmailLink import verifyEmail
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

    return session
