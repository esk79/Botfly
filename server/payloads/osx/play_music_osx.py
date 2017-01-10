'''
NAME: Play Music
DESCRIPTION: Plays the provided audio file with no visible way of stopping it
VAR FILE: Path to audio file on the bot machine
'''
import os
import sys

if os.system('afplay {}'.format(FILE)) == 0:
    sys.stdout.write("Success!")
else:
    sys.stderr.write("Error!")
