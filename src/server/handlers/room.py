# src/server/handlers/room.py
import struct
from src.server.router import router
from src.server.room_manager import room_manager
from src.common.protocol import Packet
from src.common.constants import *

@router.route(CMD_REQ_CREATE_ROOM)
def handle_create_room(client, packet):
    """방 생성 요청: [Title(Str)]"""
    try:
        title = packet.body.decode('utf-8')
        room = room_manager.create_room(title)
        
        print(f"[Room] Created Room #{room.room_id} '{title}' by {client.nickname}")
        
        # 1. 생성 결과 전송 (RES_CREATE_ROOM)
        # 구조: [Result(1B)] [RoomID(2B)]
        # Result: 0=성공
        payload = struct.pack('>B H', 0, room.room_id)
        client.send_packet(Packet(CMD_RES_CREATE_ROOM, payload))
        
        # 2. 자동으로 방 입장 처리
        slot_id = room.enter_user(client)
        client.room_id = room.room_id # 클라이언트에 현재 방 번호 기록
        
        # 방장이므로 입장 결과(RES_JOIN_ROOM)나 NOTI는 생략하거나 필요 시 전송
        # (PPT 흐름상 RES_CREATE_ROOM 받은 클라가 자동으로 입장 UI로 전환한다고 가정)

    except Exception as e:
        print(f"[Error] Create Room Failed: {e}")

@router.route(CMD_REQ_JOIN_ROOM)
def handle_join_room(client, packet):
    """방 입장 요청: [RoomID(2B)]"""
    if len(packet.body) < 2:
        return
        
    room_id = struct.unpack('>H', packet.body[:2])[0]
    room = room_manager.get_room(room_id)
    
    if not room:
        # 실패 응답 (Result=1)
        client.send_packet(Packet(CMD_RES_JOIN_ROOM, b'\x01\x00'))
        return
    # [Check] 게임 중이면 입장 불가 (혹은 관전)
    if room.is_playing:
        client.send_packet(Packet(CMD_RES_JOIN_ROOM, b'\x03\x00')) # Error 3: Playing
        return
    slot_id = room.enter_user(client)
    if slot_id == -1:
        # 방 꽉 참 (Result=2)
        client.send_packet(Packet(CMD_RES_JOIN_ROOM, b'\x02\x00'))
        return

    client.room_id = room.room_id
    print(f"[Room] {client.nickname} joined Room #{room_id} (Slot {slot_id})")

    # 1. 나에게: 입장 성공 응답 (RES_JOIN_ROOM)
    # 구조: [Result(1B)] [MySlotID(1B)]
    resp = struct.pack('>B B', 0, slot_id)
    client.send_packet(Packet(CMD_RES_JOIN_ROOM, resp))
    
    # 2. 다른 사람들에게: 입장 알림 (NOTI_ENTER_ROOM)
    # 구조: [SlotID(1B)] [NickName(Str)]
    noti_body = struct.pack('>B', slot_id) + client.nickname.encode('utf-8')
    room.broadcast(Packet(CMD_NOTI_ENTER_ROOM, noti_body), exclude_client=client)

    # [Refactor] 기존 유저 목록 전송 로직 삭제 (CMD_REQ_ROOM_INFO로 대체)

@router.route(CMD_REQ_LEAVE_ROOM)
def handle_leave_room(client, packet):
    """방 퇴장 요청"""
    if not hasattr(client, 'room_id') or client.room_id is None:
        return

    room = room_manager.get_room(client.room_id)
    if room:
        slot_id = room.leave_user(client)
        print(f"[Room] {client.nickname} left Room #{room.room_id}")
        
        # 다른 사람들에게: 퇴장 알림 (NOTI_LEAVE_ROOM)
        # 구조: [SlotID(1B)]
        if slot_id != -1:
            room.broadcast(Packet(CMD_NOTI_LEAVE_ROOM, struct.pack('>B', slot_id)))
            
        # 방이 비었으면 삭제
        if room.is_empty():
            room_manager.remove_room(room.room_id)
            print(f"[Room] Room #{room.room_id} deleted (Empty)")
            
    client.room_id = None

@router.route(CMD_REQ_SEARCH_ROOM)
def handle_search_room(client, packet):
    """
    방 목록 요청 처리
    응답 구조: [Count(1B)] + 반복([ID(2B)] + [TitleLen(1B)] + [Title(Str)])
    """
    rooms = room_manager.get_all_rooms()
    
    # 패킷 조립
    payload = bytearray()
    payload.append(len(rooms)) # 방 개수
    
    for room in rooms:
        # 방 ID (2Bytes)
        payload.extend(struct.pack('>H', room.room_id))
        status = 1 if room.is_playing else 0
        payload.append(status)
        # 방 제목 (가변 길이)
        title_bytes = room.title.encode('utf-8')
        payload.append(len(title_bytes)) # 제목 길이
        payload.extend(title_bytes)      # 제목 내용
        
        # (선택) 현재 인원 수 추가 가능 (여기선 생략)

    # 목록 전송 (CMD_REQ_SEARCH_ROOM에 대한 응답용 별도 CMD가 없으므로 동일 CMD 사용하거나 0x10 사용)
    # PPT 명세상 Server->Client의 0x10은 없으나, 목록 응답용으로 0x10을 재사용한다고 가정
    client.send_packet(Packet(CMD_REQ_SEARCH_ROOM, payload))


@router.route(CMD_REQ_ROOM_INFO)
def handle_room_info(client, packet):
    if not client.room_id: return
    room = room_manager.get_room(client.room_id)
    if not room: return
    # 1. 유저 목록 전송
    for user in room.get_users():
        slot = room.slots.index(user)
        body = struct.pack('>B', slot) + user.nickname.encode('utf-8')
        client.send_packet(Packet(CMD_NOTI_ENTER_ROOM, body))
        # 2. 레디 정보 전송 (레디한 경우만)
        if room.ready_states[slot]:
            r_body = struct.pack('>B B', slot, 1)
            client.send_packet(Packet(CMD_NOTI_READY_STATE, r_body))