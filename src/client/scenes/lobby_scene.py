# src/client/scenes/lobby_scene.py
import sys
import os
import struct
import time
from src.client.scenes.base_scene import BaseScene
from src.common.protocol import Packet
from src.common.constants import *
from src.client.router import route

# Windows msvcrt import
try:
    import msvcrt
except ImportError:
    msvcrt = None

class LobbyScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.room_list = []
        self.PROMPT_LINE = 20

    def on_enter(self):
        self._refresh_ui()

    def update(self):
        # 1. 입력 처리 (Non-blocking)
        cmd = self._get_input()
        if cmd:
            self._handle_input(cmd)

    def _get_input(self):
        # 기존 _scene_lobby의 입력 로직
        cmd = None
        if os.name == 'nt' and msvcrt:
            if msvcrt.kbhit():
                try:
                    cmd = msvcrt.getch().decode('utf-8').upper()
                except: pass
        else:
            import select
            if select.select([sys.stdin], [], [], 0.0)[0]:
                cmd = sys.stdin.read(1).upper()
        return cmd

    def _handle_input(self, cmd):
        self.renderer.clear_line(self.PROMPT_LINE)
        self.renderer.move_cursor(1, self.PROMPT_LINE)

        if cmd == 'C':
            print("[Create] Enter Room Title: ", end='', flush=True)
            self.renderer.show_cursor()
            title = sys.stdin.readline().strip()
            self.renderer.hide_cursor()
            if title:
                self.network.send_packet(Packet(CMD_REQ_CREATE_ROOM, title))
            else:
                self._refresh_ui()

        elif cmd == 'J':
            print("[Join] Enter Room ID: ", end='', flush=True)
            self.renderer.show_cursor()
            rid = sys.stdin.readline().strip()
            self.renderer.hide_cursor()
            if rid.isdigit():
                payload = struct.pack('>H', int(rid))
                self.network.send_packet(Packet(CMD_REQ_JOIN_ROOM, payload))
            else:
                self._refresh_ui()

        elif cmd == 'R':
            print("[Refresh] Updating list...", end='', flush=True)
            self.network.send_packet(Packet(CMD_REQ_SEARCH_ROOM, b''))

        elif cmd == 'Q':
            self.manager.running = False

        else:
            self._refresh_ui()

    @route(CMD_REQ_SEARCH_ROOM)
    def on_room_list_update(self, pkt):
        """방 목록 갱신 패킷 처리 (서버가 REQ CMD를 그대로 응답으로 사용 중)"""
        count = pkt.body[0]
        self.room_list = []
        offset = 1
        for _ in range(count):
            if offset + 2 > len(pkt.body): break
            rid = struct.unpack('>H', pkt.body[offset:offset+2])[0]
            offset += 2
            
            status = pkt.body[offset]
            offset += 1
            
            tlen = pkt.body[offset]
            offset += 1
            
            title = pkt.body[offset:offset+tlen].decode('utf-8')
            offset += tlen
            self.room_list.append({'id': rid, 'title': title, 'status': status})
        
        self._refresh_ui()

    @route(CMD_RES_CREATE_ROOM)
    def on_create_room_response(self, pkt):
        res, room_id = struct.unpack('>B H', pkt.body)
        if res == 0:
            self.manager.room_id = room_id
            self.manager.my_slot = 0 # 방장은 0번
            self.manager.change_scene("ROOM")

    @route(CMD_RES_JOIN_ROOM)
    def on_join_room_response(self, pkt):
        res, my_slot = struct.unpack('>B B', pkt.body)
        if res == 0:
            self.manager.my_slot = my_slot
            # 입장 성공 시 즉시 ROOM_INFO 요청
            self.network.send_packet(Packet(CMD_REQ_ROOM_INFO, b''))
            self.manager.change_scene("ROOM")
        else:
            print(f"\nJoin Failed (Error {res})")
            time.sleep(1)
            self._refresh_ui()

    def _refresh_ui(self):
        self.renderer.draw_lobby(self.room_list)
        self.renderer.clear_line(self.PROMPT_LINE)
        self.renderer.move_cursor(1, self.PROMPT_LINE)
