# src/client/scenes/game_scene.py
import struct
import time
import random
from src.client.scenes.base_scene import BaseScene
from src.common.protocol import Packet
from src.common.constants import *
from src.core.game_state import GameState
from src.client.network.router import route

class GameScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.games = {}
        self.last_tick = 0
        self.sent_gameover = False
        self.game_finished = False
        self.result_msg = ""
        self.my_final_score = 0

    def on_enter(self):
        # 데이터 초기화
        self.games = {}
        seed = self.context.game_seed
        players = self.context.game_players
        
        # State 생성
        for slot in players:
            random.seed(seed)
            self.games[slot] = GameState()
            
        self.last_tick = time.time()
        self.sent_gameover = False
        self.game_finished = False
        self.result_msg = ""
        self.renderer.clear_screen()

    def update(self):
        # 1. 입력 처리
        action = self.input_handler.get_action()
        if action:
            if self.game_finished:
                if action == Action.QUIT: # 결과 창에서 Q -> 대기실
                    self.manager.change_scene("ROOM")
                    return
            else:
                if action == Action.QUIT: # 게임 중 강제 종료
                    self.network.send_packet(Packet(CMD_REQ_LEAVE_ROOM, b''))
                    self.context.room_id = -1
                    self.manager.change_scene("LOBBY")
                    self.network.send_packet(Packet(CMD_REQ_SEARCH_ROOM, b''))
                    return
                
                if self.context.my_slot in self.games:
                    self.games[self.context.my_slot].process_input(action)
                    self.network.send_packet(Packet(CMD_REQ_MOVE, bytes([action.value])))

        # 2. 게임 상태 체크
        if not self.game_finished and not self.sent_gameover:
            my_game = self.games.get(self.context.my_slot)
            if my_game and my_game.game_over:
                score = my_game.score
                payload = struct.pack('>I', score)
                self.network.send_packet(Packet(CMD_REQ_GAMEOVER, payload))
                self.sent_gameover = True

        # 3. 업데이트 (0.5초 간격)
        if not self.game_finished and time.time() - self.last_tick > 0.5:
            for game in self.games.values():
                game.update()
            self.last_tick = time.time()

        self._draw() # 렌더링 호출
        time.sleep(0.01)

    def _draw(self):
        self.renderer.draw_battle(
            self.context.my_slot, 
            self.games, 
            self.result_msg if self.game_finished else None, 
            self.my_final_score if self.game_finished else 0
        )

    @route(CMD_NOTI_MOVE)
    def on_peer_move(self, pkt):
        slot, keycode = struct.unpack('>B B', pkt.body)
        # 내 슬롯이 아니고, 해당 슬롯에 게임 상태가 존재할 때만 처리
        if slot != self.context.my_slot and slot in self.games:
            try:
                self.games[slot].process_input(Action(keycode))
            except:
                pass
    
    @route(CMD_NOTI_RESULT)
    def on_game_result(self, pkt):
        winner_slot = pkt.body[0]
        self.game_finished = True
        
        if winner_slot == 255:
            self.result_msg = "DRAW"
        elif winner_slot == self.context.my_slot:
            self.result_msg = "WINNER"
        else:
            self.result_msg = "LOSER"
            
        if self.context.my_slot in self.games:
            self.my_final_score = self.games[self.context.my_slot].score
            
        for g in self.games.values():
            g.game_over = True
