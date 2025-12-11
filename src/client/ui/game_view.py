# src/client/ui/game_view.py
from src.common.constants import *

class BoardRenderer:
    def __init__(self):
        self.BLOCK_CHAR = "[]"
        self.EMPTY_CHAR = "  "
        self.BORDER_V = "│"
        self.BORDER_H = "─"
        self.CORNER_TL = "┌"
        self.CORNER_TR = "┐"
        self.CORNER_BL = "└"
        self.CORNER_BR = "┘"
        
        self.WIDTH = 10
        self.HEIGHT = 20

    def generate_lines(self, game_state, is_mine, slot):
        """헤더와 게임판을 조합하여 반환"""
        lines = []
        
        # 1. 헤더 (이름/점수)
        lines.extend(self.render_header(game_state, is_mine, slot))
        
        # 2. 게임판 (상단 테두리 + 내용 + 하단 테두리)
        lines.extend(self.render_grid(game_state, is_mine))
        
        return lines

    def render_header(self, game_state, is_mine, slot):
        """상단 점수/이름 표시부 생성"""
        score = game_state.score if game_state else 0
        name = "MY" if is_mine else f"P{slot+1}"
        color = COLOR_GREEN if is_mine else COLOR_RED
        
        # 이름과 점수 포맷팅
        title = f"{name}({score})"
        # 테두리 포함 전체 너비 = 10*2 (블록) + 2 (테두리) = 22
        # 가운데 정렬
        return [f"{color}{title.center(22)}{COLOR_RESET}"]

    def render_grid(self, game_state, is_mine):
        """실제 테트리스 보드 부분 생성"""
        lines = []
        
        # 상단 테두리
        lines.append(f"{self.CORNER_TL}{self.BORDER_H * 20}{self.CORNER_TR}")
        
        if not game_state:
            # 게임 상태가 없으면 빈 화면 출력
            for _ in range(self.HEIGHT): 
                lines.append(f"{self.BORDER_V}{'  '*10}{self.BORDER_V}")
        else:
            # 보드 데이터 복사 및 현재 블록 덮어쓰기
            display = [row[:] for row in game_state.board.grid]
            piece = game_state.current_piece
            if piece:
                for x, y in piece.get_blocks():
                    if 0 <= y < self.HEIGHT and 0 <= x < self.WIDTH:
                        display[y][x] = 2 # 2는 현재 조작 중인 블록

            # 그리드 렌더링
            for y in range(self.HEIGHT):
                line = self.BORDER_V
                for x in range(self.WIDTH):
                    val = display[y][x]
                    if val == 0:
                        line += self.EMPTY_CHAR
                    elif val == 1:
                        # 맵에 놓인 블럭: 파란색
                        line += f"{COLOR_BLUE}{self.BLOCK_CHAR}{COLOR_RESET}"
                    elif val == 2:
                        # 현재 조작 블럭: 노란색(나) / 흰색(적)
                        c = COLOR_YELLOW if is_mine else COLOR_WHITE
                        line += f"{c}{self.BLOCK_CHAR}{COLOR_RESET}"
                    elif val == 8:
                        # 방해 줄
                        line += f"{COLOR_WHITE}XX{COLOR_RESET}"
                line += self.BORDER_V
                lines.append(line)
            
        # 하단 테두리
        lines.append(f"{self.CORNER_BL}{self.BORDER_H * 20}{self.CORNER_BR}")
        return lines


