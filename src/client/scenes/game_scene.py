# src/client/scenes/game_scene.py
import struct
import time
import random
from src.client.scenes.base_scene import BaseScene
from src.common.protocol import Packet
from src.common.constants import *
from src.core.game_state import GameState
from src.client.network.router import route
from src.common.utils import setup_file_logger

class GameScene(BaseScene):
    def __init__(self, manager):
        super().__init__(manager)
        self.games = {}
        self.last_tick = 0
        self.sent_gameover = False
        self.game_finished = False
        self.result_msg = ""
        self.my_final_score = 0
        self.accumulated_lines = 0       # 내가 보내려고 모으고 있는 공격 줄 수
        self.last_clear_time = 0         # 마지막으로 라인을 지운 시간 (콤보 타이머용)
        self.pending_garbage = []        # 내가 맞아서 대기 중인 공격 리스트 [{'lines': n, 'trigger_time': t}, ...]

        self.logger = setup_file_logger("GameScene")
    
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

        self.pending_garbage = {slot: [] for slot in players}
        self.accumulated_lines = 0
        self.last_clear_time = 0

    def update(self):
        current_time = time.time()
        # 1. 입력 처리
        action = self.input_handler.get_action()
        if action:
            if self.game_finished:
                if action == Action.QUIT: # 결과 창에서 Q -> 대기실
                    self.manager.change_scene("ROOM")
                    return
            else:
                if action == Action.QUIT: # 게임 중 강제 종료
                    self.logger.info("User requested QUIT during game.")
                    self.network.send_packet(Packet(CMD_REQ_LEAVE_ROOM, b''))
                    self.context.room_id = -1
                    self.manager.change_scene("LOBBY")
                    self.network.send_packet(Packet(CMD_REQ_SEARCH_ROOM, b''))
                    return
                
                if self.context.my_slot in self.games:
                    cleared = self.games[self.context.my_slot].process_input(action)
                    if cleared > 0:
                        self._handle_line_clear(cleared)
                    self.network.send_packet(Packet(CMD_REQ_MOVE, bytes([action.value])))

        if self.game_finished:
            self._draw()
            time.sleep(0.01)
            return
