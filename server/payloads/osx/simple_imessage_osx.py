'''
NAME: Send Text
DESCRIPTION: Sends a single iMessage or SMS to provided BUDDY with given MESSAGE
VAR BUDDY: The name (as defined in the bot's contacts) or number of the text recipient
VAR MESSAGE: The message to send to BUDDY
'''

import os
import subprocess
import sys

version = os.system('')

proc = subprocess.Popen(['sw_vers'],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)

(out, err) = proc.communicate()

version = out.split("ProductVersion:", 1)[1].split('\n')[0].strip()

if '10.11' not in version:
    iMessage = '''tell application "Messages" to send "{}" to buddy "{}"'''.format(MESSAGE, BUDDY)

    proc = subprocess.Popen(['osascript', '-'],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    out, err = proc.communicate(iMessage.encode('UTF-8'))

else:
    sys.stderr.write("Can't send text on osx 10.11")
