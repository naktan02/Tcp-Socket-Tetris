# src/client/renderer.py
import sys
import os
from src.common.constants import *
from src.common.config import MAX_ROOM_SLOTS

class Renderer:
    def __init__(self):
        self.width = 10
        self.height = 20
        self.cols = 2  # 화면 분할 개수 (2인용)
        
        # [Alternate Screen Buffer]
        sys.stdout.write("\033[?1049h")
        self.hide_cursor()
        self.clear_screen()

    def __del__(self):
        sys.stdout.write("\033[?1049l")
        self.show_cursor()

    def hide_cursor(self):
        sys.stdout.write("\033[?25l")

    def show_cursor(self):
        sys.stdout.write("\033[?25h")
    def move_cursor(self, x, y):
        """커서를 특정 좌표(x, y)로 이동"""
        sys.stdout.write(f"\033[{y};{x}H")
    def clear_screen(self):
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def move_cursor_home(self):
        sys.stdout.write("\033[H")

    def draw_lobby(self, room_list):
        """로비 화면 그리기"""
        self.move_cursor_home()
        lines = []
        lines.append(f"┌{'─'*40}┐")
        lines.append(f"│ {COLOR_YELLOW}TETRIS BATTLE ONLINE{COLOR_RESET}".ljust(49) + "│")
        lines.append(f"├{'─'*40}┤")
        lines.append(f"│ Available Rooms:".ljust(41) + "│")
        
        for room in room_list: # room: {'id':1, 'title':'Test'}
            info = f" [{room['id']}] {room['title']}"
            lines.append(f"│{info}".ljust(41) + "│")
            
        for _ in range(10 - len(room_list)):
             lines.append(f"│".ljust(41) + "│")
             
        lines.append(f"├{'─'*40}┤")
        lines.append(f"│ [C]reate Room    [J]oin Room    [Q]uit │")
        lines.append(f"└{'─'*40}┘")
        
        sys.stdout.write("\n".join(lines))
        sys.stdout.flush()

    def draw_room_wait(self, room_id, slots, ready_states, my_slot):
        """방 대기실 화면 그리기"""
        self.move_cursor_home()
        lines = []
        
        lines.append(f"┌{'─'*40}┐")
        lines.append(f"│      ROOM #{room_id} - WAITING...       │")
        lines.append(f"├{'─'*40}┤")
        lines.append(f"│                                        │")
        
        # 슬롯(플레이어) 정보 표시
        for i in range(MAX_ROOM_SLOTS): # 2인용
            status = "EMPTY"
            color = COLOR_GRAY
            name = "..."
            
            if i < len(slots) and slots[i]:
                name = slots[i] # 닉네임
                if i == 0: # 방장(Slot 0)
                    status = "HOST"
                    color = COLOR_CYAN
                elif i < len(ready_states) and ready_states[i]:
                    status = "READY!"
                    color = COLOR_GREEN
                else:
                    status = "WAITING"
                    color = COLOR_YELLOW
                
                if i == my_slot:
                    name += " (ME)"
            
            # 한 줄 출력: [Slot 1] Hero (ME)      READY!
            info = f" [Slot {i+1}] {name}".ljust(25) + f"{color}{status}{COLOR_RESET}"
            # 색상 코드가 들어가면 길이 계산이 꼬이므로 포맷팅 주의
            display_line = f"│ {info}".ljust(50) + "│" # 넉넉하게 공백 처리
            lines.append(display_line)

        lines.append(f"│                                        │")
        lines.append(f"├{'─'*40}┤")
        if my_slot == 0:
            action_msg = "[Space] Start Game  "
        else:
            action_msg = "[Space] Toggle Ready"
        lines.append(f"│ {action_msg}  [Q] Leave Room │")
        lines.append(f"└{'─'*40}┘")
        
        sys.stdout.write("\n".join(lines))
        sys.stdout.flush()

    def draw_battle(self, local_slot_id, games):
        self.move_cursor_home()
        output = []

        sorted_slots = sorted(games.keys())
        board_strings_map = {} 
        
        PLAYER_GAP = " " * 2

        for slot in sorted_slots:
            game_state = games[slot]
            is_mine = (slot == local_slot_id)
            board_strings_map[slot] = self._generate_board_strings(game_state, is_mine, slot)

        # 1. 헤더 생성 (상단 테두리)
        header_line = ""
        for slot in sorted_slots:
            header_line += f"┌{'─'*20}┐" + PLAYER_GAP
        output.append(header_line)

        # 2. 타이틀 생성 (이름 + 점수)
        title_line = ""
        for slot in sorted_slots:
            game_state = games[slot]
            score = game_state.score if game_state else 0
            
            if slot == local_slot_id:
                display_name = f"MY ({score})"
                colored_name = f"{COLOR_GREEN}{display_name}{COLOR_RESET}"
            else:
                display_name = f"P{slot+1} ({score})"
                colored_name = f"{COLOR_RED}{display_name}{COLOR_RESET}"
            
            padding = " " * (20 - len(display_name) - 1) 
            
            # "│ " + 이름 + 공백 + "│"
            title_block = f"│ {colored_name}{padding}│"
            
            title_line += title_block + PLAYER_GAP
            
        output.append(title_line)

        # 3. 본문 라인 합치기
        if sorted_slots:
            total_lines = len(board_strings_map[sorted_slots[0]])
            for i in range(total_lines):
                full_line = ""
                for slot in sorted_slots:
                    line = board_strings_map[slot][i]
                    full_line += line + PLAYER_GAP
                output.append(full_line)

        sys.stdout.write("\n".join(output))
        sys.stdout.flush()

    def _generate_board_strings(self, game_state, is_mine, slot=None):
        if not game_state:
            # 빈 화면 (접속 안 함)
            return [f"│{' '*20}│"] * 20 + [f"└{'─'*20}┘"]

        display = [row[:] for row in game_state.board.grid]
        piece = game_state.current_piece
        if piece:
            for x, y in piece.get_blocks():
                if 0 <= y < self.height and 0 <= x < self.width:
                    display[y][x] = 2

        lines = []
        # 보드 높이(20)만큼 반복
        for y in range(self.height):
            line = "│" # 왼쪽 여백 1칸
            for x in range(self.width):
                c = display[y][x]
                if c == 0: line += "  " # 공백
                elif c == 1: line += f"{COLOR_CYAN}[]{COLOR_RESET}" if is_mine else f"{COLOR_GRAY}[]{COLOR_RESET}"
                elif c == 2: line += f"{COLOR_YELLOW}[]{COLOR_RESET}" if is_mine else f"{COLOR_WHITE}[]{COLOR_RESET}"
                elif c == 8: line += "XX"
            line += "│" # 오른쪽 여백 1칸 (오른쪽 벽 위치 조정됨)
            
            lines.append(line)
            
        # 하단 테두리
        lines.append(f"└{'─'*20}┘")
        return lines

    def draw_message(self, msg):
        """화면 중앙에 메시지 띄우기 (Ready, Game Over 등)"""
        sys.stdout.write(f"\033[10;20H{COLOR_MAGENTA} {msg} {COLOR_RESET}")
        sys.stdout.flush()

    def clear_line(self, y):
        """해당 줄(y)을 공백으로 지움"""
        self.move_cursor(1, y)
        sys.stdout.write(" " * 80) # 80칸 공백으로 덮어쓰기
        sys.stdout.flush()
        self.move_cursor(1, y) # 커서 원위치