# src/tests/test_protocol.py
import sys
import os
import unittest

# 현재 파일 위치: src/tests/test_protocol.py
# 목표: 프로젝트 루트(Tcp-Socket-Tetris/)를 sys.path에 추가해야 'src' 패키지를 찾을 수 있음
current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, '..', '..')) # 두 단계 위로 이동
sys.path.append(project_root)

from src.common.protocol import Packet
from src.common.packet_handler import Packetizer
from src.common.constants import CMD_REQ_LOGIN

class TestProtocol(unittest.TestCase):
    def test_packet_encoding(self):
        """패킷이 바이트로 잘 변환되는지 테스트"""
        cmd = CMD_REQ_LOGIN  # 0x01
        body = b'HERO'
        pkt = Packet(cmd, body)
        
        serialized = pkt.to_bytes()
        
        # 예상: [LEN=5 (00 05)] [CMD=01] [H E R O]
        expected = b'\x00\x05\x01HERO'
        self.assertEqual(serialized, expected)
        print(f"[Pass] Encoding: {serialized.hex()}")

    def test_packet_fragmentation(self):
        """패킷이 쪼개져서 들어왔을 때 잘 조립하는지 테스트"""
        packetizer = Packetizer()
        
        # "Login" 패킷을 생성 -> 바이트로 변환
        full_data = Packet(CMD_REQ_LOGIN, b'TESTUSER').to_bytes()
        
        # 상황: 데이터가 두 번에 걸쳐서 쪼개져서 도착함
        part1 = full_data[:4] # 앞부분 4바이트
        part2 = full_data[4:] # 뒷부분 나머지
        
        # 1. 앞부분만 넣음 -> 패킷이 나오면 안 됨
        packetizer.put_data(part1)
        packets = list(packetizer.get_packets())
        self.assertEqual(len(packets), 0)
        
        # 2. 뒷부분 넣음 -> 패킷이 완성되어 나와야 함
        packetizer.put_data(part2)
        packets = list(packetizer.get_packets())
        self.assertEqual(len(packets), 1)
        
        received_pkt = packets[0]
        self.assertEqual(received_pkt.cmd, CMD_REQ_LOGIN)
        self.assertEqual(received_pkt.body, b'TESTUSER')
        print(f"[Pass] Fragmentation Test Success")

if __name__ == '__main__':
    unittest.main()