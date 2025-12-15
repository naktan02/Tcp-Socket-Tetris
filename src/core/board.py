# src/core/board.py

class Board:
    WIDTH = 10
    HEIGHT = 20

    def __init__(self):
        # 0: 빈 칸, 1: 고정된 블록, 8: 방해 줄(Garbage)
        self.grid = [[0] * self.WIDTH for _ in range(self.HEIGHT)]

    def is_valid_position(self, tetromino, adj_x=0, adj_y=0):
        """해당 블록이 보드 내부에 있고, 다른 블록과 겹치지 않는지 확인"""
        for lx, ly in tetromino.SHAPES[tetromino.type][tetromino.rotation % tetromino.max_rotation]:
            target_x = tetromino.x + lx + adj_x
            target_y = tetromino.y + ly + adj_y

            # 1. 벽 밖으로 나갔는지 확인
            if not (0 <= target_x < self.WIDTH and 0 <= target_y < self.HEIGHT):
                return False
            
            # 2. 이미 채워진 칸인지 확인 (충돌)
            if self.grid[target_y][target_x] != 0:
                return False
        return True

    def place_tetromino(self, tetromino):
        """블록을 보드에 고정"""
        for x, y in tetromino.get_blocks():
            if 0 <= y < self.HEIGHT and 0 <= x < self.WIDTH:
                self.grid[y][x] = tetromino.color_id

    def clear_lines(self):
        """꽉 찬 줄을 지우고, 지운 줄 수를 반환"""
        new_grid = [row for row in self.grid if any(cell == 0 for cell in row)]
        lines_cleared = self.HEIGHT - len(new_grid)
        
        # 지운 만큼 위쪽에 빈 줄 추가
        for _ in range(lines_cleared):
            new_grid.insert(0, [0] * self.WIDTH)
            
        self.grid = new_grid
        return lines_cleared
    
    def add_garbage_lines(self, count):
        """방해 줄(Garbage) 추가 (아래에서 솟아오름)"""
        # 위쪽 줄 삭제 (게임 오버 유발 가능)
        if count >= self.HEIGHT:
            count = self.HEIGHT
        self.grid = self.grid[count:]
        
        # 아래쪽에 회색 줄(8) 추가 (한 칸은 비워둠)
        import random
        for _ in range(count):
            row = [8] * self.WIDTH
            row[random.randint(0, self.WIDTH-1)] = 0 # 구멍 하나 뚫기
            self.grid.append(row)

    def drill_path(self, tetromino):
        """[추가] 블록 아래의 모든 장애물 제거 (무게추 효과)"""
        for x, y in tetromino.get_blocks():
            # 현재 블록 위치보다 아래(y+1)부터 바닥까지 0으로 만듦
            for dy in range(y + 1, self.HEIGHT):
                if 0 <= x < self.WIDTH:
                    self.grid[dy][x] = 0
    
    def is_in_bounds(self, tetromino, adj_x=0, adj_y=0):
        """블록이 보드 경계(벽, 바닥) 안에 있는지 확인"""
        for lx, ly in tetromino.SHAPES[tetromino.type][tetromino.rotation % tetromino.max_rotation]:
            target_x = tetromino.x + lx + adj_x
            target_y = tetromino.y + ly + adj_y
            
            # 보드 밖으로 나가면 False
            if not (0 <= target_x < self.WIDTH and 0 <= target_y < self.HEIGHT):
                return False
        return True

    def drill_position(self, tetromino, adj_x=0, adj_y=0):
        """블록이 위치할 좌표의 기존 블록들을 제거"""
        for lx, ly in tetromino.SHAPES[tetromino.type][tetromino.rotation % tetromino.max_rotation]:
            target_x = tetromino.x + lx + adj_x
            target_y = tetromino.y + ly + adj_y
            
            # 범위 안이라면 해당 칸을 0(빈 공간)으로 만듦
            if 0 <= target_x < self.WIDTH and 0 <= target_y < self.HEIGHT:
                self.grid[target_y][target_x] = 0