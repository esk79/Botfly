import struct
import sys


def formatBytes(msg):
    '''
    Takes str or bytes and produces bytes where the first 4 bytes
    correspond to the message length
    :param msg: input message
    :return: <[length][message]>
    '''
    if type(msg) == str:
        msg = str.encode(msg)
    if type(msg) == bytes:
        return (struct.pack('>i', len(msg)) + msg)
    else:
        raise Exception("msg must be of type bytes or str")


def recvFormatBytes(recvable):
    '''
    Receives bytes from recvable, expects first 4 bytes to be length of message,
    then receives that amount of data and returns raw bytes of message
    :param recvable: Any object with recv(bytes) function
    :return:
    '''
    total_len = 0
    total_data = b''
    size = sys.maxsize
    size_data = b''
    recv_size = 8192
    while total_len < size:
        sock_data = recvable.recv(recv_size)
        if not total_data:
            if len(sock_data) > 4:
                size_data += sock_data
                size = struct.unpack('>i', size_data[:4])[0]
                recv_size = min(524288, size)
                total_data += size_data[4:]
            else:
                size_data += sock_data
        else:
            total_data += sock_data
        total_len = len(total_data)
    return total_data