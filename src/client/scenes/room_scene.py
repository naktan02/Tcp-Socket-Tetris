# src/client/scenes/room_scene.py
import struct
import time
from src.client.scenes.base_scene import BaseScene
from src.common.protocol import Packet
from src.common.constants import *
from src.common.config import MAX_ROOM_SLOTS
from src.client.router import route

class RoomScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        # 데이터는 Manager에 저장하는 게 좋을까, 아니면 Scene에?
        # RoomScene이 파괴되면 데이터도 사라짐 -> 상관 없음 (어차피 서버 동기화)
        self.room_slots = [None] * MAX_ROOM_SLOTS 
        self.room_ready = [False] * MAX_ROOM_SLOTS

    def on_enter(self):
        # [핵심] 들어올 때마다 최신 정보 요청
        self.network.send_packet(Packet(CMD_REQ_ROOM_INFO, b''))
        
        # 화면 초기화
        self.renderer.clear_screen()
        self._draw()

    def update(self):
        action = self.input_handler.get_action()
        if action == Action.DROP: # Spacebar -> Ready
            self.network.send_packet(Packet(CMD_REQ_TOGGLE_READY, b''))
        elif action == Action.QUIT: # Q -> Leave
            self.network.send_packet(Packet(CMD_REQ_LEAVE_ROOM, b''))
            self.manager.room_id = -1
            self.manager.my_slot = -1
            self.manager.change_scene("LOBBY")
            # 로비 목록 갱신 요청
            self.network.send_packet(Packet(CMD_REQ_SEARCH_ROOM, b''))

        time.sleep(0.05)
        self._draw()

    @route(CMD_NOTI_ENTER_ROOM)
    def on_user_enter(self, pkt):
        slot = pkt.body[0]
        nick = pkt.body[1:].decode('utf-8')
        if slot < MAX_ROOM_SLOTS:
            self.room_slots[slot] = nick
            self.room_ready[slot] = False

    @route(CMD_NOTI_LEAVE_ROOM)
    def on_user_leave(self, pkt):
        slot = pkt.body[0]
        if slot < MAX_ROOM_SLOTS:
            self.room_slots[slot] = None
            self.room_ready[slot] = False

    @route(CMD_NOTI_READY_STATE)
    def on_ready_change(self, pkt):
        slot, state = struct.unpack('>B B', pkt.body)
        if slot < MAX_ROOM_SLOTS:
            self.room_ready[slot] = bool(state)

    @route(CMD_NOTI_GAME_START)
    def on_game_start(self, pkt):
        seed = struct.unpack('>I', pkt.body)[0]
        players = [i for i, u in enumerate(self.room_slots) if u is not None]
        
        self.manager.game_seed = seed
        self.manager.game_players = players
        self.manager.change_scene("GAME")

    def _draw(self):
        # 매니저에 저장된 내 슬롯 번호 사용
        self.renderer.draw_room_wait(self.manager.room_id, self.room_slots, self.room_ready, self.manager.my_slot)
