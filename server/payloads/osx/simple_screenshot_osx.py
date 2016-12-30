import os

'''Takes screenshot and saves image to bot's /tmp folder with a date-time stamp'''

os.system('screencapture /tmp/screen-$(date +"%m_%d_%Y-%T").png')
