# src/server/server_core.py
import socket
import selectors
import sys
import os
import struct
# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.server.game.room_manager import room_manager
from src.common.config import HOST, PORT, BUFFER_SIZE
from src.server.infra.client_peer import ClientPeer
from src.server.infra.router import router
from src.common.utils import get_local_ip
from src.common.protocol import Packet
from src.common.constants import *

# 핸들러 모듈을 임포트해야 데코레이터가 실행되어 라우터에 등록됨
import src.server.handlers.connection 
import src.server.handlers.room
import src.server.handlers.game

class TetrisServer:
    def __init__(self):
        self.sel = selectors.DefaultSelector()
        self.clients = {} # socket -> ClientPeer

    def start(self):
        """서버 시작"""
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((HOST, PORT))
        server_sock.listen()
        server_sock.setblocking(False)

        # 서버 소켓을 감시 대상에 등록 (새로운 연결이 오면 accept 호출)
        self.sel.register(server_sock, selectors.EVENT_READ, data=None)
        
        local_ip = get_local_ip()
        print(f"========================================")
        print(f" [Server] Started on {local_ip}:{PORT}")
        print(f" [Info] Tell your friend to connect to: {local_ip}")
        print(f"========================================")

        try:
            while True:
                # 이벤트 대기 (블로킹)
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        # 1. 새로운 연결 요청 (ServerSocket)
                        self._accept_wrapper(key.fileobj)
                    else:
                        # 2. 기존 클라이언트의 데이터 수신
                        client = key.data
                        self._service_connection(key, mask, client)
        except KeyboardInterrupt:
            print("\n[Server] Shutting down...")
        finally:
            self.sel.close()
            server_sock.close()

    def _accept_wrapper(self, sock):
        conn, addr = sock.accept()  # 연결 수락
        print(f"[Connect] New connection from {addr}")
        conn.setblocking(False)
        
        # 클라이언트 객체 생성 및 등록
        client = ClientPeer(conn, addr)
        self.clients[conn] = client
        
        # 셀렉터에 등록 (데이터 수신 감시)
        self.sel.register(conn, selectors.EVENT_READ, data=client)

    def _service_connection(self, key, mask, client):
        sock = key.fileobj
        if mask & selectors.EVENT_READ:
            try:
                data = sock.recv(BUFFER_SIZE)
                if data:
                    # 1. 받은 데이터를 패킷 조립기에 넣음
                    client.packetizer.put_data(data)
                    
                    # 2. 완성된 패킷이 있으면 하나씩 꺼내서 처리
                    while True:
                        try:
                            # generator에서 패킷 하나 꺼내기 (next)
                            packet = next(client.packetizer.get_packets())
                            # 라우터에게 패킷 전달
                            router.handle(client, packet)
                        except StopIteration:
                            break # 더 이상 완성된 패킷 없음
                else:
                    # 데이터가 없으면 연결 종료 신호
                    self._close_connection(key, client)
            except ConnectionResetError:
                self._close_connection(key, client)

    def _close_connection(self, key, client):
        print(f"[Disconnect] Closed connection from {client.addr}")
        
        # [NEW] 강제 종료 시 방에서 퇴장 처리 로직 추가 =====================
        if hasattr(client, 'room_id') and client.room_id is not None:
            room = room_manager.get_room(client.room_id)
            if room:
                slot_id = room.leave_user(client)
                if slot_id != -1:
                    print(f"[Room] {client.nickname} forced leave Room #{room.room_id}")
                    # 남은 사람들에게 알림
                    noti = Packet(CMD_NOTI_LEAVE_ROOM, struct.pack('>B', slot_id))
                    room.broadcast(noti)
                    
                if room.is_empty():
                    room_manager.remove_room(room.room_id)
                    print(f"[Room] Room #{room.room_id} deleted (Empty)")
        # =================================================================
        
        self.sel.unregister(key.fileobj)
        key.fileobj.close()
        del self.clients[key.fileobj]

if __name__ == "__main__":
    server = TetrisServer()
    server.start()