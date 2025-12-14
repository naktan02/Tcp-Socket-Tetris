# src/client/network_client.py
import socket
import threading
import queue
from src.common.config import HOST, PORT, BUFFER_SIZE
from src.common.protocol import Packet
from src.common.packet_handler import Packetizer
from src.common.constants import CMD_REQ_LOGIN

class NetworkClient:
    def __init__(self):
        self.sock = None
        self.is_running = False
        self.packet_queue = queue.Queue() # 메인 스레드로 패킷을 넘겨줄 큐
        self.packetizer = Packetizer()
        
        # 수신 스레드
        self.recv_thread = None

    def connect(self, ip=HOST, port=PORT):
        """서버 연결 시도"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, port))
            self.is_running = True
            
            # 수신 스레드 시작
            self.recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.recv_thread.start()
            print(f"[Network] Connected to {ip}:{port}")
            return True
        except Exception as e:
            print(f"[Network] Connection failed: {e}")
            return False

    def send_packet(self, packet):
        """패킷 전송"""
        if self.sock and self.is_running:
            try:
                self.sock.sendall(packet.to_bytes())
            except Exception as e:
                print(f"[Network] Send failed: {e}")
                self.disconnect()

    def login(self, nickname):
        """로그인 패킷 전송 편의 함수"""
        pkt = Packet(CMD_REQ_LOGIN, nickname)
        self.send_packet(pkt)

    def get_packet(self):
        """큐에서 패킷 꺼내기 (메인 루프에서 호출)"""
        if not self.packet_queue.empty():
            return self.packet_queue.get()
        return None

    def disconnect(self):
        self.is_running = False
        if self.sock:
            self.sock.close()
            self.sock = None
        print("[Network] Disconnected")

    def _receive_loop(self):
        """백그라운드에서 계속 데이터 수신"""
        while self.is_running and self.sock:
            try:
                data = self.sock.recv(BUFFER_SIZE)
                if not data:
                    break
                
                # 조립기에 넣고 패킷 완성되면 큐에 넣음
                self.packetizer.put_data(data)
                for packet in self.packetizer.get_packets():
                    self.packet_queue.put(packet)
                    
            except Exception:
                break
        
        self.disconnect()