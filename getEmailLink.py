import win32com.client
import re

def verifyEmail():

    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")

    inbox = outlook.Folders('Audio.Visual').Folders('Inbox')
    messages = inbox.Items.Restrict("[Subject] = 'MyStreamSpot - Verify Email'")
    messages.Sort('[ReceivedTime]', False)
    message = messages.GetLast()

    link = re.search(r'https:\/\/mystreamspot\.com\/login-confirmation\?vtoken\=.+?(?=>)', message.body).group(0)

    return link


verifyEmail()