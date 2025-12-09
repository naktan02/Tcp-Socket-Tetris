# src/client/scene_manager.py (전체 덮어쓰기 권장)

import time
import struct
import random
from src.client.renderer import Renderer
from src.client.input_handler import InputHandler
from src.client.network_client import NetworkClient
from src.core.game_state import GameState
from src.common.constants import *
from src.common.protocol import Packet
from src.common.config import MAX_ROOM_SLOTS

class SceneManager:
    def __init__(self):
        self.renderer = Renderer()
        self.input_handler = InputHandler()
        self.network = NetworkClient()
        
        self.running = True
        self.state = "LOGIN"
        
        self.games = {}
        self.my_slot = -1
        self.room_id = -1
        
        # 로비 데이터
        self.room_list = [] # [{'id':1, 'title':'Test'}]
        
        # 대기실 데이터
        self.room_slots = [None] * MAX_ROOM_SLOTS # 닉네임 저장
        self.room_ready = [False] * MAX_ROOM_SLOTS # 준비 상태 저장
        self.PROMPT_LINE = 22

    def run(self):
        while self.running:
            if self.state == "LOGIN":
                self._scene_login()
            elif self.state == "LOBBY":
                self._scene_lobby()
            elif self.state == "ROOM":
                self._scene_room()
            elif self.state == "GAME":
                self._scene_game()
        
        self.network.disconnect()

    def _scene_login(self):
        self.renderer.clear_screen()
        print("=== TETRIS ONLINE ===")
        # 1. IP 입력 받기 (노트북에서 서버 IP 입력 가능)
        ip = input("Server IP (Default 127.0.0.1): ").strip()
        if not ip: ip = "127.0.0.1"
        
        print(f"Connecting to {ip}...")
        if not self.network.connect(ip, 5000):
            print("Connection failed. Check IP and try again.")
            time.sleep(2)
            return

        # 2. 닉네임 입력
        nick = input("Nickname: ").strip()
        if not nick: nick = "Player"
        
        self.network.login(nick)
        
        start = time.time()
        while time.time() - start < 5:
            pkt = self.network.get_packet()
            if pkt and pkt.cmd == CMD_RES_LOGIN:
                if pkt.body[0] == 0:
                    self.state = "LOBBY"
                    # 로그인 직후 방 목록 한 번 요청
                    self.network.send_packet(Packet(CMD_REQ_SEARCH_ROOM, b''))
                else:
                    print("Login failed.")
                return
            time.sleep(0.1)
        print("Login timeout.")

    def _scene_lobby(self):
        """로비: 방 목록 보여주고 선택 (수정됨: 논블로킹 입력 적용)"""
        self._refresh_lobby_ui()

        import sys
        import os
        
        # 윈도우용 입력 모듈 (없으면 무시)
        try:
            import msvcrt
        except ImportError:
            msvcrt = None

        while self.state == "LOBBY":
            # 1. 비동기 키 입력 감지 (Blocking 없이 확인만 함)
            cmd = None
            if os.name == 'nt' and msvcrt:
                if msvcrt.kbhit(): # 키가 눌려있을 때만 읽음
                    try:
                        # getch()는 바이트를 반환하므로 decode 필요
                        cmd = msvcrt.getch().decode('utf-8').upper()
                    except:
                        pass
            else:
                # 맥/리눅스용 (select 모듈 사용)
                import select
                if select.select([sys.stdin], [], [], 0.0)[0]:
                    cmd = sys.stdin.read(1).upper()

            # 2. 입력에 따른 처리
            if cmd:
                self.renderer.clear_line(self.PROMPT_LINE)
                self.renderer.move_cursor(1, self.PROMPT_LINE)
                
                if cmd == 'C':
                    print("[Create] Enter Room Title: ", end='', flush=True)
                    # 여기선 타이핑을 위해 잠시 멈춰도 됨 (Blocking Input)
                    self.renderer.show_cursor()
                    title = sys.stdin.readline().strip() 
                    self.renderer.hide_cursor()
                    if title:
                        self.network.send_packet(Packet(CMD_REQ_CREATE_ROOM, title))
                    else:
                        self._refresh_lobby_ui()

                elif cmd == 'J':
                    print("[Join] Enter Room ID: ", end='', flush=True)
                    self.renderer.show_cursor()
                    rid = sys.stdin.readline().strip()
                    self.renderer.hide_cursor()
                    if rid.isdigit():
                        payload = struct.pack('>H', int(rid))
                        self.network.send_packet(Packet(CMD_REQ_JOIN_ROOM, payload))
                    else:
                        self._refresh_lobby_ui()

                elif cmd == 'R':
                    print("[Refresh] Updating list...", end='', flush=True)
                    self.network.send_packet(Packet(CMD_REQ_SEARCH_ROOM, b''))
                    # 잠시 후 UI 갱신은 패킷 수신부에서 처리되거나, 여기서 잠시 대기
                    time.sleep(0.2)
                    self._refresh_lobby_ui()
                    
                elif cmd == 'Q':
                    self.running = False
                    return
                else:
                    self._refresh_lobby_ui()

            # 3. 네트워크 패킷 처리 (지속적으로 수신)
            while True:
                pkt = self.network.get_packet()
                if not pkt: break
                
                if pkt.cmd == CMD_REQ_SEARCH_ROOM:
                    # 방 목록 갱신
                    count = pkt.body[0]
                    self.room_list = []
                    offset = 1
                    for _ in range(count):
                        if offset + 2 > len(pkt.body): break
                        rid = struct.unpack('>H', pkt.body[offset:offset+2])[0]
                        offset += 2
                        
                        tlen = pkt.body[offset]
                        offset += 1
                        
                        title = pkt.body[offset:offset+tlen].decode('utf-8')
                        offset += tlen
                        self.room_list.append({'id': rid, 'title': title})
                    
                    # 목록을 받으면 화면을 새로고침
                    self._refresh_lobby_ui()

                elif pkt.cmd == CMD_RES_CREATE_ROOM:
                    res, self.room_id = struct.unpack('>B H', pkt.body)
                    if res == 0:
                        self.state = "ROOM"
                        self.my_slot = 0
                        self._init_room_data() # 데이터 초기화
                        self.room_slots[0] = "ME"
                        return

                elif pkt.cmd == CMD_RES_JOIN_ROOM:
                    res, self.my_slot = struct.unpack('>B B', pkt.body)
                    if res == 0:
                        self.state = "ROOM"
                        self._init_room_data()
                        self.room_slots[self.my_slot] = "ME"
                        return
                    else:
                        print(f"\nJoin Failed (Error {res})")
                        time.sleep(1)
                        self._refresh_lobby_ui()

            time.sleep(0.05) # CPU 점유율 낮춤

    def _refresh_lobby_ui(self):
        """로비 화면 및 하단 메뉴 다시 그리기"""
        self.renderer.draw_lobby(self.room_list)
        # 하단 프롬프트 위치를 상수로 통일 (Line 19)
        self.renderer.clear_line(self.PROMPT_LINE)
        self.renderer.move_cursor(1, self.PROMPT_LINE)
        print("Command [C:Create, J:Join, R:Refresh, Q:Quit]: ", end='', flush=True)

    def _init_room_data(self):
        """방 진입 전 데이터 초기화"""
        self.room_slots = [None] * MAX_ROOM_SLOTS 
        self.room_ready = [False] * MAX_ROOM_SLOTS
        
    def _scene_room(self):
        """대기실: Ready 상태 표시"""
        self.renderer.clear_screen()
        while self.state == "ROOM":
            self.renderer.draw_room_wait(self.room_id, self.room_slots, self.room_ready, self.my_slot)
            
            action = self.input_handler.get_action()
            if action == Action.DROP: # Spacebar
                self.network.send_packet(Packet(CMD_REQ_TOGGLE_READY, b''))
            elif action == Action.QUIT: # Q
                self.network.send_packet(Packet(CMD_REQ_LEAVE_ROOM, b''))
                self.state = "LOBBY"
                self.network.send_packet(Packet(CMD_REQ_SEARCH_ROOM, b'')) # 목록 갱신 요청
                return

            # 패킷 처리
            while True:
                pkt = self.network.get_packet()
                if not pkt: break
                
                if pkt.cmd == CMD_NOTI_ENTER_ROOM:
                    # [SlotID] [NickName]
                    slot = pkt.body[0]
                    nick = pkt.body[1:].decode('utf-8')
                    if slot < 2:
                        self.room_slots[slot] = nick
                        self.room_ready[slot] = False
                
                elif pkt.cmd == CMD_NOTI_LEAVE_ROOM:
                    slot = pkt.body[0]
                    if slot < 2:
                        self.room_slots[slot] = None
                        self.room_ready[slot] = False

                elif pkt.cmd == CMD_NOTI_READY_STATE:
                    slot, state = struct.unpack('>B B', pkt.body)
                    if slot < 2:
                        self.room_ready[slot] = bool(state)

                elif pkt.cmd == CMD_NOTI_GAME_START:
                    seed = struct.unpack('>I', pkt.body)[0]
                    # 게임 참가자 슬롯 확인
                    players = [i for i, u in enumerate(self.room_slots) if u is not None]
                    self._init_game(seed, players)
                    self.state = "GAME"
                    return

            time.sleep(0.1)

    def _init_game(self, seed, player_slots):
        """게임 초기화: 모든 플레이어의 GameState 생성"""
        random.seed(seed)
        self.games = {}
        
        # 시드 동기화를 위해 루프마다 시드 재설정
        for slot in player_slots:
            random.seed(seed) 
            self.games[slot] = GameState()

    def _scene_game(self):
        """인게임 루프"""
        self.renderer.clear_screen()
        last_tick = time.time()
        
        while self.state == "GAME":
            # 1. 내 입력 처리
            action = self.input_handler.get_action()
            if action:
                if action == Action.QUIT:
                    self.running = False
                    return
                
                # 내 게임 조작 및 서버 전송
                if self.my_slot in self.games:
                    self.games[self.my_slot].process_input(action)
                    # 키보드 입력을 서버로 전송
                    self.network.send_packet(Packet(CMD_REQ_MOVE, bytes([action.value])))

            # 2. 서버 패킷 처리 (상대방 움직임)
            while True:
                pkt = self.network.get_packet()
                if not pkt: break
                
                if pkt.cmd == CMD_NOTI_MOVE:
                    # [SlotID] [KeyCode]
                    slot, keycode = struct.unpack('>B B', pkt.body)
                    
                    # 내가 아닌 다른 사람의 움직임 반영
                    if slot != self.my_slot and slot in self.games:
                        try:
                            peer_action = Action(keycode)
                            self.games[slot].process_input(peer_action)
                        except ValueError:
                            pass
                
                # 게임 오버 등 추가 패킷 처리 가능

            # 3. 주기적 업데이트 (중력)
            if time.time() - last_tick > 0.5:
                for game in self.games.values():
                    game.update()
                last_tick = time.time()

            # 4. 화면 그리기
            self.renderer.draw_battle(self.my_slot, self.games)
            time.sleep(0.01)