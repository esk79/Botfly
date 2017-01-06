'''
NAME: Get Contacts
DESCRIPTION: Prints the buddy names of all the contacts in order to send iMessages
'''
import subprocess
import sys

script = '''tell application "Messages"
                get the full name of every buddy
            end tell'''

proc = subprocess.Popen(['osascript', '-'],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)

(out, err) = proc.communicate(script.encode('UTF-8'))

sys.stdout.write(out)
sys.stderr.write(err)




