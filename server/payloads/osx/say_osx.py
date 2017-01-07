'''
NAME: Say
DESCRIPTION: Send a say command to the victim with the provided text
VAR TEXT: The text to be said by the victim machine
VAR VOLUME = 100: The volume of the victim machine, defaults to 100/100
'''
import os
import subprocess

check_volume = 'set ovol to output volume of (get volume settings)\nreturn ovol'
set_volume = "osascript -e 'set volume output volume {}'"

proc = subprocess.Popen(['osascript', '-'],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)

out, err = proc.communicate(check_volume.encode('UTF-8'))
vol = out.decode('UTF-8')

os.system(set_volume.format(VOLUME))
os.system('say "{}"'.format(TEXT))
os.system(set_volume.format(vol))

print("Successfully said: {}".format(TEXT))