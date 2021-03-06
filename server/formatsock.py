import struct
import sys
import threading


class FormatSocket:
    SIZE_BYTES = 4
    RECV_SIZE = 8192

    def __init__(self, sock):
        self.sock = sock
        self.lastbytes = b''
        self.sendlock = threading.Lock()
        self.recvlock = threading.Lock()

    def send(self,msg):
        '''
        Takes str or bytes and produces bytes where the first 4 bytes
        correspond to the message length
        :param msg: input message
        :return: <[length][message]>
        '''
        if type(msg) == str:
            msg = str.encode(msg)
        if type(msg) == bytes:
            with self.sendlock:
                self.sock.sendall(struct.pack('>i', len(msg)) + msg)
        else:
            raise Exception("msg must be of type bytes or str")

    def closeswapsock(self, newsock):
        # Needs both locks to stop other threads from working with socket
        with self.sendlock:
            # Closing should stop any recv that may be happening
            self.sock.close()
            with self.recvlock:
                self.sock = newsock

    def recv(self):
        '''
        Receives bytes from recvable, expects first 4 bytes to be length of message,
        then receives that amount of data and returns raw bytes of message
        :param recvable: Any object with recv(bytes) function
        :return:
        '''
        with self.recvlock:
            total_data = self.lastbytes
            self.lastbytes = b''

            msg_data = b''
            expected_size = sys.maxsize
            if len(total_data) > FormatSocket.SIZE_BYTES:
                size_data = total_data[:FormatSocket.SIZE_BYTES]
                expected_size = struct.unpack('>i',size_data)[0]
                msg_data += total_data[FormatSocket.SIZE_BYTES:]

            while len(msg_data) < expected_size:
                sock_data = self.sock.recv(FormatSocket.RECV_SIZE)
                if len(sock_data) == 0:
                    raise IOError("Connection interrupted")

                total_data += sock_data
                if expected_size == sys.maxsize and len(total_data) > FormatSocket.SIZE_BYTES:
                    size_data = total_data[:FormatSocket.SIZE_BYTES]
                    expected_size = struct.unpack('>i',size_data)[0]
                    msg_data += total_data[FormatSocket.SIZE_BYTES:]
                else:
                    msg_data += sock_data
            # Store anything above expected size for next time
            self.lastbytes = msg_data[expected_size:]
            return msg_data[:expected_size]

    def rawsend(self,bs):
        with self.sendlock:
            self.sock.send(bs)

    def rawrecv(self,size):
        with self.recvlock:
            return self.sock.recv(size)

    def fileno(self):
        with self.sendlock:
            return self.sock.fileno()

    def close(self):
        # Allowed to close while recv, not while sending
        with self.sendlock:
            return self.sock.close()
