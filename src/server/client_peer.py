# src/server/client_peer.py
import socket
from src.common.packet_handler import Packetizer

class ClientPeer:
    """
    서버에 접속한 클라이언트 객체 래퍼
    소켓, 주소, 닉네임, 수신 버퍼 등을 관리함
    """
    def __init__(self, conn: socket.socket, addr):
        self.conn = conn
        self.addr = addr       # (IP, Port)
        self.nickname = "Unknown"
        self.packetizer = Packetizer() # 패킷 조립기 (TCP 스트림 처리용)
        self.is_authenticated = False  # 로그인 여부

    def send_packet(self, packet):
        """패킷 객체를 바이트로 변환하여 전송"""
        try:
            self.conn.sendall(packet.to_bytes())
        except OSError:
            pass # 연결이 끊긴 경우 처리는 server_core에서 담당

    def __repr__(self):
        return f"<Client {self.nickname}@{self.addr[0]}>"