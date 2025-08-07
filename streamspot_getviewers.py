#! /usr/bin/python3

"""
Get viewer numbers at the same time every week for comparison across weeks. 
Outlook Desktop application MUST be open for the verifyEmail to work.
verifyEmailGraph does not require Outlook to be open. 

"""

import requests
import re
import time
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import date
import logging
from random import *
from functions.getEmailLink import verifyEmailGraph
from functions.logging_config import setup_logging


setup_logging(
    config_path='functions/logging_config.json',
    log_file_path='streamspot.log'
)

logger=logging.getLogger(__name__)

url = "https://mystreamspot.com"
values = {
    "username": os.environ.get("STREAMSPOT_USERNAME"),
    "password": os.environ.get("STREAMSPOT_PASSWORD"),
}
id_num = ""
mydate = date.today()


def open_session():
    global session
    global response
    global url

    # open session
    session = requests.session()
    logger.info("Opening session")

    # log in
    response = session.post(url + "/login", data=values, allow_redirects=True)
    logger.debug("Login response: " + response.url)
    logger.info("Checking for email verification")
    verifylink = verifyEmailGraph()
    response = session.get(verifylink, allow_redirects=True)
    logger.info(response.request.headers)
    logger.info(response.url)

    # go to analytics page
    time.sleep(15)
    response = session.get(url + "/analytics/", timeout=20)
    logger.info(response.url)

    return response


def get_first_file_id():
    global response
    global session
    global id_num

    logger.debug("Entering get_first_file_id()")
    id_num = str(re.search(r"=([A-Z])\w+==", response.text))
    id_num = id_num[46:59]
    logger.info(id_num)

    # get the id_num of the latest study
    if not id_num:
        time.sleep(30)
        id_num = str(re.search(r"=([A-Z])\w+==", response.text))
        id_num = id_num[46:59]

    logger.debug("Leaving get_first_file_id()")
    return response, id_num


def download_file():
    global url
    global response
    global session
    global id_num

    logger.debug("Entering download_file()")
    # switch to file download page
    link = url + "/analytics/export-event-uniques?id" + id_num
    response = session.get(link, allow_redirects=True)

    # get filename from header
    dictionary = response.headers
    data = str(dictionary.get("Content-Disposition"))
    data = data[22:-2]
    filepath = (
        "/mnt/streamspot/" + data
    )

    # download with header filename
    with open(filepath, "wb") as file:
        file.write(response.content)
        file.close()

    logger.debug("Leaving download_file()")
    return response


# get the second newest study for Sunday 1st service
if mydate.strftime("%w") == "1":
    logger.debug("Entering if loop")
    open_session()
    # go to analytics page
    response = session.get(url + "/analytics/")

    # get the id_num_num of the latest study
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

    logger.debug("2nd: " + id_num)

    download_file()
    logger.debug("Leaving if loop")


open_session()

get_first_file_id()
download_file()
logger.info("GetViewers successful")


message = Mail(
    from_email=os.environ.get("EMAIL_FROM"),
    to_emails=os.environ.get("EMAIL_TO"),
    subject="Streamspot getviewers script ran successfully",
    html_content="This email indicates that the getviewers script ran without errors. <p>There is no guarantee that it ran correctly.</p>",
)


try:
    sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
    response = sg.send(
        message
    )  # https://docs.sendgrid.com/for-developers/sending-email/v3-python-code-example

except Exception as e:
    print(e.message)
