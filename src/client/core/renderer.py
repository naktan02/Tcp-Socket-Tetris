# src/client/renderer.py
import sys
from src.common.constants import *
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
        
        # [핵심] 이전 프레임 화면 버퍼
        self.prev_lines = []

    def __del__(self):
        Console.cleanup()

    def clear_screen(self):
        """강제 초기화가 필요할 때 사용 (씬 전환 등)"""
        Console.clear()
        self.prev_lines = []

    def render_diff(self, new_lines):
        """
        [Diff Algorithm]
        이전 프레임(self.prev_lines)과 새 프레임(new_lines)을 비교하여
        변경된 줄만 커서를 이동해 덮어씁니다.
        """
        # 1. 화면 크기가 달라졌거나 첫 렌더링이면 전체 다시 그리기
        if len(self.prev_lines) != len(new_lines):
            Console.clear()
            Console.print_lines(new_lines)
            self.prev_lines = list(new_lines)
            return

        # 2. 줄 단위 비교
        for i, (old_line, new_line) in enumerate(zip(self.prev_lines, new_lines)):
            if old_line != new_line:
                # 변경된 줄 위치로 이동 (터미널은 1부터 시작하므로 i+1)
                Console.move_cursor(1, i + 1)
                sys.stdout.write(new_line)
                
                # 새 줄이 더 짧으면 뒤에 남은 잔상을 지움
                if len(new_line) < len(old_line):
                    sys.stdout.write("\033[K") # ANSI: Clear to end of line

        sys.stdout.flush()
        
        # 3. 현재 화면을 버퍼에 저장
        self.prev_lines = list(new_lines)

    def move_cursor(self, x, y):
        Console.move_cursor(x, y)
        
    def clear_line(self, y):
        Console.clear_line(y)
    
    def hide_cursor(self):
        Console.hide_cursor()
        
    def show_cursor(self):
        Console.show_cursor()

    # --- 각 화면 그리기 (이제 render_diff를 사용합니다) ---

    def draw_lobby(self, room_list, server_ip=""):  
        lines = self.lobby_view.draw(room_list, server_ip)
        self.render_diff(lines)

    def draw_room_wait(self, room_id, slots, ready_states, my_slot):
        lines = self.room_view.draw(room_id, slots, ready_states, my_slot)
        self.render_diff(lines)

    def draw_battle(self, local_slot_id, games, result_msg=None, final_score=0):
        """
        게임 화면 그리기 (Diff + Overlay)
        """
        # 1. 기본 게임 화면 라인 생성
        lines = self.game_view.draw(local_slot_id, games)
        
        # 2. 바탕 화면 Diff 렌더링 (여기서 깜빡임 제거됨)
        self.render_diff(lines)

        # 3. 결과 오버레이가 있다면 Diff 위에 '강제 덧칠' (Z-index 개념)
        if result_msg:
            overlay_lines = self.game_view.create_result_box(result_msg, final_score)
            
            # 오버레이 위치 잡기 (화면 중앙 즈음)
            start_y = 9 
            start_x = 30
            
            for i, line in enumerate(overlay_lines):
                # 해당 위치로 커서 이동 후 라인 덮어쓰기
                Console.move_cursor(start_x, start_y + i)
                sys.stdout.write(line)
            
            sys.stdout.flush()

    def draw_message(self, msg):
        Console.move_cursor(20, 10) # 위치 조정
        sys.stdout.write(f"{COLOR_MAGENTA} {msg} {COLOR_RESET}")
        sys.stdout.flush()

    def draw_result_overlay(self, result_msg, score):
        """게임 결과 화면을 중앙에 덮어씀 (draw_battle 내에서도 처리되지만 호환성 위해 유지)"""
        start_x = 25 # 대략 중앙
        start_y = 8
        
        overlay_lines = self.game_view.create_result_box(result_msg, score)
        
        for i, line in enumerate(overlay_lines):
            self.move_cursor(start_x, start_y + i)
            sys.stdout.write(line)
        
        sys.stdout.flush()