# 2. 0.5초 콤보 타이머 체크 (공격 전송)
        if self.accumulated_lines > 0:
            if current_time - self.last_clear_time > 0.5:
                # 콤보 종료 -> 서버로 공격 전송
                self.logger.info(f"[Attack] Sending {self.accumulated_lines} lines attack!")
                payload = struct.pack('>B', self.accumulated_lines)
                self.network.send_packet(Packet(CMD_REQ_ATTACK, payload))
                
                self.accumulated_lines = 0 # 초기화

        for slot, garbage_list in self.pending_garbage.items():
            if not garbage_list: continue
            
            if slot not in self.games: continue
            game = self.games[slot]
            if game.game_over: continue

            while garbage_list:
                attack = garbage_list[0]
                if current_time >= attack['trigger_time']:
                    lines = attack['lines']
                    game.board.add_garbage_lines(lines)
                    garbage_list.pop(0)
                    
                    if slot == self.context.my_slot:
                        self.logger.info(f"[Defense] Garbage applied: {lines} lines")
                else:
                    break

        # 4. 게임 상태 체크 (내 게임 오버)
        if not self.sent_gameover:
            my_game = self.games.get(self.context.my_slot)
            if my_game and my_game.game_over:
                self.logger.info("My Game Over detected.")
                score = my_game.score
                payload = struct.pack('>I', score)
                self.network.send_packet(Packet(CMD_REQ_GAMEOVER, payload))
                self.sent_gameover = True

        # 5. 주기적 업데이트 (중력)
        if time.time() - self.last_tick > 0.5:
            for slot, game in self.games.items():
                cleared = game.update()
                if slot == self.context.my_slot and cleared > 0:
                    self._handle_line_clear(cleared) # 중력으로 지워진 줄도 처리
            self.last_tick = time.time()

        self._draw()
        time.sleep(0.01)

    def _handle_line_clear(self, cleared):
        """라인 삭제 시 방어 및 공격 장전 로직"""
        self.logger.debug(f"[Clear] Cleared {cleared} lines")
        self.last_clear_time = time.time()
        my_slot = self.context.my_slot
        my_garbage = self.pending_garbage.get(my_slot, [])
        # 1. 방어 (Pending Garbage 상쇄)
        while cleared > 0 and my_garbage:
            attack = my_garbage[0]
            if attack['lines'] <= cleared:
                cleared -= attack['lines']
                my_garbage.pop(0)
                self.logger.info("[Defense] Blocked completely!")
            else:
                attack['lines'] -= cleared
                cleared = 0
                self.logger.info(f"[Defense] Reduced attack. Rem: {attack['lines']}")

        # 2. 공격 장전 (남은 클리어 라인)
        if cleared > 0:
            self.accumulated_lines += cleared
            self.logger.info(f"[Combo] Accumulated: {self.accumulated_lines}")

    def _draw(self):

        for slot, game in self.games.items():
            if slot in self.pending_garbage:
                total_pending = sum(a['lines'] for a in self.pending_garbage[slot])
                game.pending_garbage = total_pending
            else:
                game.pending_garbage = 0
            
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

    @route(CMD_NOTI_GARBAGE)
    def on_garbage(self, pkt):
        """서버로부터 공격 알림 받음 (Broadcast)"""
        # [수정] 3바이트 파싱 (Attacker, Target, Lines)
        attacker_slot, target_slot, lines = struct.unpack('>B B B', pkt.body)
        
        self.logger.info(f"[Net] Attack: {attacker_slot} -> {target_slot} ({lines} lines)")

        # 1. 내가 타겟인 경우: 방어(Counter) 로직 수행
        if target_slot == self.context.my_slot:
            # 크로스 카운터 (내 장전된 공격으로 상쇄)
            if self.accumulated_lines > 0:
                if self.accumulated_lines >= lines:
                    self.accumulated_lines -= lines
                    self.logger.info(f"[Counter] Blocked attack! (Rem acc: {self.accumulated_lines})")
                    lines = 0
                else:
                    lines -= self.accumulated_lines
                    self.accumulated_lines = 0
                    self.logger.info(f"[Counter] Reduced attack. (Inc: {lines})")

        # 2. 대기열 추가 (나 & 상대방 모두 해당)
        # 상대방이 공격받은 것도 시각적으로 보여주기 위해 pending에 추가함
        if lines > 0:
            trigger_time = time.time() + 2.0
            
            # 해당 슬롯의 대기열에 추가
            if target_slot in self.pending_garbage:
                self.pending_garbage[target_slot].append({
                    'lines': lines,
                    'trigger_time': trigger_time,
                    'attacker': attacker_slot
                })
                
            if target_slot == self.context.my_slot:
                self.logger.info(f"[Danger] {lines} lines incoming in 2s!")

    @route(CMD_NOTI_RESULT)
    def on_game_result(self, pkt):
        # [Modified] 승리 사유 추가 (1B)
        # 구조: [WinnerSlot(1B)] [Reason(1B)] (Reason은 선택적일 수 있음 - 하위호환)
        winner_slot = pkt.body[0]
        reason = 0
        if len(pkt.body) >= 2:
            reason = pkt.body[1]
        self.logger.info(f"Game Finished. Winner: {winner_slot}, Reason: {reason}") # [로그]
        self.game_finished = True
        
        if winner_slot == 255:
            self.result_msg = "DRAW"
        elif winner_slot == self.context.my_slot:
            if reason == 1:
                self.result_msg = "YOU WIN! (BY WALKOVER)"
            else:
                self.result_msg = "YOU WIN!"
        else:
            self.result_msg = f"WINNER: P{winner_slot + 1}"
            
        if self.context.my_slot in self.games:
            self.my_final_score = self.games[self.context.my_slot].score
            
        for g in self.games.values():
            g.game_over = True
