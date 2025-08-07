#!/usr/bin/python3

import requests
import time
import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from functions.getEmailLink import verifyEmailGraph
from functions.logging_config import setup_logging

setup_logging(
    config_path='functions/logging_config.json',
    log_file_path='streamspot.log'
)

logger= logging.getLogger(__name__)

url = "https://mystreamspot.com"
values = {
    "username": os.environ.get("STREAMSPOT_USERNAME"),
    "password": os.environ.get("STREAMSPOT_PASSWORD"),
}


class LoginError(Exception):
    """Raised when the login fails"""

    e = "Login failed"


class DeleteError(Exception):
    """Raised when the delete fails"""

    e = "Delete Failed"


def open_session():
    global session
    global response
    global url
    dashboard = "https://mystreamspot.com/dashboard"
    # open session
    session = requests.session()
    logger.info("Opening session")

    # log in
    response = session.post(url + "/login", data=values, allow_redirects=True)
    logger.info(response.url)
    time.sleep(10)
    logger.info("Checking for email verification")
    verifylink = verifyEmailGraph()
    response = session.get(verifylink, allow_redirects=True)
    logger.info(response.url)
    logger.debug(response.headers)

    # go to expired-archive page
    response = session.get(url + "/archive/expired-archives")
    logger.info(response.url)
    logger.debug(response.headers)

    return response


open_session()

time.sleep(10)


try:
    payload = {"confirm": "delete"}

    response = session.post(
        "https://mystreamspot.com/archive/del-all-exp-archives",
        data=payload,
        allow_redirects=True,
    )

    if response.status_code != 200:
        raise DeleteError
    else:
        logger.info("Delete successful")

except Exception as e:
    message = Mail(
        from_email="kristin@northcountrychapel.com",
        to_emails="kristin@northcountrychapel.com",
        subject="Streamspot delete archive script did not complete ",
        html_content=f"This email indicates that the delete archive script did not run as expected. <p>Error details: {str(e)}.</p>",
    )

    sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
    response = sg.send(message)
