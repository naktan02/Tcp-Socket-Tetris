# src/common/protocol.py
import struct
from .config import HEADER_SIZE

class Packet:
    """
    네트워크 패킷 객체
    구조: [LEN(2)] + [CMD(1)] + [BODY(N)]
    """
    def __init__(self, cmd, body=b''):
        self.cmd = cmd
        self.body = body
        if isinstance(self.body, str):
            self.body = self.body.encode('utf-8')

    def to_bytes(self):
        """객체를 전송 가능한 바이트로 변환 (Serialize)"""
        # CMD(1) + Body 길이
        payload_len = 1 + len(self.body)
        
        # >H: Big-Endian Unsigned Short (2 bytes)
        # B: Unsigned Char (1 byte)
        header = struct.pack('>H B', payload_len, self.cmd)
        
        return header + self.body

    @staticmethod
    def parse_header(header_bytes):
        """헤더(2바이트)를 읽어 Payload(CMD+Body) 길이를 반환"""
        # 결과값: (length, ) 튜플
        return struct.unpack('>H', header_bytes)[0]

    def __repr__(self):
        return f"<Packet CMD={hex(self.cmd)} LEN={len(self.body)}>"