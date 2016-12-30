# Botfly
- Not meant for malicious purposes, simply a P.O.C. for educational purposes

### Change log
- 2/29: Ease of use improvements. Download fixes. Now can send payloads for execution on client.py
- 2/28: Can download from GUI. Type 'download <filename>' from terminal. Test with 'download example.txt'. This is no error handling yet and file paths are not relative as they will need to be. File upload/download redesign, no longer stored on server, instead based on bytestreams through server. Prevents above mentioned race conditions. Also implmented introductory directory listings: Work starts on GUI section.
- 2/27: Terminal zoom in/out complete. To use, click inside terminal and use 'cmd+{plus key}' or 'cmd+{minus key}' respectively.
- 2/27: File upload complete. Clicking "Upload File" from gui and selecting a file will upload that file to the current directory on the bot.
  - The file is not deleted off of the server (though it should be). Would need to wait for success from bot before deleting in order to avoid possible race conditon
- 2/27: Log Started

### Payload Ideas
- Get current location of computer using IP
- Install traditional backdoor
- Install client.py script into all available word docs using macros (possibly spreading to other computers)
- Webcam/Screenshot
- Scan network devices, map local network
- Fake security alert, ask for password (maybe download java application to do this?)
- Download `.ssh/id_rsa`
- Test connections listed in `.ssh/known_hosts` to check if any will allow connection without password (i.e. key based), if connected then upload client.py to new bot