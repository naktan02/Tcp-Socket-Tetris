# src/core/game_state.py
from src.common.constants import Action
from .board import Board
from .tetromino import Tetromino

class GameState:
    def __init__(self):
        self.board = Board()
        self.current_piece = Tetromino.create_random()
        self.next_piece = Tetromino.create_random()
        self.score = 0
        self.game_over = False
        
    def process_input(self, action):
        """유저 입력을 처리하고 상태 업데이트"""
        if self.game_over:
            return 0

        lines_cleared = 0

        if action == Action.MOVE_LEFT:
            if self.board.is_valid_position(self.current_piece, adj_x=-1):
                self.current_piece.x -= 1
                
        elif action == Action.MOVE_RIGHT:
            if self.board.is_valid_position(self.current_piece, adj_x=1):
                self.current_piece.x += 1
                
        elif action == Action.DOWN:
            if self.board.is_valid_position(self.current_piece, adj_y=1):
                self.current_piece.y += 1
                
        elif action == Action.ROTATE:
            self.current_piece.rotate()
            if not self.board.is_valid_position(self.current_piece):
                # 회전 불가능하면 원상복구 (벽 차기 생략)
                self.current_piece.rotate_counter()
                
        elif action == Action.DROP:
            # 바닥에 닿을 때까지 내림
            while self.board.is_valid_position(self.current_piece, adj_y=1):
                self.current_piece.y += 1
            lines_cleared = self.lock_piece()

        return lines_cleared

    def update(self):
        """일정 시간마다 호출되는 게임 루프 (중력 작용)"""
        if self.game_over:
            return 0

        lines_cleared = 0

        # 한 칸 아래로 이동 시도
        if self.board.is_valid_position(self.current_piece, adj_y=1):
            self.current_piece.y += 1
        else:
            # 더 이상 못 내려가면 고정
            lines_cleared = self.lock_piece()
        
        return lines_cleared

    def lock_piece(self):
        """블록을 보드에 고정하고 새 블록 생성"""
        self.board.place_tetromino(self.current_piece)
        lines = self.board.clear_lines()
        self.score += lines * 100
        
        # 새 블록 가져오기
        self.current_piece = self.next_piece
        self.next_piece = Tetromino.create_random()
        
        # 새 블록을 놓을 자리가 없으면 게임 오버
        if not self.board.is_valid_position(self.current_piece):
            self.game_over = True
        
        return lines
        
    def get_ghost_piece(self):
        """현재 블록이 바닥에 떨어질 위치(Ghost)를 계산하여 반환"""
        if not self.current_piece:
            return None
            
        ghost = self.current_piece.clone()
        
        # 바닥에 닿을 때까지 y를 증가시킴 (Hard Drop 시뮬레이션)
        while self.board.is_valid_position(ghost, adj_y=1):
            ghost.y += 1
            
        return ghost