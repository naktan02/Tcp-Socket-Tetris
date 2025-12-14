# src/server/game_session.py
import random
import struct
from src.common.protocol import Packet
from src.common.constants import *

class GameSession:
    def __init__(self, room):
        self.room = room  # 패킷 전송을 위해 Room 참조
        self.alive_slots = set()
        self.final_scores = {}
        self.is_active = True
        
        # 게임 시작 시 현재 방에 있는 유저들로 생존자 목록 초기화
        for i, user in enumerate(self.room.slots):
            if user:
                self.alive_slots.add(i)
                
    def start(self):
        """게임 시작: 시드 생성 및 브로드캐스트"""
        seed = random.randint(0, 0xFFFFFFFF)
        print(f"[Room #{self.room.room_id}] Game Start! Seed: {seed}")
        
        payload = struct.pack('>I', seed)
        self.room.broadcast(Packet(CMD_NOTI_GAME_START, payload))

    def handle_death(self, slot_id, score):
        """플레이어 사망 처리 및 승자 판정 로직"""
        if not self.is_active:
            return

        if slot_id in self.alive_slots:
            self.alive_slots.remove(slot_id)
            self.final_scores[slot_id] = score
            
            print(f"[Room #{self.room.room_id}] Slot {slot_id} Died. Score: {score}. Survivors: {self.alive_slots}")
            
            # 현재 접속 중인 유저 수 (나간 유저 제외)
            active_users_count = len([u for u in self.room.slots if u is not None])
            
            winner_slot = -1
            should_end = False

            # 생존자가 아무도 없으면 (모두 사망)
            if len(self.alive_slots) == 0:
                should_end = True
                winner_slot = self._get_highest_score_slot()
            
            # (예외 처리) 방에 접속자가 아무도 없게 된 경우 강제 종료
            active_users_count = len([u for u in self.room.slots if u is not None])
            if active_users_count == 0:
                should_end = True
                winner_slot = -1

            if should_end:
                self.finish_game(winner_slot)

    def _get_highest_score_slot(self):
        """기록된 점수 중 최고점 슬롯 반환"""
        if not self.final_scores: return -1
        # 점수(value)가 가장 큰 키(slot)를 찾음
        return max(self.final_scores, key=self.final_scores.get)

    def finish_game(self, winner_slot):
        """게임 종료 처리"""
        if not self.is_active: return
        self.is_active = False
        
        print(f"[Room #{self.room.room_id}] Game Finished. Winner: Slot {winner_slot}")
        
        # 결과 전송: [WinnerSlot(1B)] (255 = 무승부/없음)
        w = winner_slot if winner_slot != -1 else 255
        payload = struct.pack('>B', w)
        self.room.broadcast(Packet(CMD_NOTI_RESULT, payload))
        
        # Room에 게임 종료 알림 (상태 정리)
        self.room.on_game_end()