# src/common/errors.py

class TetrisError(Exception):
    """프로젝트 기본 예외"""
    pass

class ProtocolError(TetrisError):
    """패킷 구조가 잘못되었거나 약속된 CMD가 아닐 때"""
    pass

class DisconnectedError(TetrisError):
    """소켓 연결이 끊어졌을 때"""
    pass