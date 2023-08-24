import requests
import time
import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import logging
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
    logging.info("Opening session")

    # log in
    response = session.post(url + "/login", data=values, allow_redirects=True)
    logging.info(response.url)
    time.sleep(10)
    logging.info("Checking for email verification")
    verifylink = verifyEmail()
    response = session.get(verifylink, allow_redirects=True)
    logging.info(response.url)
    logging.info(response.headers)

    # go to expired-archive page
    response = session.get(url + "/archive/expired-archives")
    logging.info(response.url)
    logging.info(response.headers)

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

    if response.status_code != "200":
        raise DeleteError
    else:
        logging.info("Delete successful")

except:
    message = Mail(
        from_email="kristin@northcountrychapel.com",
        to_emails="kristin@northcountrychapel.com.com",
        subject="Streamspot delete archive script did not complete ",
        html_content="This email indicates that the delete archive script did not run as expected. <p>Check to make sure expired studies were deleted on the site.</p>",
    )

    sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
    response = sg.send(message)
