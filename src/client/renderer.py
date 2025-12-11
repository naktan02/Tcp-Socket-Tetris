# src/client/renderer.py
import sys
from src.common.constants import *
# 새로 만든 모듈들 임포트
from src.client.ui.console import Console
from src.client.ui.lobby_view import LobbyView
from src.client.ui.room_view import RoomView
from src.client.ui.game_view import GameView

class Renderer:
    def __init__(self):
        # Console 초기화
        Console.init()
        
        # 하위 뷰 인스턴스 생성
        self.lobby_view = LobbyView()
        self.room_view = RoomView()
        self.game_view = GameView()

    def __del__(self):
        Console.cleanup()

    def clear_screen(self):
        Console.clear()

    def move_cursor(self, x, y):
        Console.move_cursor(x, y)
        
    def clear_line(self, y):
        Console.clear_line(y)
    
    def hide_cursor(self):
        Console.hide_cursor()
        
    def show_cursor(self):
        Console.show_cursor()

    # --- 각 화면 그리기 요청을 하위 뷰에 위임 ---

    def draw_lobby(self, room_list):
        Console.clear()
        lines = self.lobby_view.draw(room_list)
        Console.print_lines(lines)

    def draw_room_wait(self, room_id, slots, ready_states, my_slot):
        Console.home()
        lines = self.room_view.draw(room_id, slots, ready_states, my_slot)
        Console.print_lines(lines)

    def draw_battle(self, local_slot_id, games, result_msg=None, final_score=0):
        """
        게임 화면 그리기
        """
        # 1. 화면 데이터 생성 (GameView 위임)
        lines = self.game_view.draw(local_slot_id, games)
        
        # 2. 출력 문자열 조립
        full_output = "\033[H" 
        full_output += "\n".join(lines)
        
        # 3. 결과 오버레이가 있다면 중앙에 덮어쓰기 (ANSI 코드 활용)
        if result_msg:
            overlay_lines = self.game_view.create_result_box(result_msg, final_score)
            
            # 오버레이 위치 잡기 (화면 중앙 즈음)
            start_y = 9 
            start_x = 30
            
            overlay_str = ""
            for i, line in enumerate(overlay_lines):
                # 해당 위치로 커서 이동 후 라인 출력
                overlay_str += f"\033[{start_y + i};{start_x}H{line}"
            
            full_output += overlay_str
            
        # 4. 최종 출력
        sys.stdout.write(full_output)
        sys.stdout.flush()

    def draw_message(self, msg):
        Console.move_cursor(20, 10) # 위치 조정
        sys.stdout.write(f"{COLOR_MAGENTA} {msg} {COLOR_RESET}")
        sys.stdout.flush()

    def draw_result_overlay(self, result_msg, score):
        """게임 결과 화면을 중앙에 덮어씀 (GameView에 생성 위임)"""
        start_x = 25 # 대략 중앙
        start_y = 8
        
        # [수정] 박스 내용은 GameView에서 받아옴
        overlay_lines = self.game_view.create_result_box(result_msg, score)
        
        # 받아온 줄들을 화면 중앙 위치에 출력
        for i, line in enumerate(overlay_lines):
            self.move_cursor(start_x, start_y + i)
            sys.stdout.write(line)
        
        sys.stdout.flush()