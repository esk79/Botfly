'''
NAME: Send Email
DESCRIPTION: Sends a single email to provided RCPT with given MESSAGE
VAR RCPT_EMAIL: The email address of the recipient
VAR RCPT_NAME: The name of the recipient
VAR SUBJECT: The subject to send to RCPT
VAR MESSAGE: The message to send to RCPT
'''

import subprocess
import sys

script = '''set recipientName to "%s"
set recipientAddress to "%s"
set theSubject to "%s"
set theContent to "%s"

tell application "Mail"

        ##Create the message
        set theMessage to make new outgoing message with properties {subject:theSubject, content:theContent, visible:true}

        ##Set a recipient
        tell theMessage
                make new to recipient with properties {name:recipientName, address:recipientAddress}

                ##Send the Message
                send

        end tell
end tell''' % (RCPT_NAME, RCPT_EMAIL,SUBJECT, MESSAGE)

proc = subprocess.Popen(['osascript', '-'],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)

(out, err) = proc.communicate(script.encode('UTF-8'))

sys.stdout.write(out)
sys.stderr.write(err)