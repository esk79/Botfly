'''
NAME: Dialog Box
DESCRIPTION: Pops up a native dialog box with the provided DIALOG text
VAR DIALOG: The text that will populate the pop-up (ie, "I'm watching you...")
VAR BUTTONS = OK: Add optional buttons to pop-up. Separate buttons with commas (ie, "Yes,No,Maybe") defaults to "OK"
'''
import subprocess
import sys

#ugly but chaining is actually proven best way to do multiple replace
buttons  = str(BUTTONS.split(',')).replace('[', '{').replace(']', '}').replace('\'', '"')
buttons = 'buttons ' + buttons

script = 'tell app "System Events" to display dialog "{}" {}'.format(DIALOG, buttons)
proc = subprocess.Popen(['osascript', '-'],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)

(out, err) = proc.communicate(script.encode('UTF-8'))

sys.stdout.write(out)
sys.stderr.write(err)