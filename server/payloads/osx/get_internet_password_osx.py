'''
NAME: Get Website Password
DESCRIPTION: Retrieve website credentials stored in the users keychain. Note, this requires the user clicking allow.
VAR WEBSITE: The website that you'd like the credentials for. (ie, 'www.facebook.com')
'''
import subprocess
import sys

command = ['security', 'find-internet-password', '-gs', WEBSITE]

proc = subprocess.Popen(command,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)

(out, err) = proc.communicate()

sys.stdout.write(out)
sys.stderr.write(err)






