# src/tests/test_game_sync.py
import time
import sys
import os
import struct
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.client.network.network_client import NetworkClient
from src.common.constants import *

def run_client(nickname, room_id, is_host):
    client = NetworkClient()
    client.connect('127.0.0.1', 5000)
    client.login(nickname)
    time.sleep(0.2)

    # 방 입장 (호스트는 생성, 게스트는 입장)
    if is_host:
        client.send_packet(from_packet(CMD_REQ_CREATE_ROOM, "Battle Room"))
        # 응답 대기 (생략 - 실제론 RoomID 받아야 함)
        time.sleep(0.5)
    else:
        # 방 번호 1번 가정
        client.send_packet(from_packet(CMD_REQ_JOIN_ROOM, struct.pack('>H', 1)))
        time.sleep(0.5)

    print(f"[{nickname}] Sending READY...")
    client.send_packet(from_packet(CMD_REQ_TOGGLE_READY, b''))

    # 게임 시작 신호 대기
    start_time = time.time()
    while time.time() - start_time < 3.0:
        pkt = client.get_packet()
        if pkt:
            if pkt.cmd == CMD_NOTI_GAME_START:
                seed = struct.unpack('>I', pkt.body)[0]
                print(f"[{nickname}] GAME START RECEIVED! Seed: {seed}")
                client.disconnect()
                return
        time.sleep(0.1)
    
    print(f"[{nickname}] Timed out waiting for start.")
    client.disconnect()

def from_packet(cmd, body):
    # 테스트 편의용 패킷 생성 헬퍼
    from src.common.protocol import Packet
    if isinstance(body, str): body = body.encode('utf-8')
    return Packet(cmd, body)

if __name__ == "__main__":
    # 서버가 켜져 있어야 합니다.
    # 스레드로 두 명의 클라이언트를 동시 실행
    t1 = threading.Thread(target=run_client, args=("P1_HOST", 1, True))
    t2 = threading.Thread(target=run_client, args=("P2_GUEST", 1, False))

    t1.start()
    time.sleep(1) # 방 만들 시간 줌
    t2.start()

    t1.join()
    t2.join()