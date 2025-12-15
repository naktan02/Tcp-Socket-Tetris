# src/server/room.py
import struct
from src.common.protocol import Packet
from src.common.constants import CMD_NOTI_LEAVE_ROOM, CMD_NOTI_ENTER_ROOM
from src.server.infra.client_peer import ClientPeer
from src.server.game.game_session import GameSession
from src.common.config import MAX_ROOM_SLOTS

class Room:
    def __init__(self, room_id: int, title: str):
        self.room_id = room_id
        self.title = title
        self.max_slots = MAX_ROOM_SLOTS
        self.slots = [None] * self.max_slots
        self.ready_states = [False] * self.max_slots
        
        # 게임 세션 객체 (게임 중일 때만 존재)
        self.game_session = None

    @property
    def is_playing(self):
        """현재 게임 진행 중인지 여부"""
        return self.game_session is not None and self.game_session.is_active

    def enter_user(self, client: ClientPeer):
        """유저 입장"""
        for i in range(self.max_slots):
            if self.slots[i] is None:
                self.slots[i] = client
                self.ready_states[i] = False
                return i
        return -1

    def leave_user(self, client: ClientPeer):
        """유저 퇴장 처리 및 방장 이양 로직"""
        slot_id = -1
        
        # 1. 나가는 유저 슬롯 찾기
        for i in range(self.max_slots):
            if self.slots[i] == client:
                slot_id = i
                break
        
        if slot_id != -1:
            self.slots[slot_id] = None
            self.ready_states[slot_id] = False

            if self.is_playing:
                self.handle_player_death(slot_id, score=0)
            
            # 방장(0번)이 나갔을 때 방장 이양 (Host Migration)
            if slot_id == 0:
                if self.is_playing:
                    # 게임 중이면 즉시 이양하지 않고, 게임 끝난 후 처리 (return slot_id -> Handler에서 LEAVE 전송)
                    return slot_id
                else:
                    # 대기 중이면 즉시 이양
                    # 우선 방장이 나갔음을 모두에게 알림
                    leave_pkt = Packet(CMD_NOTI_LEAVE_ROOM, struct.pack('>B', 0))
                    self.broadcast(leave_pkt)

                    self._attempt_host_migration()

                    return -1

        return slot_id

    def _attempt_host_migration(self):
        """방장 이양 로직 (0번 슬롯이 비었을 때 호출)"""
        new_host_idx = -1
        for i in range(1, self.max_slots):
            if self.slots[i] is not None:
                new_host_idx = i
                break
        
        if new_host_idx != -1:
            new_host_client = self.slots[new_host_idx]
            self.slots[0] = new_host_client
            self.slots[new_host_idx] = None
            self.ready_states[0] = False
            
            self.broadcast(Packet(CMD_NOTI_LEAVE_ROOM, struct.pack('>B', new_host_idx)))
            
            nick_bytes = new_host_client.nickname.encode('utf-8')
            enter_body = struct.pack('>B', 0) + nick_bytes
            self.broadcast(Packet(CMD_NOTI_ENTER_ROOM, enter_body))
            
            print(f"[Room #{self.room_id}] Host migrated to {new_host_client.nickname}")



    def get_users(self):
        return [u for u in self.slots if u is not None]

    def broadcast(self, packet, exclude_client=None):
        for user in self.get_users():
            if user != exclude_client:
                user.send_packet(packet)

    def is_empty(self):
        return all(s is None for s in self.slots)

    def toggle_ready(self, slot_id):
        if 0 <= slot_id < self.max_slots:
            self.ready_states[slot_id] = not self.ready_states[slot_id]
            return self.ready_states[slot_id]
        return False

    def can_start_game(self):
        """게임 시작 조건 검사"""
        if self.is_playing: return False
        
        users = self.get_users()
        if len(users) < 2: return False # 최소 2명
        
        # 방장(0번) 외 모두 Ready 상태여야 함
        for i in range(1, self.max_slots):
            if self.slots[i] is not None and not self.ready_states[i]:
                return False
        return True

    def start_game(self):
        """게임 세션 생성 및 시작"""
        if not self.can_start_game(): return

        # 세션 생성 후 시작
        self.game_session = GameSession(self)
        self.game_session.start()

    def handle_player_death(self, slot_id, score):
        """핸들러에서 오는 사망 요청을 세션으로 위임"""
        if self.game_session:
            self.game_session.handle_death(slot_id, score)

    def on_game_end(self):
        """게임이 끝났을 때 세션에서 호출하는 콜백"""
        self.game_session = None
        # 모든 유저 레디 해제
        # 모든 유저 레디 해제
        for i in range(self.max_slots):
            self.ready_states[i] = False
            
        # 게임 도중 방장이 나가서 0번이 비어있다면, 이제 이양 시도
        if self.slots[0] is None:
            self._attempt_host_migration()