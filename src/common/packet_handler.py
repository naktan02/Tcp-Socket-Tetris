# src/common/packet_handler.py
from .protocol import Packet
from .config import HEADER_SIZE

class Packetizer:
    """
    TCP 스트림 데이터를 받아서 완성된 패킷 단위로 잘라주는 클래스
    """
    def __init__(self):
        self.buffer = b''

    def put_data(self, data):
        """수신된 데이터를 버퍼에 추가"""
        if data:
            self.buffer += data

    def get_packets(self):
        """버퍼에서 완성된 패킷들을 하나씩 꺼내서 반환 (Generator)"""
        while True:
            # 1. 헤더(LEN)를 읽을 수 있는지 확인
            if len(self.buffer) < HEADER_SIZE:
                break # 데이터가 부족함

            # 2. 패킷 길이 파악 (Peek)
            # Packet.parse_header는 CMD+BODY 길이를 반환함
            payload_len = Packet.parse_header(self.buffer[:HEADER_SIZE])
            total_packet_len = HEADER_SIZE + payload_len

            # 3. 전체 패킷이 도착했는지 확인
            if len(self.buffer) < total_packet_len:
                break # 아직 바디가 다 안 옴

            # 4. 패킷 분리 (Slicing)
            # [LEN(2)] [CMD(1)] [BODY(...)]
            # packet_data는 CMD부터 끝까지
            raw_payload = self.buffer[HEADER_SIZE : total_packet_len]
            
            # 버퍼에서 잘라낸 부분 삭제
            self.buffer = self.buffer[total_packet_len:]

            # 5. CMD와 BODY 분리
            cmd = raw_payload[0]
            body = raw_payload[1:]

            yield Packet(cmd, body)

    def has_data(self):
        return len(self.buffer) > 0