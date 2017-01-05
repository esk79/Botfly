'''
NAME: Example File Download
DESCRIPTION:
VAR FILENAME: file to download
'''

if payloadlib.upload(FILENAME):
    print("Sending file "+FILENAME)
else:
    print("Error sending "+FILENAME)