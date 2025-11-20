import time
import msvcrt
from typing import Optional

from common.messages import make_game_input, make_leave_game
from client.renderer import draw_game

# --- 키 매핑 설정 ---
KEY_MAP = {
    'w': 'rotate', 'i': 'rotate',
    'a': 'left',   'j': 'left',
    's': 'down',   'k': 'down',
    'd': 'right',  'l': 'right',
    ' ': 'drop',
}

class GameUI:
    # [수정 1] my_player_id 인자 추가
    def __init__(self, conn, game_id: int, my_player_id: int, role: str, opponent_name: str):
        self.conn = conn
        self.game_id = game_id
        self.my_player_id = my_player_id  # 내 ID 저장
        self.my_role = role
        self.opponent_name = opponent_name
        
        self.my_board = [['.'] * 10 for _ in range(20)]
        self.op_board = [['.'] * 10 for _ in range(20)]
        self.scores = {'p1': 0, 'p2': 0}
        self.game_over_msg: Optional[str] = None
        self.dirty = True

    def handle_game_state(self, payload: list[str]):
        try:
            self.scores['p1'] = int(payload[0])
            self.scores['p2'] = int(payload[2])
            # p1, p2 보드 파싱
            p1_board = self._parse_board(payload[1])
            p2_board = self._parse_board(payload[3])
            
            if self.my_role == 'P1':
                self.my_board = p1_board
                self.op_board = p2_board
            else:
                self.my_board = p2_board
                self.op_board = p1_board
                
            self.dirty = True
        except (IndexError, ValueError):
            pass

    def handle_game_over(self, payload: list[str]):
        result = payload[0] if payload else "Unknown"
        if result == "WIN":
            msg = "승리했습니다! 축하합니다!"
        elif result == "LOSE":
            msg = "패배했습니다. 다음 기회에..."
        elif result == "DRAW":
            msg = "무승부입니다."
        else:
            msg = f"게임 종료: {result}"
        self.game_over_msg = msg
        self.dirty = True

    def _parse_board(self, board_str: str) -> list[list[str]]:
        """
        서버에서 온 "0000/0000/..." 형태의 문자열을 2차원 배열로 변환
        """
        # [수정 2] '/' 기준으로 분리하여 정확히 파싱
        rows = board_str.split('/')
        board = []
        for row_str in rows:
            # 혹시 모를 빈 문자열이나 길이 안 맞는 경우 처리
            if not row_str: continue
            row = ['■' if char != '0' else '.' for char in row_str]
            board.append(row)
        
        # 보드 크기가 20줄이 안되면 빈 줄로 채움 (안전장치)
        while len(board) < 20:
            board.insert(0, ['.'] * 10)
            
        return board

    def loop(self):
        # 입력 버퍼 비우기
        while msvcrt.kbhit():
            msvcrt.getch()

        while True:
            if self.dirty:
                draw_game(
                    self.my_role,
                    self.opponent_name,
                    self.scores,
                    self.my_board,
                    self.op_board,
                    self.game_over_msg
                )
                self.dirty = False

            if self.game_over_msg:
                time.sleep(2)
                return

            if msvcrt.kbhit():
                try:
                    ch = msvcrt.getch()
                    key = ch.decode('utf-8').lower()
                    
                    if key == 'q':
                        self.conn.send(make_leave_game())
                        return
                    
                    action = KEY_MAP.get(key)
                    if action:
                        # [수정 3] make_game_input에 필요한 인자(game_id, player_id) 전달
                        packet = make_game_input(self.game_id, self.my_player_id, action)
                        self.conn.send(packet)
                        
                except UnicodeDecodeError:
                    pass

            time.sleep(0.02)