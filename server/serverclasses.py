from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from server.flaskdb import db

# Todo: turn into sqlite sometime
class UserManager:
    instance = None

    def __init__(self):
        self.users = {}
        self.unames = {}

        adminuser = User('admin', 'secret', 'admin-id')
        self.users[adminuser.uid] = adminuser
        self.unames[adminuser.uname] = adminuser


    @staticmethod
    def getinstance():
        if UserManager.instance is None:
            UserManager.instance = UserManager()
        return UserManager.instance

    @staticmethod
    def get(user_id):
        inst = UserManager.getinstance()
        if user_id in inst.users:
            return inst.users[user_id]
        return None

    @staticmethod
    def getbyname(uname):
        inst = UserManager.getinstance()
        if uname in inst.unames:
            return inst.unames[uname]
        return None

    @staticmethod
    def validate(uname, passwd):
        inst = UserManager.getinstance()
        if uname in inst.unames:
            return inst.unames[uname].validate(passwd)
        return False

    @staticmethod
    def create_user(uname, passwd):
        inst = UserManager.getinstance()
        uid = uuid.uuid4()
        adminuser = User(uname, passwd, uid)
        inst.users[adminuser.uid] = adminuser
        inst.unames[adminuser.uname] = adminuser


class User(UserMixin,db.Model):
    __tablename__ = 'User'
    uid = db.Column(db.String(40), unique=True, primary_key=True)
    uname = db.Column(db.String(80), unique=True)
    pwhash = db.Column(db.String(80))
    def __init__(self, uname, passwd, uid):
        self.uname = uname
        self.uid = uid
        self.pwhash = generate_password_hash(passwd)

    def get_id(self):
        return self.uid

    def validate(self,passwd):
        return check_password_hash(self.pwhash, passwd)

    def __repr__(self):
        return '<User %r>' % self.uname