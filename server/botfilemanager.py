from threading import Lock
import pickle
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
        self.filedets = {}
        self.lock = Lock()
        self.outputdir = outputdir
        self.filenamefile = os.path.join(outputdir,BotNetFileManager.FILENAME_OBJFILE)
        if os.path.exists(self.filenamefile):
            with open(self.filenamefile,"rb") as jsonfile:
                self.filedets = pickle.load(jsonfile)
                for uf in list(self.filedets.keys()):
                    filepath = self.filedets[uf][0]
                    if not os.path.exists(filepath):
                        self.filedets.pop(uf)
            with open(self.filenamefile, "wb") as jsonfile:
                pickle.dump(self.filedets, jsonfile)

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
                return uf in self.filedets

    def appendBytesToFile(self, user, filename, wbytes):
        uf = (user, filename)
        with self.lock:
            if uf not in self.fileobjs:
                if uf in self.filedets:
                    real_filename = self.filedets[uf][0]
                    self.filedets.pop(uf)
                    os.remove(real_filename)
                filename = os.path.join(self.outputdir,str(uuid.uuid4()))
                self.fileobjs[uf] = open(filename, "wb")
                self.filedets[uf] = [filename,0,0]
                with open(self.filenamefile,"wb") as jsonfile:
                    pickle.dump(self.filedets, jsonfile)
            if not self.fileobjs[uf].closed:
                self.fileobjs[uf].write(wbytes)
                self.filedets[uf][1] += len(wbytes)

    def closeFile(self, user, filename):
        uf = (user, filename)
        with self.lock:
            if not self.fileobjs[uf].closed:
                self.fileobjs[uf].close()
            self.fileobjs.pop(uf)
            with open(self.filenamefile, "wb") as jsonfile:
                pickle.dump(self.filedets, jsonfile)

    def setFileSize(self, user, filename, filesize):
        uf = (user, filename)
        with self.lock:
            if uf not in self.fileobjs:
                if uf in self.filedets:
                    real_filename = self.filedets[uf][0]
                    self.filedets.pop(uf)
                    os.remove(real_filename)
                filename = os.path.join(self.outputdir, str(uuid.uuid4()))
                self.fileobjs[uf] = open(filename, "wb")
                self.filedets[uf] = [filename, 0, filesize]
            else:
                self.filedets[uf][2] = filesize
            with open(self.filenamefile, "wb") as jsonfile:
                pickle.dump(self.filedets, jsonfile)

    def getFilesAndInfo(self):
        '''
        Creates a list of fileinfo objects with {user, filename, size, downloaded}
        :return:
        '''
        # Get (user,file) list
        with self.lock:
            ufilenames = self.filedets.keys()
            fileinfo = []
            for key in ufilenames:
                (user, filename) = key
                uuidname, downloaded, size = self.filedets[key]
                fileinfo.append(dict(user=user,filename=filename,size=size,downloaded=downloaded))
            return fileinfo

    def getFileName(self, user, filename):
        uf = (user, filename)
        with self.lock:
            if uf in self.filedets:
                return self.filedets[uf][0]
            else:
                return None

    def deleteFile(self, user, filename):
        uf = (user, filename)
        with self.lock:
            if uf in self.filedets:
                if uf in self.fileobjs:
                    self.fileobjs[uf].close()
                real_filename = self.filedets[uf][0]
                self.filedets.pop(uf)
                try:
                    os.remove(real_filename)
                except:
                    pass
                with open(self.filenamefile, "wb") as jsonfile:
                    pickle.dump(self.filedets, jsonfile)
                return True
            return False
