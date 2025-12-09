# src/server/handlers/game.py
import struct
from src.server.router import router
from src.server.room_manager import room_manager
from src.common.protocol import Packet
from src.common.constants import *

@router.route(CMD_REQ_TOGGLE_READY)
def handle_toggle_ready(client, packet):
    """준비 상태 변경 요청"""
    if not hasattr(client, 'room_id') or client.room_id is None:
        return

    room = room_manager.get_room(client.room_id)
    if not room: return

    # 1. 내 슬롯 찾기
    my_slot = -1
    for i, user in enumerate(room.slots):
        if user == client:
            my_slot = i
            break
    
    if my_slot == -1: return

    if my_slot == 0:
        if room.can_start_game():
            room.start_game()
        else:
            # (선택) 시작 불가능하면 로그 출력 or 에러 패킷 전송
            print(f"[Room #{room.room_id}] Host tried to start, but guests are not ready.")
    
    # [수정] 일반 유저인 경우 -> Ready 토글
    else:
        is_ready = room.toggle_ready(my_slot)
        state_val = 1 if is_ready else 0
        
        # 변경 사실 알림 (NOTI_READY_STATE)
        noti_payload = struct.pack('>B B', my_slot, state_val)
        room.broadcast(Packet(CMD_NOTI_READY_STATE, noti_payload))


@router.route(CMD_REQ_MOVE)
def handle_move(client, packet):
    """
    이동 패킷 중계 (Relay)
    받은 키 입력을 같은 방의 다른 사람에게 그대로 전달
    """
    if not hasattr(client, 'room_id') or client.room_id is None:
        return
    
    room = room_manager.get_room(client.room_id)
    if not room or not room.is_playing: return

    # 패킷 구조: [KeyCode(1B)]
    if len(packet.body) < 1: return
    keycode = packet.body[0]

    # 내 슬롯 번호 찾기
    my_slot = -1
    for i, user in enumerate(room.slots):
        if user == client:
            my_slot = i
            break
    
    if my_slot == -1: return

    # 상대방에게 알림 (NOTI_MOVE)
    # 구조: [SlotID(1B)] [KeyCode(1B)]
    # 나를 제외한(exclude_client=client) 모두에게 전송
    relay_payload = struct.pack('>B B', my_slot, keycode)
    room.broadcast(Packet(CMD_NOTI_MOVE, relay_payload), exclude_client=client)