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
            active_users = [u for u in self.room.slots if u is not None]
            active_users_count = len(active_users)
            
            winner_slot = -1
            should_end = False

            # 생존자가 아무도 없으면 (모두 사망)
            if len(self.alive_slots) == 0:
                should_end = True
                winner_slot = self._get_highest_score_slot()
                print(f"[Room #{self.room.room_id}] All players dead. Winner: {winner_slot}")
            # 접속자가 1명뿐이고, 그 사람이 아직 살아있다면 -> 즉시 승리 (기권승)
            elif active_users_count == 1:
                last_user = active_users[0]
                # last_user 객체가 어느 슬롯인지 찾음
                try:
                    last_user_slot = self.room.slots.index(last_user)
                    # 그 유저가 살아있는 상태라면 승리
                    if last_user_slot in self.alive_slots:
                        should_end = True
                        winner_slot = last_user_slot
                        # [Modified] 승리 사유 추가 (1=기권승/Walkover)
                        self.finish_game(winner_slot, reason=1)
                        print(f"[Room #{self.room.room_id}] Auto-Win: Slot {winner_slot} is the last survivor.")
                        return # finish_game에서 처리하므로 여기서 리턴
                except ValueError:
                    pass # 혹시 모를 에러 방지       
            # (예외 처리) 방에 접속자가 아무도 없게 된 경우 강제 종료
            if active_users_count == 0:
                should_end = True
                winner_slot = -1
                self.finish_game(winner_slot, reason=0)
                return

            if should_end:
                self.finish_game(winner_slot, reason=0)

    def _get_highest_score_slot(self):
        """기록된 점수 중 최고점 슬롯 반환"""
        if not self.final_scores: return -1
        # 점수(value)가 가장 큰 키(slot)를 찾음
        max_score = max(self.final_scores.values())

        winners = [slot for slot, score in self.final_scores.items() if score == max_score]
        if len(winners) > 1:
            return -1
        return winners[0]
        
    def finish_game(self, winner_slot, reason=0):
        """
        게임 종료 처리
        reason: 0=Normal, 1=Walkover(Last Survivor)
        """
        if not self.is_active: return
        self.is_active = False
        
        print(f"[Room #{self.room.room_id}] Game Finished. Winner: Slot {winner_slot}, Reason: {reason}")
        
        # 결과 전송: [WinnerSlot(1B)] [Reason(1B)]
        # (WinnerSlot: 255 = 무승부/없음)
        w = winner_slot if winner_slot != -1 else 255
        payload = struct.pack('>B B', w, reason)
        self.room.broadcast(Packet(CMD_NOTI_RESULT, payload))
        
        # Room에 게임 종료 알림 (상태 정리)
        self.room.on_game_end()