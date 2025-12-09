# src/server/room.py (수정)
import struct
import random
from src.server.client_peer import ClientPeer
from src.common.protocol import Packet
from src.common.constants import *
from src.common.config import MAX_ROOM_SLOTS

class Room:
    def __init__(self, room_id: int, title: str):
        self.room_id = room_id
        self.title = title
        self.max_slots = MAX_ROOM_SLOTS
        self.slots = [None] * self.max_slots
        self.is_playing = False
        
        # [NEW] 슬롯별 준비 상태 (True/False)
        self.ready_states = [False] * self.max_slots

    def enter_user(self, client: ClientPeer):
        for i in range(self.max_slots):
            if self.slots[i] is None:
                self.slots[i] = client
                self.ready_states[i] = False # 입장 시 준비 해제
                return i
        return -1

    def leave_user(self, client: ClientPeer):
        for i in range(self.max_slots):
            if self.slots[i] == client:
                self.slots[i] = None
                self.ready_states[i] = False # 퇴장 시 준비 해제
                return i
        return -1

    def get_users(self):
        return [u for u in self.slots if u is not None]

    def broadcast(self, packet, exclude_client=None):
        for user in self.get_users():
            if user != exclude_client:
                user.send_packet(packet)

    def is_empty(self):
        return all(s is None for s in self.slots)

    # --- [NEW] 게임 진행 관련 메서드 추가 ---

    def toggle_ready(self, slot_id):
        """특정 슬롯의 준비 상태를 토글하고 변경된 상태 반환"""
        if 0 <= slot_id < self.max_slots:
            self.ready_states[slot_id] = not self.ready_states[slot_id]
            return self.ready_states[slot_id]
        return False

    def can_start_game(self):
        """
        게임 시작 조건 검사:
        1. 혼자가 아니어야 함 (최소 2명)
        2. 방장(Slot 0)을 제외한 모든 참가자가 Ready 상태여야 함
        """
        users = self.get_users()
        if len(users) < 2: 
            return False # 혼자서는 시작 불가
        
        # Slot 1부터 끝까지 확인
        for i in range(1, self.max_slots):
            # 유저가 있는데 Ready가 안 되어 있다면 시작 불가
            if self.slots[i] is not None and not self.ready_states[i]:
                return False
        
        return True

    def start_game(self):
        """게임 시작 처리: 시드 생성 및 브로드캐스트"""
        self.is_playing = True
        
        # 1. 랜덤 시드 생성 (4바이트 정수)
        seed = random.randint(0, 0xFFFFFFFF)
        
        # 2. 모든 유저에게 NOTI_GAME_START 전송
        # 구조: [RandomSeed(4B)]
        print(f"[Room #{self.room_id}] Game Start! Seed: {seed}")
        payload = struct.pack('>I', seed)
        packet = Packet(CMD_NOTI_GAME_START, payload)
        self.broadcast(packet)