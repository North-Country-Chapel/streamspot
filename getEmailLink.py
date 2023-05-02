import win32com.client
import re
import logging


logging.basicConfig(
    level= logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename= "streamspot.log",
)


def verifyEmail():
    # time.sleep(10)
    logging.info("Verifying email")
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

    inbox = outlook.Folders('Audio.Visual').Folders('Inbox')
    messages = inbox.Items.Restrict("[Subject] = 'MyStreamSpot - Verify Email'")

    messages.Sort('[ReceivedTime]', False)
    message = messages.GetLast()
    logging.info("Message time: " + str(message.ReceivedTime))
    link_regex = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    link = re.findall(link_regex, message.body)[1]
    logging.info(link)

    message.Unread = False
    logging.info("Message marked as read")

    return link



# https://learn.microsoft.com/en-us/office/vba/api/outlook.items

