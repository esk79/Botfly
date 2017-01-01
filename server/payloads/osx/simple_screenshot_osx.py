import os

import sys

'''Takes screenshot and saves image to bot's /tmp folder with a date-time stamp'''

if os.system('screencapture /tmp/screen-$(date +"%m_%d_%Y-%T").png') == 0:
    sys.stdout.write("Screenshot successful")
else:
    sys.stderr.write("Screenshot failed")