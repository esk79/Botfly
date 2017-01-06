'''
NAME: Dialog Box
DESCRIPTION: Pops up a native dialog box with the provided DIALOG text
VAR DIALOG: The text that will populate the pop-up (ie, "I'm watching you...")
'''
import subprocess
import sys

script = 'tell app "System Events" to display dialog "{}"'.format(DIALOG)
proc = subprocess.Popen(['osascript', '-'],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)

(out, err) = proc.communicate(script.encode('UTF-8'))

sys.stdout.write(out)
sys.stderr.write(err)