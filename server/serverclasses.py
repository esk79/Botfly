from flask_login import UserMixin


# Todo: turn into sqlite sometime
class UserManager:
    instance = None

    def __init__(self):
        self.users = {}
        self.unames = {}

        adminuser = User('admin','secret','admin_id')
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

    @classmethod
    def validate(cls, uname, passwd):
        inst = UserManager.getinstance()
        if uname in inst.unames:
            return inst.unames[uname].validate(passwd)
        return False

class User(UserMixin):
    def __init__(self, uname, passwd, uid):
        self.uname = uname
        self.uid = uid
        # TODO RED ALERT: FIX THIS FUCKERY
        self.passwd = passwd

    def get_id(self):
        return self.uid

    def validate(self,passwd):
        # TODO RED ALERT: FIX THIS FUCKERY
        return self.passwd == passwd