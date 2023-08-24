<!-- @format -->

# Streamspot

streamspot_getviewers.py logs in to mystreamspot.com and pulls the newest unique-viewer analytics CSV file. Except on Mondays where it pulls the newest and second-newest because there are two Sunday videos. Create a cronjob/task scheduler to make it fully hands-off. Downloads the file to the folder the script is in.

streamspot_add_schedule.py logs into mystreamspot.com and fills in the form to add a broadcast. Because if you don't have the premium and want facebook integration you can't do recurring broadcasts. That gets old after a year or so. According to [XKCD](https://xkcd.com/1205) I'm saving 21 hours over the next five years.

streamspot_delete_archives.py logs into mystreamspot.com and deletes any expired archives so they aren't taking up Current Storage space.

streamspot_hide_video.py is a work in progress to hide the Sunday 2nd service video from end users on a weekly basis.