class SidebarRenderer:
    def __init__(self):
        self.BLOCK_CHAR = "[]"
        self.BORDER_H = "─"
        self.BORDER_V = "│"
        self.CORNER_TL = "┌"
        self.CORNER_TR = "┐"
        self.CORNER_BL = "└"
        self.CORNER_BR = "┘"
        
        self.WIDTH = 12
        self.INNER_WIDTH = self.WIDTH - 2

    def generate_lines(self, game_state):
        """사이드바 요소(Next, Attack) 조합"""
        lines = []
        
        # 상단 공백 (헤더 높이 맞춤)
        lines.append(" " * self.WIDTH)
        
        # 1. Next 블록 상자
        lines.extend(self.render_next_block(game_state))
        
        # 공백
        lines.append(" " * self.WIDTH)
        
        # 2. Attack 게이지 상자
        lines.extend(self.render_attack_gauge(game_state))
        
        # 남은 공간 공백 채우기 (전체 높이 23줄 맞춤)
        while len(lines) < 23:
            lines.append(" " * self.WIDTH)
            
        return lines

    def render_next_block(self, game_state):
        """다음 블록 미리보기 생성 (텍스트 제거됨)"""
        lines = []
        # 상단 테두리
        lines.append(f"{self.CORNER_TL}{self.BORDER_H * self.INNER_WIDTH}{self.CORNER_TR}")
        
        # 미리보기 데이터 준비 (4x4)
        next_piece = game_state.next_piece
        preview = [['  '] * 4 for _ in range(4)]
        if next_piece:
            # 초기 회전 상태(0)의 모양 가져오기
            shape = next_piece.SHAPES[next_piece.type][0]
            for x, y in shape:
                if 0 <= y < 4 and 0 <= x < 4:
                    # 다음 블록: 보라색 (구분감)
                    preview[y][x] = f"{COLOR_MAGENTA}{self.BLOCK_CHAR}{COLOR_RESET}"
        
        # 4줄 출력
        for row in preview:
            row_str = "".join(row)
            # preview는 8글자, inner_width는 10글자 -> 좌우 1칸 공백 패딩
            lines.append(f"{self.BORDER_V} {row_str} {self.BORDER_V}")
            
        # 하단 테두리
        lines.append(f"{self.CORNER_BL}{self.BORDER_H * self.INNER_WIDTH}{self.CORNER_BR}")
        return lines

    def render_attack_gauge(self, game_state):
        """공격(Garbage) 게이지 생성 (텍스트 제거됨)"""
        lines = []
        # 상단 테두리
        lines.append(f"{self.CORNER_TL}{self.BORDER_H * self.INNER_WIDTH}{self.CORNER_TR}")
        
        pending = getattr(game_state, 'pending_garbage', 0)
        gauge_h = 10
        
        # 게이지 바 채우기 (아래에서 위로)
        for i in range(gauge_h):
            level = gauge_h - 1 - i
            if level < pending:
                fill = f"{COLOR_RED}{self.BLOCK_CHAR * 3}{COLOR_RESET}"
            else:
                fill = " " * 6
            # 게이지 바 폭 6칸, 좌우 여백 2칸씩
            lines.append(f"{self.BORDER_V}  {fill}  {self.BORDER_V}")
            
        # 하단 테두리
        lines.append(f"{self.CORNER_BL}{self.BORDER_H * self.INNER_WIDTH}{self.CORNER_BR}")
        return lines


class GameView:
    def __init__(self):
        self.board_renderer = BoardRenderer()
        self.sidebar_renderer = SidebarRenderer()

    def draw(self, local_slot_id, games):
        """전체 게임 화면(모든 플레이어) 렌더링"""
        output = []
        player_renders = []
        
        sorted_slots = sorted(games.keys())
        
        for slot in sorted_slots:
            game_state = games[slot]
            is_mine = (slot == local_slot_id)
            
            # 1. 보드 렌더링
            board_lines = self.board_renderer.generate_lines(game_state, is_mine, slot)
            
            # 2. 내 화면이면 사이드바 병합
            if is_mine:
                sidebar_lines = self.sidebar_renderer.generate_lines(game_state)
                combined = []
                max_h = max(len(board_lines), len(sidebar_lines))
                
                for i in range(max_h):
                    b_part = board_lines[i] if i < len(board_lines) else " " * 22
                    s_part = sidebar_lines[i] if i < len(sidebar_lines) else " " * 12
                    combined.append(b_part + " " + s_part)
                player_renders.append(combined)
            else:
                player_renders.append(board_lines)

        # 3. 최종 가로 병합 (플레이어 간 간격 추가)
        if not player_renders: return []
        max_height = max(len(r) for r in player_renders)
        
        for y in range(max_height):
            line_str = ""
            for p_render in player_renders:
                if y < len(p_render):
                    line_str += p_render[y] + "    " # 플레이어 사이 간격
                else:
                    line_str += " " * 34 # 빈 공간 채움
            output.append(line_str)
            
        return output

    def create_result_box(self, result_msg, score):
        """결과 오버레이 박스 생성"""
        lines = []
        box_w = 26
        
        color = COLOR_GREEN if result_msg == "WINNER" else COLOR_RED
        if result_msg == "DRAW": color = COLOR_YELLOW
        
        lines.append(f"┌{'─'*box_w}┐")
        lines.append(f"│{' '*box_w}│")
        
        # 결과 메시지
        padding = (box_w - len(result_msg)) // 2
        msg_line = " " * padding + f"{color}{result_msg}{COLOR_RESET}"
        rem = box_w - len(result_msg) - padding
        lines.append(f"│{msg_line + ' '*rem}│")
        
        lines.append(f"│{' '*box_w}│")
        
        # 점수
        s_msg = f"SCORE: {score}"
        s_pad = (box_w - len(s_msg)) // 2
        s_rem = box_w - len(s_msg) - s_pad
        lines.append(f"│{' '*s_pad}{COLOR_YELLOW}{s_msg}{COLOR_RESET}{' '*s_rem}│")

        lines.append(f"│{' '*box_w}│")
        
        # 안내 문구
        info = "Press [Q] to Return"
        i_pad = (box_w - len(info)) // 2
        i_rem = box_w - len(info) - i_pad
        lines.append(f"│{' '*i_pad}{info}{' '*i_rem}│")

        lines.append(f"└{'─'*box_w}┘")
        
        return lines