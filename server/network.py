import socket
import threading

from server.config import HOST, PORT
from server.lobby import Lobby
from server.game_session import GameManager
from server.client_session import ClientSession


class Server:
    def __init__(self):
        self.host = HOST
        self.port = PORT
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.alive = True

        self._next_player_id = 1
        self._id_lock = threading.Lock()

        self.lobby = Lobby(self)
        self.game_manager = GameManager()

    def next_player_id(self) -> int:
        with self._id_lock:
            pid = self._next_player_id
            self._next_player_id += 1
        return pid

    def start(self):
        self.sock.bind((self.host, self.port))
        self.sock.listen()
        print(f"[SERVER] Listening on {self.host}:{self.port}")
        try:
            while self.alive:
                conn, addr = self.sock.accept()
                session = ClientSession(self, conn, addr)
                session.start()
        finally:
            self.sock.close()
