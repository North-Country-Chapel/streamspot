"""
Automates checking email account for verification email for streamspot scripts.
Outlook Desktop application MUST be open for the verifyEmail to work.
verifyEmailGraph does not require Outlook to be open. 

"""

import requests
import win32com.client
import re
import logging
import time
from datetime import datetime, timedelta
import os
from html import unescape


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename="streamspot.log",
)


def verifyEmail():
    time.sleep(60)
    logging.info("Verifying email")
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

    inbox = outlook.Folders("Audio.Visual").Folders("Inbox")
    messages = inbox.Items.Restrict("[Subject] = 'MyStreamSpot - Verify Email'")

    messages.Sort("[ReceivedTime]", False)
    message = messages.GetLast()
    logging.info("Message time: " + str(message.ReceivedTime))
    link_regex = re.compile(
        "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    )
    link = re.findall(link_regex, message.body)[1]
    logging.info(link)

    message.Unread = False
    logging.info("Message marked as read")

    return link


# https://learn.microsoft.com/en-us/office/vba/api/outlook.items


def verifyEmailGraph():
    time.sleep(60)
    # Azure AD application details
    client_id = os.environ.get("MS_CLIENT_ID")
    client_secret = os.environ.get("MS_CLIENT_SECRET")
    tenant_id = os.environ.get("MS_TENANT_ID")
    mailbox_id = os.environ.get("AV_MAILBOX_ID")

    # Microsoft Graph API endpoints
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
    graph_api_url = f"https://graph.microsoft.com/v1.0/users/{mailbox_id}/messages"

    # 5 minute timer
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=2)
    formatted_time = five_minutes_ago.strftime("%Y-%m-%dT%H:%M:%SZ")

    subject = "MyStreamSpot - Verify Email"

    # Get an access token
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "resource": "https://graph.microsoft.com",
    }

    token_response = requests.post(token_url, data=token_data)
    access_token = token_response.json().get("access_token")

    # Get email request
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Filter email by title and time recieved
    params = {
        "$filter": f"subject eq '{subject}'",
        "$filter": f"receivedDateTime ge {formatted_time}",
        # "$orderby": "receivedDateTime desc",
    }

    response = requests.get(graph_api_url, headers=headers, params=params)

    if response.status_code == 200:
        emails = response.json().get("value", [])
        link = None

        for email in emails:
            body = email.get("body", {}).get("content")
            message_id = email.get("id")
            logging.debug(message_id)
            link_regex = re.compile(
                "http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
            )
            links = re.findall(link_regex, body)
            # There's an &amp; that messes up the link
            # I'm sure it's some encoding difference with Graph API
            unescaped_links = [unescape(link) for link in links]
            logging.debug(unescaped_links)

            if unescaped_links:
                link = unescaped_links[1]
                logging.debug(link)

            # Mark the email as read
            mark_as_read_url = f"https://graph.microsoft.com/v1.0/users/8f2584e3-ce39-4cd7-bb4b-83efac00797b/messages/{message_id}"
            mark_as_read_payload = {"isRead": True}

            mark_as_read_response = requests.patch(
                mark_as_read_url, headers=headers, json=mark_as_read_payload
            )

            if mark_as_read_response.status_code == 200:
                logging.info("Latest email marked as read successfully.")
            else:
                logging.warning(
                    f"Error marking email as read: {mark_as_read_response.status_code}, {mark_as_read_response.text}"
                )
            logging.info(link)

    else:
        logging.warning(f"Error: {response.status_code}, {response.text}")

    return link
