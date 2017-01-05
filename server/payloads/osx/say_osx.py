'''
NAME: Say
DESCRIPTION: Send a say command to the victim with the provided text
VAR TEXT: The text to be said by the victim machine
'''
import os

os.system('say "{}"'.format(TEXT))
print "Successfully said: {}".format(TEXT)