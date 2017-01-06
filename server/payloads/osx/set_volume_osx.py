'''
NAME: Set Volume
DESCRIPTION: Set the volume of the victim machine
VAR VOLUME = 100: The volume level out of 100, defaults to 100
'''
import os

set_volume = "osascript -e 'set volume output volume {}'"
os.system(set_volume.format(VOLUME))

print "Volume set to {}%".format(VOLUME)