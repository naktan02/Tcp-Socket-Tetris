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
        self.item_count = 0        # 보유 아이템 수 (최대 3)
        self.item_target = 4       # 다음 아이템 획득 목표 (4 -> 8 -> 16)
        self.item_progress = 0
        
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
                lines_cleared = self._move_down()
                
        elif action == Action.ROTATE:
            self.current_piece.rotate()
            if not self.board.is_valid_position(self.current_piece):
                # 회전 불가능하면 원상복구 (벽 차기 생략)
                self.current_piece.rotate_counter()
                
        elif action == Action.DROP:
            #  스페이스바(하드 드롭) 처리
            if self.current_piece.is_heavy:
                # 무게추: 바닥에 닿을 때까지 부수면서 내려감
                while self.board.is_in_bounds(self.current_piece, adj_y=1):
                    self.board.drill_position(self.current_piece, adj_y=1)
                    self.current_piece.y += 1
                lines_cleared = self.lock_piece()
            else:
                # 일반: 그냥 내려감
                while self.board.is_valid_position(self.current_piece, adj_y=1):
                    self.current_piece.y += 1
                lines_cleared = self.lock_piece()
            
        elif action == Action.USE_ITEM: 
            self.use_item()

        return lines_cleared

    def update(self):
        """일정 시간마다 호출되는 게임 루프 (중력 작용)"""
        return self._move_down()

    def _move_down(self):
        """한 칸 아래로 이동 시도 (무게추 로직 포함)"""
        lines_cleared = 0
        
        if self.current_piece.is_heavy:
            # [무게추] 바닥 범위 안이라면 무조건 내려감 (블록 파괴)
            if self.board.is_in_bounds(self.current_piece, adj_y=1):
                self.board.drill_position(self.current_piece, adj_y=1) # 아래칸 부수기
                self.current_piece.y += 1
            else:
                # 바닥에 닿음 -> 고정
                lines_cleared = self.lock_piece()
        else:
            # [일반] 빈 공간이어야 내려감
            if self.board.is_valid_position(self.current_piece, adj_y=1):
                self.current_piece.y += 1
            else:
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
        if not self.current_piece: return None
        ghost = self.current_piece.clone()
        
        # 고스트 표시: 무게추 상태면 바닥까지 뚫는 위치 보여주기
        if ghost.is_heavy:
            while self.board.is_in_bounds(ghost, adj_y=1):
                ghost.y += 1
        else:
            while self.board.is_valid_position(ghost, adj_y=1):
                ghost.y += 1
        return ghost

    def use_item(self):
        """아이템 사용: 현재 블록을 무게추로 변환"""
        # 아이템이 있고, 아직 무게추 상태가 아니면 사용
        if self.item_count > 0 and not self.current_piece.is_heavy:
            self.item_count -= 1
            self.current_piece.make_heavy()
            return True
        return False

    def lock_piece(self):
        self.board.place_tetromino(self.current_piece)
        lines = self.board.clear_lines()
        self.score += lines * 100
        
        # 아이템 획득 로직
        if lines > 0:
            self.item_progress += lines
            # 목표 달성 시
            if self.item_progress >= self.item_target:
                if self.item_count < 3: # 최대 3개
                    self.item_count += 1
                    self.item_progress = 0 # 0으로 초기화 (요청사항)
                    self.item_target *= 2  # 목표 2배 증가 (4->8->16)
                else:
                    # 아이템 꽉 차면 게이지 유지하거나 초기화 (여기선 유지)
                    pass

        self.current_piece = self.next_piece
        self.next_piece = Tetromino.create_random()
        
        if not self.board.is_valid_position(self.current_piece):
            self.game_over = True
        
        return lines