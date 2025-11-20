import socket
import threading

from common.protocol import decode_line


class ClientConnection:
    def __init__(self, host: str, port: int):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.file = self.sock.makefile("rb")
        self.lock = threading.Lock()
        self.alive = True

    def send(self, data: bytes):
        with self.lock:
            try:
                self.sock.sendall(data)
            except OSError:
                self.alive = False

    def recv_packet(self):
        try:
            line = self.file.readline()
        except OSError:
            self.alive = False
            return None
        if not line:
            self.alive = False
            return None
        return decode_line(line)

    def close(self):
        self.alive = False
        try:
            self.sock.close()
        except OSError:
            pass
