# src/tests/test_room.py
import time
import sys
import os
import struct

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.common.protocol import Packet
from src.client.network.network_client import NetworkClient
from src.common.constants import *

def main():
    print("--- Room Management Test ---")
    
    # [Client 1] 방장
    host = NetworkClient()
    host.connect('127.0.0.1', 5000)
    host.login("HOST_USER")
    time.sleep(0.5) # 로그인 대기

    # 1. 방 생성 요청
    print("[1] Host creating room 'Tetris Battle'...")
    pkt = Packet(CMD_REQ_CREATE_ROOM, "Tetris Battle")
    host.send_packet(pkt)
    
    room_id = -1
    
    # 방 생성 응답 대기
    start = time.time()
    while time.time() - start < 2.0:
        pkt = host.get_packet()
        if pkt and pkt.cmd == CMD_RES_CREATE_ROOM:
            # Result(1B) + RoomID(2B)
            res, room_id = struct.unpack('>B H', pkt.body[:3])
            if res == 0:
                print(f"[Success] Room Created! RoomID: {room_id}")
            break
        elif pkt:
             # 로그인 응답 등은 무시
             pass
        time.sleep(0.1)

    if room_id == -1:
        print("[Fail] Room creation failed.")
        return

    # [Client 2] 참가자
    guest = NetworkClient()
    guest.connect('127.0.0.1', 5000)
    guest.login("GUEST_USER")
    time.sleep(0.5)

    # 2. 방 입장 요청
    print(f"[2] Guest joining Room #{room_id}...")
    # RoomID(2B)
    join_payload = struct.pack('>H', room_id)
    guest.send_packet(Packet(CMD_REQ_JOIN_ROOM, join_payload))
    
    # 입장 결과 확인
    start = time.time()
    while time.time() - start < 2.0:
        pkt = guest.get_packet()
        if pkt and pkt.cmd == CMD_RES_JOIN_ROOM:
            res, slot_id = struct.unpack('>B B', pkt.body[:2])
            if res == 0:
                print(f"[Success] Guest Joined! My Slot: {slot_id}")
            else:
                print(f"[Fail] Join Error Code: {res}")
            break
        time.sleep(0.1)

    host.disconnect()
    guest.disconnect()

if __name__ == "__main__":
    main()