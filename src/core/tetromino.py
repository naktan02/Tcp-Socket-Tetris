# src/core/tetromino.py
import random
from src.common.constants import Action

class Tetromino:
    """
    테트리스 블록(미노) 객체
    형태(Shape), 색상, 현재 좌표(x, y)를 관리함
    """
    # 블록 모양 정의 (4x4 or 3x3 box within local coordinates)
    SHAPES = {
        'I': [
            [(0, 1), (1, 1), (2, 1), (3, 1)], # 0 deg
            [(2, 0), (2, 1), (2, 2), (2, 3)], # 90 deg
            [(0, 2), (1, 2), (2, 2), (3, 2)], # 180 deg
            [(1, 0), (1, 1), (1, 2), (1, 3)]  # 270 deg
        ],
        'O': [
            [(1, 0), (2, 0), (1, 1), (2, 1)] # O는 회전해도 똑같음
        ],
        'T': [
            [(1, 0), (0, 1), (1, 1), (2, 1)],
            [(1, 0), (1, 1), (2, 1), (1, 2)],
            [(0, 1), (1, 1), (2, 1), (1, 2)],
            [(1, 0), (0, 1), (1, 1), (1, 2)]
        ],
        'S': [
            [(1, 0), (2, 0), (0, 1), (1, 1)],
            [(1, 0), (1, 1), (2, 1), (2, 2)],
            [(1, 1), (2, 1), (0, 2), (1, 2)],
            [(0, 0), (0, 1), (1, 1), (1, 2)]
        ],
        'Z': [
            [(0, 0), (1, 0), (1, 1), (2, 1)],
            [(2, 0), (1, 1), (2, 1), (1, 2)],
            [(0, 1), (1, 1), (1, 2), (2, 2)],
            [(1, 0), (0, 1), (1, 1), (0, 2)]
        ],
        'J': [
            [(0, 0), (0, 1), (1, 1), (2, 1)],
            [(1, 0), (2, 0), (1, 1), (1, 2)],
            [(0, 1), (1, 1), (2, 1), (2, 2)],
            [(1, 0), (1, 1), (0, 2), (1, 2)]
        ],
        'L': [
            [(2, 0), (0, 1), (1, 1), (2, 1)],
            [(1, 0), (1, 1), (1, 2), (2, 2)],
            [(0, 1), (1, 1), (2, 1), (0, 2)],
            [(0, 0), (1, 0), (1, 1), (1, 2)]
        ],
        'WEIGHT': [
            [(1, 2), (2, 2), (0, 3), (1, 3), (2, 3), (3, 3)] 
        ]
    }
    
    TYPES = ['I', 'O', 'T', 'S', 'Z', 'J', 'L']

    def __init__(self, shape_type):
        self.type = shape_type
        self.rotation = 0 # 0 ~ 3
        self.x = 3        # 초기 시작 위치 (가로 중앙)
        self.y = 0        # 초기 시작 위치 (맨 위)
        
        # O형은 회전이 없음
        self.max_rotation = len(self.SHAPES[shape_type])
        if shape_type in self.TYPES:
            self.color_id = self.TYPES.index(shape_type) + 1
        else:
            self.color_id = 8 
        self.is_heavy = False

    @classmethod
    def create_random(cls):
        """무작위 블록 생성"""
        return cls(random.choice(cls.TYPES))

    def get_blocks(self):
        """현재 회전 상태에 따른 블록들의 절대 좌표(board 상의 x, y) 반환"""
        local_coords = self.SHAPES[self.type][self.rotation % self.max_rotation]
        return [(self.x + lx, self.y + ly) for lx, ly in local_coords]

    def rotate(self):
        self.rotation = (self.rotation + 1) % self.max_rotation

    def rotate_counter(self):
        self.rotation = (self.rotation - 1) % self.max_rotation

    def clone(self):
        """현재 블록의 상태를 복제한 새 객체 반환"""
        new_piece = Tetromino(self.type)
        new_piece.rotation = self.rotation
        new_piece.x = self.x
        new_piece.y = self.y
        new_piece.color_id = self.color_id
        new_piece.is_heavy = self.is_heavy
        return new_piece

    def make_heavy(self):
        """블록을 무게추 모드로 변경 (모양 변경 포함)"""
        self.is_heavy = True
        self.type = 'WEIGHT'     # [수정] 모양을 무게추 모양으로 변경
        self.rotation = 0        # 회전 초기화 (무게추는 회전 안 함)
        self.max_rotation = 1    # 회전 불가 설정
        self.color_id = 8        # 색상: 흰색/회색
        if self.x > 6: 
            self.x = 6