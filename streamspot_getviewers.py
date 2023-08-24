"""
Get viewer numbers at the same time every week for comparison across weeks. 
Outlook Desktop application MUST be open for the email verification to work. 

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
from functions.getEmailLink import verifyEmail

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="streamspot.log",
)


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
    logging.info("Opening session")

    # log in
    response = session.post(url + "/login", data=values, allow_redirects=True)
    logging.info("Login response: " + response.url)
    logging.info("Checking for email verification")
    verifylink = verifyEmail()
    response = session.get(verifylink, allow_redirects=True)
    logging.info(response.request.headers)
    logging.info(response.url)

    # go to analytics page
    response = session.get(url + "/analytics/", timeout=20)
    logging.info(response.url)
    logging.info(response.headers)

    return response


def get_first_file_id():
    global response
    global session
    global id_num

    logging.info("Entering get_first_file_id()")
    id_num = str(re.search(r"=([A-Z])\w+==", response.text))
    id_num = id_num[46:59]
    logging.info(id_num)

    # get the id_num of the latest study
    if not id_num:
        time.sleep(30)
        id_num = str(re.search(r"=([A-Z])\w+==", response.text))
        id_num = id_num[46:59]

    logging.info("Leaving get_first_file_id()")
    return response, id_num


def download_file():
    global url
    global response
    global session
    global id_num

    logging.info("Entering download_file()")
    # switch to file download page
    link = url + "/analytics/export-event-uniques?id" + id_num
    response = session.get(link, allow_redirects=True)

    # get filename from header
    dictionary = response.headers
    data = str(dictionary.get("Content-Disposition"))
    data = data[22:-2]
    logging.info(data)
    filepath = (
        "C:/Users/Kristin/OneDrive - North Country Chapel/sundaystreams_stats/" + data
    )

    # download with header filename
    with open(filepath, "wb") as file:
        file.write(response.content)
        file.close()

    logging.info("Leaving download_file()")
    return response


# get the second newest study for Sunday 1st service
if mydate.strftime("%w") == "1":
    logging.info("Entering if loop")
    # go to analytics page
    response = session.get(url + "/analytics")

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

    logging.info("2nd: " + id_num)

    download_file()
    logging.info("Leaving if loop")


open_session()

get_first_file_id()
download_file()


message = Mail(
    from_email="kristin@northcountrychapel.com",
    to_emails="kristin@northcountrychapel.com",
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
