# Streamspot
Learning python by automating streamspot stuff with some python scripts

a_streamspot_getviewers.py logs in to mystreamspot.com and pulls the newest unique-viewer analytics CSV file. Except on Mondays where it pulls the newest and second-newest because there are two Sunday videos. Create a cronjob/task scheduler to make it fully hands-off. Downloads the file to the folder the script is in.
