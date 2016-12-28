# Botfly
- Not meant for malicious purposes, simply a P.O.C. for educational purposes

#Changle log

2/28: Can download from GUI. Type 'download <filename>' from terminal. Test with 'download example.txt'. This is no error handling yet and file paths are not relative as they will need to be
2/27: Terminal zoom in/out complete. To use, click inside terminal and use 'cmd+{plus key}' or 'cmd+{minus key}' respectively.
2/27: File upload complete. Clicking "Upload File" from gui and selecting a file will upload that file to the current directory on the bot.
        - The file is not deleted off of the server (though it should be). Would need to wait for success from bot before deleting in order to avoid possible race conditon
