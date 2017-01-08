import os
import sys
import json


class BotNetPayloadManager:
    PAYLOAD_EXT = '.py'
    COMMENT_DELIMIT = ['"""',"'''"]
    VAR_DENOTE = 'VAR'

    def __init__(self, payloadpath):
        self.payloaddescriptions = {}
        self.payloadfiles = {}
        self.payloadpath = payloadpath
        for root, dirs, files in os.walk(self.payloadpath):
            for file in files:
                if file.endswith(BotNetPayloadManager.PAYLOAD_EXT):
                    filepath = os.path.join(root, file)
                    name, desc = self.parsePayload(filepath)
                    self.payloaddescriptions[name] = desc
                    self.payloadfiles[name] = filepath

    def getPayloads(self):
        return self.payloaddescriptions

    def getPayloadNames(self):
        return [payload for payload in self.payloaddescriptions.keys()]

    def parsePayload(self,payloadpath):
        with open(payloadpath,"r") as f:
            payloadlines = f.readlines()
        payloaddict = dict(name=payloadpath[len(self.payloadpath)+1:-len(BotNetPayloadManager.PAYLOAD_EXT)],
                           description='',
                           vars={})
        try:
            if payloadlines[0].strip() in BotNetPayloadManager.COMMENT_DELIMIT:
                for i in range(1,len(payloadlines)):
                    payloadline = payloadlines[i].strip()
                    if payloadline in BotNetPayloadManager.COMMENT_DELIMIT:
                        break
                    elif ':' in payloadline:
                        indx = payloadline.index(':')
                        lhs, rhs = payloadline[:indx].strip(), payloadline[indx+1:].strip()
                        if lhs.startswith(BotNetPayloadManager.VAR_DENOTE):
                            var = lhs[len(BotNetPayloadManager.VAR_DENOTE):].strip()
                            defval = None
                            if '=' in var:
                                eqindx = var.index('=')
                                defval = var[eqindx+1:].strip()
                                var = var[:eqindx].strip()
                            payloaddict['vars'][var] = {'description':rhs}
                            if defval is not None:
                                payloaddict['vars'][var]['default_value'] = defval
                        else:
                            payloaddict[lhs.lower()] = rhs
        except Exception as e:
            sys.stderr.write("[!] Error parsing {}: {}\n".format(payloadpath,str(e)))
            sys.stderr.flush()
        return payloaddict['name'], payloaddict

    def getPayloadText(self, payload, args):
        if payload not in self.payloaddescriptions:
            return None
        vars = self.payloaddescriptions[payload]['vars']
        vartext = ""
        for reqvar in vars.keys():
            if reqvar in args and len(args[reqvar])>0:
                arg = json.dumps(args[reqvar])
                vartext += '{}={}\n'.format(reqvar,arg)
            elif 'default_value' in vars[reqvar]:
                arg = json.dumps(vars[reqvar]['default_value'])
                vartext += '{}={}\n'.format(reqvar, arg)
        with open(self.payloadfiles[payload],"r") as f:
            payloadtext = f.read()
            return vartext + payloadtext
